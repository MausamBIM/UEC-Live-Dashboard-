"""
Database module for the dashboard application.
Handles SQLite database operations with a normalized customer/report data model.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

import pandas as pd

from etl import build_normalized_datasets

logger = logging.getLogger(__name__)

DATABASE_PATH = Path(__file__).parent / "dashboard.db"

REQUIRED_TABLE_COLUMNS = {
    "branches": {
        "id", "name", "location", "created_at"
    },
    "customers": {
        "id", "company_name", "address", "contact_name", "primary_mobile",
        "secondary_mobile", "email", "pan_no", "vat_no", "created_at"
    },
    "calling_reports": {
        "id", "date", "customer_id", "branch_id", "calling_person",
        "work_status", "remarks", "remarks_status", "next_calling_date",
        "service_lead", "created_at"
    },
    "marketing_reports": {
        "id", "date", "customer_id", "branch_id", "marketing_person",
        "segment", "outcome", "remarks", "final_remarks", "created_at"
    },
    "payment_followups": {
        "id", "date", "customer_id", "branch_id", "os_amount",
        "payment_received", "next_calling_date", "status", "remarks", "created_at"
    }
}


class DatabaseManager:
    """Manages all database operations with context manager support."""

    def __init__(self, db_path: str = str(DATABASE_PATH)):
        self.db_path = Path(db_path)
        self.init_database()

    def __enter__(self):
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON;")
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'connection'):
            self.connection.close()

    def _create_tables(self, conn: sqlite3.Connection) -> None:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS branches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT,
                address TEXT,
                contact_name TEXT,
                primary_mobile TEXT,
                secondary_mobile TEXT,
                email TEXT,
                pan_no TEXT,
                vat_no TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calling_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE,
                customer_id INTEGER NOT NULL,
                branch_id INTEGER NOT NULL,
                calling_person TEXT,
                work_status TEXT CHECK(work_status IN ('connected', 'not_connected', 'service_confirm')),
                remarks TEXT,
                remarks_status TEXT,
                next_calling_date DATE,
                service_lead TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (branch_id) REFERENCES branches(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS marketing_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE,
                customer_id INTEGER NOT NULL,
                branch_id INTEGER NOT NULL,
                marketing_person TEXT,
                segment TEXT,
                outcome TEXT CHECK(outcome IN ('visit', 'service_confirm', 'followup')),
                remarks TEXT,
                final_remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (branch_id) REFERENCES branches(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_followups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE,
                customer_id INTEGER NOT NULL,
                branch_id INTEGER NOT NULL,
                os_amount REAL DEFAULT 0,
                payment_received REAL DEFAULT 0,
                next_calling_date DATE,
                status TEXT CHECK(status IN ('paid', 'pending', 'followup')),
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (branch_id) REFERENCES branches(id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_calling_date 
            ON calling_reports(date)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_marketing_date 
            ON marketing_reports(date)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_payment_date 
            ON payment_followups(date)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_branch_id 
            ON branches(id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_customer_id_calling
            ON calling_reports(customer_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_customer_id_marketing
            ON marketing_reports(customer_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_customer_id_payment
            ON payment_followups(customer_id)
        """)
        conn.commit()

    def _get_table_columns(self, conn: sqlite3.Connection, table: str) -> set:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        return {row[1] for row in cursor.fetchall()}

    def _is_schema_compatible(self, conn: sqlite3.Connection) -> bool:
        for table, required_columns in REQUIRED_TABLE_COLUMNS.items():
            try:
                existing = self._get_table_columns(conn, table)
            except sqlite3.DatabaseError:
                return False
            if not required_columns.issubset(existing):
                logger.warning("Table %s is missing expected columns: %s", table, required_columns - existing)
                return False
        return True

    def _backup_mismatched_database(self) -> None:
        backup_path = self.db_path.with_name(f"{self.db_path.stem}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}{self.db_path.suffix}")
        if self.db_path.exists():
            self.db_path.replace(backup_path)
            logger.warning("Incompatible database backed up to %s", backup_path)

    def init_database(self):
        """Initialize database with required tables and relationships."""
        try:
            rebuilt = False
            with self as conn:
                self._create_tables(conn)
                if not self._is_schema_compatible(conn):
                    logger.warning("Detected incompatible database schema. Rebuilding database from source CSV.")
                    conn.close()
                    self._backup_mismatched_database()
                    if self.db_path.exists():
                        self.db_path.unlink()
                    with self as conn2:
                        self._create_tables(conn2)
                    rebuilt = True

            if rebuilt or self._should_refresh_from_csv() or self._database_is_empty():
                self.insert_sample_data(replace=True)
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise

    def _should_refresh_from_csv(self) -> bool:
        csv_path = Path(__file__).parent / "data.csv"
        db_path = Path(self.db_path)
        if not csv_path.exists():
            return False
        if not db_path.exists():
            return True
        return csv_path.stat().st_mtime > db_path.stat().st_mtime

    def _truncate_tables(self, conn: sqlite3.Connection) -> None:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM calling_reports")
        cursor.execute("DELETE FROM marketing_reports")
        cursor.execute("DELETE FROM payment_followups")
        cursor.execute("DELETE FROM customers")
        cursor.execute("DELETE FROM branches")
        conn.commit()

    def _database_is_empty(self) -> bool:
        with self as conn:
            cursor = conn.cursor()
            for table in ["branches", "customers", "calling_reports", "marketing_reports", "payment_followups"]:
                cursor.execute(f"SELECT COUNT(1) FROM {table}")
                count = cursor.fetchone()[0]
                if count == 0:
                    return True
        return False

    def insert_sample_data(self, replace: bool = False):
        """Insert cleaned sample data from CSV into normalized tables."""
        try:
            csv_path = Path(__file__).parent / "data.csv"
            if not csv_path.exists():
                logger.warning("data.csv not found")
                return

            customers, calling, marketing, payments = build_normalized_datasets(csv_path)

            with self as conn:
                if replace:
                    self._truncate_tables(conn)

                cursor = conn.cursor()

                for branch_name in sorted({*calling["branch"].dropna().unique(), *marketing["branch"].dropna().unique(), *payments["branch"].dropna().unique()}):
                    if not branch_name:
                        continue
                    cursor.execute(
                        "INSERT OR IGNORE INTO branches (name) VALUES (?)",
                        (branch_name,)
                    )

                cursor.execute("SELECT id, name FROM branches")
                branch_map = {row[1]: row[0] for row in cursor.fetchall()}

                for _, row in customers.iterrows():
                    cursor.execute(
                        "INSERT INTO customers (id, company_name, address, contact_name, primary_mobile, secondary_mobile, email, pan_no, vat_no) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            int(row.get("id", 0)),
                            row.get("company_name", ""),
                            row.get("address", ""),
                            row.get("contact_name", ""),
                            row.get("primary_mobile", ""),
                            row.get("secondary_mobile", ""),
                            row.get("email", ""),
                            row.get("pan_no", ""),
                            row.get("vat_no", "")
                        )
                    )

                cursor.execute("SELECT id, contact_name, primary_mobile FROM customers")
                customer_rows = cursor.fetchall()
                customer_map = {
                    (row[1] or "", row[2] or ""): row[0]
                    for row in customer_rows
                }
                valid_customer_ids = {row[0] for row in customer_rows}

                def lookup_customer_id(row):
                    if pd.notna(row.get("customer_id")) and row.get("customer_id") != "":
                        try:
                            cid = int(row.get("customer_id"))
                            if cid in valid_customer_ids:
                                return cid
                        except (ValueError, TypeError):
                            pass

                    key = (
                        str(row.get("contact_name", "")).strip(),
                        str(row.get("primary_mobile", "")).strip()
                    )
                    return customer_map.get(key)

                def insert_report(query: str, values: tuple):
                    cursor.execute(query, values)

                for _, row in calling.iterrows():
                    branch_id = branch_map.get(row.get("branch", ""), None)
                    customer_id = lookup_customer_id(row)
                    if branch_id is None or customer_id is None:
                        continue
                    cursor.execute(
                        "INSERT INTO calling_reports (date, customer_id, branch_id, calling_person, work_status, remarks, remarks_status, next_calling_date, service_lead) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            row.get("date"),
                            customer_id,
                            branch_id,
                            row.get("calling_person", ""),
                            row.get("work_status", "not_connected"),
                            row.get("remarks", ""),
                            row.get("remarks_status", ""),
                            row.get("next_calling_date", ""),
                            row.get("service_lead", "")
                        )
                    )

                for _, row in marketing.iterrows():
                    branch_id = branch_map.get(row.get("branch", ""), None)
                    customer_id = lookup_customer_id(row)
                    if branch_id is None or customer_id is None:
                        continue
                    cursor.execute(
                        "INSERT INTO marketing_reports (date, customer_id, branch_id, marketing_person, segment, outcome, remarks, final_remarks) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            row.get("date"),
                            customer_id,
                            branch_id,
                            row.get("marketing_person", ""),
                            row.get("segment", ""),
                            row.get("outcome", "followup"),
                            row.get("remarks", ""),
                            row.get("final_remarks", "")
                        )
                    )

                for _, row in payments.iterrows():
                    branch_id = branch_map.get(row.get("branch", ""), None)
                    customer_id = lookup_customer_id(row)
                    if branch_id is None or customer_id is None:
                        continue
                    cursor.execute(
                        "INSERT INTO payment_followups (date, customer_id, branch_id, os_amount, payment_received, next_calling_date, status, remarks) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            row.get("date"),
                            customer_id,
                            branch_id,
                            row.get("os_amount", 0.0),
                            row.get("payment_received", 0.0),
                            row.get("next_calling_date", ""),
                            row.get("status", "followup"),
                            row.get("remarks", "")
                        )
                    )

                conn.commit()
                logger.info("Sample data inserted successfully")

        except Exception as e:
            logger.error(f"Error inserting sample data: {e}")
            raise

    def _execute_report_query(self, query: str, params: list = None) -> pd.DataFrame:
        try:
            with self as conn:
                return pd.read_sql_query(query, conn, params=params or [])
        except sqlite3.OperationalError as e:
            if "no such column" in str(e).lower() or "no such table" in str(e).lower():
                logger.warning("Schema error during query execution: %s. Reinitializing database.", e)
                self.init_database()
                with self as conn:
                    return pd.read_sql_query(query, conn, params=params or [])
            raise

    def get_calling_reports(self, branch_id: Optional[int] = None) -> pd.DataFrame:
        """Fetch calling reports with normalized columns."""
        query = """
            SELECT
                cr.id,
                cr.date,
                c.company_name as customer_name,
                c.contact_name as contact_name,
                c.address as address,
                c.primary_mobile as contact_number,
                b.name as branch,
                cr.calling_person,
                cr.work_status,
                cr.remarks,
                cr.remarks_status,
                cr.next_calling_date,
                cr.service_lead,
                cr.customer_id
            FROM calling_reports cr
            JOIN customers c ON cr.customer_id = c.id
            JOIN branches b ON cr.branch_id = b.id
            WHERE 1=1
        """
        params = []
        if branch_id:
            query += " AND cr.branch_id = ?"
            params.append(branch_id)
        query += " ORDER BY cr.date DESC"
        return self._execute_report_query(query, params)

    def get_marketing_reports(self, branch_id: Optional[int] = None) -> pd.DataFrame:
        """Fetch marketing reports with normalized columns."""
        query = """
            SELECT
                mr.id,
                mr.date,
                c.company_name as customer_name,
                c.contact_name as contact_name,
                c.address as address,
                c.primary_mobile as contact_number,
                b.name as branch,
                mr.marketing_person,
                mr.segment,
                mr.outcome,
                mr.remarks,
                mr.final_remarks,
                mr.customer_id
            FROM marketing_reports mr
            JOIN customers c ON mr.customer_id = c.id
            JOIN branches b ON mr.branch_id = b.id
            WHERE 1=1
        """
        params = []
        if branch_id:
            query += " AND mr.branch_id = ?"
            params.append(branch_id)
        query += " ORDER BY mr.date DESC"
        return self._execute_report_query(query, params)

    def get_payment_followups(self, branch_id: Optional[int] = None) -> pd.DataFrame:
        """Fetch payment followups with normalized columns."""
        query = """
            SELECT
                pf.id,
                pf.date,
                c.company_name as customer_name,
                c.contact_name as contact_name,
                c.address as address,
                c.primary_mobile as contact_number,
                b.name as branch,
                pf.os_amount,
                pf.payment_received,
                pf.next_calling_date,
                pf.status,
                pf.remarks,
                pf.customer_id
            FROM payment_followups pf
            JOIN customers c ON pf.customer_id = c.id
            JOIN branches b ON pf.branch_id = b.id
            WHERE 1=1
        """
        params = []
        if branch_id:
            query += " AND pf.branch_id = ?"
            params.append(branch_id)
        query += " ORDER BY pf.date DESC"
        return self._execute_report_query(query, params)

    def get_branches(self) -> List[str]:
        """Get all branches."""
        with self as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM branches ORDER BY name")
            return [row[0] for row in cursor.fetchall()]

    def get_branch_id(self, branch_name: str) -> Optional[int]:
        """Get branch ID by name."""
        with self as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM branches WHERE name = ?", (branch_name,))
            result = cursor.fetchone()
            return result[0] if result else None

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for overall dashboard."""
        with self as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM calling_reports")
            total_calls = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM marketing_reports")
            total_marketing = cursor.fetchone()[0]
            cursor.execute("SELECT SUM(payment_received) FROM payment_followups")
            total_collection = cursor.fetchone()[0] or 0.0
            cursor.execute("SELECT SUM(os_amount) FROM payment_followups")
            total_pending = cursor.fetchone()[0] or 0.0
            return {
                "total_calls": total_calls,
                "total_marketing": total_marketing,
                "total_collection": float(total_collection),
                "total_pending": float(total_pending)
            }


def get_db() -> DatabaseManager:
    """Factory function to get database instance."""
    return DatabaseManager()
