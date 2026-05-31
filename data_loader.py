"""
Data Insertion Module - Load Excel data into database one by one.

This module provides efficient data loading from Excel files into the SQLite database,
replacing the slow Google Sheets loading.

Usage:
    from data_loader import ExcelDataLoader
    
    loader = ExcelDataLoader()
    loader.load_calling_data("calling_data.xlsx")
    loader.load_marketing_data("marketing_data.xlsx")
    loader.load_payment_data("payment_data.xlsx")
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from db import DatabaseManager
from etl import normalize_date, normalize_headers

logger = logging.getLogger(__name__)


class ExcelDataLoader:
    """Load Excel data into database one record at a time."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize loader with database connection."""
        self.db = DatabaseManager(db_path)
        self.stats = {
            "inserted": 0,
            "skipped": 0,
            "errors": 0
        }
    
    def _reset_stats(self):
        """Reset statistics counters."""
        self.stats = {"inserted": 0, "skipped": 0, "errors": 0}
    
    def _get_or_create_branch(self, conn, branch_name: str) -> int:
        """Get or create branch and return its ID."""
        cursor = conn.cursor()
        
        # Get existing branch
        cursor.execute("SELECT id FROM branches WHERE name = ?", (branch_name,))
        row = cursor.fetchone()
        if row:
            return row[0]
        
        # Create new branch
        cursor.execute(
            "INSERT INTO branches (name, location) VALUES (?, ?)",
            (branch_name, "")
        )
        conn.commit()
        return cursor.lastrowid
    
    def _get_or_create_customer(self, conn, customer_data: Dict[str, Any]) -> int:
        """Get or create customer and return its ID."""
        cursor = conn.cursor()
        
        # Try to find by company name
        cursor.execute(
            "SELECT id FROM customers WHERE company_name = ?",
            (customer_data.get("customer_name", ""),)
        )
        row = cursor.fetchone()
        if row:
            return row[0]
        
        # Create new customer
        cursor.execute("""
            INSERT INTO customers 
            (company_name, address, contact_name, primary_mobile, email)
            VALUES (?, ?, ?, ?, ?)
        """, (
            customer_data.get("customer_name", ""),
            customer_data.get("address", ""),
            customer_data.get("contact_name", ""),
            customer_data.get("contact_number", ""),
            customer_data.get("email", "")
        ))
        conn.commit()
        return cursor.lastrowid
    
    def load_calling_data(self, excel_file: str, sheet_name: str = 0) -> Dict[str, int]:
        """
        Load calling data from Excel file into database.
        
        Args:
            excel_file: Path to Excel file
            sheet_name: Sheet name or index (default: 0)
        
        Returns:
            Dictionary with stats: {inserted, skipped, errors}
        """
        self._reset_stats()
        
        try:
            # Read Excel file
            df = pd.read_excel(excel_file, sheet_name=sheet_name, dtype=str)
            df = normalize_headers(df)
            
            logger.info(f"Loading {len(df)} calling records from {excel_file}")
            
            with self.db as conn:
                cursor = conn.cursor()
                
                for idx, row in df.iterrows():
                    try:
                        # Get or create branch
                        branch_name = str(row.get("branch", "Kathmandu")).strip() or "Kathmandu"
                        branch_id = self._get_or_create_branch(conn, branch_name)
                        
                        # Get or create customer
                        customer_data = {
                            "customer_name": str(row.get("customer_name", "")).strip(),
                            "address": str(row.get("address", "")).strip(),
                            "contact_name": str(row.get("contact_name", "")).strip(),
                            "contact_number": str(row.get("contact_number", "")).strip(),
                            "email": str(row.get("email", "")).strip(),
                        }
                        
                        if not customer_data["customer_name"]:
                            logger.warning(f"Row {idx+2}: Missing customer name, skipping")
                            self.stats["skipped"] += 1
                            continue
                        
                        customer_id = self._get_or_create_customer(conn, customer_data)
                        
                        # Insert calling report
                        cursor.execute("""
                            INSERT INTO calling_reports
                            (date, customer_id, branch_id, calling_person, work_status, 
                             remarks_status, remarks, service_lead, next_calling_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            normalize_date(row.get("date", "")),
                            customer_id,
                            branch_id,
                            str(row.get("calling_person", "")).strip(),
                            str(row.get("work_status", "not_connected")).strip().lower(),
                            str(row.get("remarks_status", "")).strip(),
                            str(row.get("remarks", "")).strip(),
                            str(row.get("service_lead", "")).strip(),
                            normalize_date(row.get("next_calling_date", ""))
                        ))
                        
                        self.stats["inserted"] += 1
                        
                        # Commit every 100 records
                        if (self.stats["inserted"] + self.stats["skipped"]) % 100 == 0:
                            conn.commit()
                            logger.info(f"Inserted {self.stats['inserted']} records so far...")
                    
                    except Exception as e:
                        logger.error(f"Row {idx+2}: Error inserting record - {e}")
                        self.stats["errors"] += 1
                        continue
                
                conn.commit()
            
            logger.info(f"Calling data load complete: {self.stats}")
            return self.stats
        
        except Exception as e:
            logger.error(f"Failed to load calling data: {e}")
            raise
    
    def load_marketing_data(self, excel_file: str, sheet_name: str = 0) -> Dict[str, int]:
        """
        Load marketing data from Excel file into database.
        
        Args:
            excel_file: Path to Excel file
            sheet_name: Sheet name or index (default: 0)
        
        Returns:
            Dictionary with stats: {inserted, skipped, errors}
        """
        self._reset_stats()
        
        try:
            # Read Excel file
            df = pd.read_excel(excel_file, sheet_name=sheet_name, dtype=str)
            df = normalize_headers(df)
            
            logger.info(f"Loading {len(df)} marketing records from {excel_file}")
            
            with self.db as conn:
                cursor = conn.cursor()
                
                for idx, row in df.iterrows():
                    try:
                        # Get or create branch
                        branch_name = str(row.get("branch", "Kathmandu")).strip() or "Kathmandu"
                        branch_id = self._get_or_create_branch(conn, branch_name)
                        
                        # Get or create customer
                        customer_data = {
                            "customer_name": str(row.get("customer_name", "")).strip(),
                            "address": str(row.get("address", "")).strip(),
                            "contact_name": str(row.get("contact_name", "")).strip(),
                            "contact_number": str(row.get("contact_number", "")).strip(),
                            "email": str(row.get("email", "")).strip(),
                        }
                        
                        if not customer_data["customer_name"]:
                            logger.warning(f"Row {idx+2}: Missing customer name, skipping")
                            self.stats["skipped"] += 1
                            continue
                        
                        customer_id = self._get_or_create_customer(conn, customer_data)
                        
                        # Insert marketing report
                        cursor.execute("""
                            INSERT INTO marketing_reports
                            (date, customer_id, branch_id, marketing_person, segment, 
                             outcome, remarks, final_remarks)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            normalize_date(row.get("date", "")),
                            customer_id,
                            branch_id,
                            str(row.get("marketing_person", "")).strip(),
                            str(row.get("segment", "")).strip(),
                            str(row.get("outcome", "followup")).strip().lower(),
                            str(row.get("remarks", "")).strip(),
                            str(row.get("final_remarks", "")).strip()
                        ))
                        
                        self.stats["inserted"] += 1
                        
                        # Commit every 100 records
                        if (self.stats["inserted"] + self.stats["skipped"]) % 100 == 0:
                            conn.commit()
                            logger.info(f"Inserted {self.stats['inserted']} records so far...")
                    
                    except Exception as e:
                        logger.error(f"Row {idx+2}: Error inserting record - {e}")
                        self.stats["errors"] += 1
                        continue
                
                conn.commit()
            
            logger.info(f"Marketing data load complete: {self.stats}")
            return self.stats
        
        except Exception as e:
            logger.error(f"Failed to load marketing data: {e}")
            raise
    
    def load_payment_data(self, excel_file: str, sheet_name: str = 0) -> Dict[str, int]:
        """
        Load payment data from Excel file into database.
        
        Args:
            excel_file: Path to Excel file
            sheet_name: Sheet name or index (default: 0)
        
        Returns:
            Dictionary with stats: {inserted, skipped, errors}
        """
        self._reset_stats()
        
        try:
            # Read Excel file
            df = pd.read_excel(excel_file, sheet_name=sheet_name, dtype=str)
            df = normalize_headers(df)
            
            logger.info(f"Loading {len(df)} payment records from {excel_file}")
            
            with self.db as conn:
                cursor = conn.cursor()
                
                for idx, row in df.iterrows():
                    try:
                        # Get or create branch
                        branch_name = str(row.get("branch", "Kathmandu")).strip() or "Kathmandu"
                        branch_id = self._get_or_create_branch(conn, branch_name)
                        
                        # Get or create customer
                        customer_data = {
                            "customer_name": str(row.get("customer_name", "")).strip(),
                            "address": str(row.get("address", "")).strip(),
                            "contact_name": str(row.get("contact_name", "")).strip(),
                            "contact_number": str(row.get("contact_number", "")).strip(),
                            "email": str(row.get("email", "")).strip(),
                        }
                        
                        if not customer_data["customer_name"]:
                            logger.warning(f"Row {idx+2}: Missing customer name, skipping")
                            self.stats["skipped"] += 1
                            continue
                        
                        customer_id = self._get_or_create_customer(conn, customer_data)
                        
                        # Convert amounts to float
                        try:
                            os_amount = float(str(row.get("os_amount", "0")).replace(",", ""))
                        except:
                            os_amount = 0.0
                        
                        try:
                            payment_received = float(str(row.get("payment_received", "0")).replace(",", ""))
                        except:
                            payment_received = 0.0
                        
                        # Insert payment followup
                        cursor.execute("""
                            INSERT INTO payment_followups
                            (date, customer_id, branch_id, os_amount, payment_received, 
                             status, remarks, next_calling_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            normalize_date(row.get("date", "")),
                            customer_id,
                            branch_id,
                            os_amount,
                            payment_received,
                            str(row.get("status", "pending")).strip().lower(),
                            str(row.get("remarks", "")).strip(),
                            normalize_date(row.get("next_calling_date", ""))
                        ))
                        
                        self.stats["inserted"] += 1
                        
                        # Commit every 100 records
                        if (self.stats["inserted"] + self.stats["skipped"]) % 100 == 0:
                            conn.commit()
                            logger.info(f"Inserted {self.stats['inserted']} records so far...")
                    
                    except Exception as e:
                        logger.error(f"Row {idx+2}: Error inserting record - {e}")
                        self.stats["errors"] += 1
                        continue
                
                conn.commit()
            
            logger.info(f"Payment data load complete: {self.stats}")
            return self.stats
        
        except Exception as e:
            logger.error(f"Failed to load payment data: {e}")
            raise
    
    def clear_all_data(self, confirm: bool = False) -> bool:
        """
        Clear all data from database (for testing/reloading).
        
        Args:
            confirm: Must be True to execute
        
        Returns:
            True if cleared, False otherwise
        """
        if not confirm:
            logger.warning("Call with confirm=True to clear data")
            return False
        
        try:
            with self.db as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM calling_reports")
                cursor.execute("DELETE FROM marketing_reports")
                cursor.execute("DELETE FROM payment_followups")
                cursor.execute("DELETE FROM customers")
                cursor.execute("DELETE FROM branches")
                conn.commit()
            
            logger.info("All data cleared from database")
            return True
        
        except Exception as e:
            logger.error(f"Failed to clear data: {e}")
            raise


if __name__ == "__main__":
    """
    Command-line usage example:
    
    python data_loader.py calling_data.xlsx
    python data_loader.py marketing_data.xlsx
    python data_loader.py payment_data.xlsx
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python data_loader.py <excel_file>")
        print("       python data_loader.py calling_data.xlsx")
        sys.exit(1)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    excel_file = sys.argv[1]
    loader = ExcelDataLoader()
    
    # Detect file type from name
    if "calling" in excel_file.lower():
        stats = loader.load_calling_data(excel_file)
    elif "marketing" in excel_file.lower():
        stats = loader.load_marketing_data(excel_file)
    elif "payment" in excel_file.lower():
        stats = loader.load_payment_data(excel_file)
    else:
        print(f"Cannot determine data type from filename: {excel_file}")
        sys.exit(1)
    
    print(f"\nLoad complete!")
    print(f"  Inserted: {stats['inserted']}")
    print(f"  Skipped: {stats['skipped']}")
    print(f"  Errors: {stats['errors']}")
