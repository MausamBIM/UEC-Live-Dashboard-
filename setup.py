"""
Setup & Data Management Script

Use this script to:
1. Initialize database
2. Load Excel data
3. Clear and reload data
4. Check data status

Usage:
    python setup.py load --calling calling_data.xlsx
    python setup.py load --marketing marketing_data.xlsx
    python setup.py load --payment payment_data.xlsx
    python setup.py status
    python setup.py clear (caution: clears all data)
"""

import argparse
import logging
from pathlib import Path
from data_loader import ExcelDataLoader
from db import DatabaseManager, get_db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_data(data_type: str, filepath: str) -> None:
    """Load data from Excel file."""
    
    if not Path(filepath).exists():
        print(f"❌ Error: File not found - {filepath}")
        return
    
    print(f"\n📁 Loading {data_type} data from: {filepath}")
    print("⏳ Processing... (this may take a moment)")
    
    loader = ExcelDataLoader()
    
    try:
        if data_type == "calling":
            stats = loader.load_calling_data(filepath)
        elif data_type == "marketing":
            stats = loader.load_marketing_data(filepath)
        elif data_type == "payment":
            stats = loader.load_payment_data(filepath)
        else:
            print(f"❌ Unknown data type: {data_type}")
            return
        
        print(f"\n✅ {data_type.title()} data loaded successfully!")
        print(f"   ✓ Inserted: {stats['inserted']} records")
        print(f"   ⊘ Skipped: {stats['skipped']} records")
        print(f"   ✗ Errors: {stats['errors']} records")
    
    except Exception as e:
        print(f"❌ Error loading data: {e}")


def show_status() -> None:
    """Show database status."""
    
    print("\n📊 Database Status:")
    print("=" * 50)
    
    try:
        db = get_db()
        
        # Count records
        calling_count = len(db.get_calling_reports())
        marketing_count = len(db.get_marketing_reports())
        payment_count = len(db.get_payment_followups())
        branches = db.get_branches()
        
        print(f"✓ Calling Reports: {calling_count:,} records")
        print(f"✓ Marketing Reports: {marketing_count:,} records")
        print(f"✓ Payment Followups: {payment_count:,} records")
        print(f"✓ Branches: {len(branches) if branches else 0} branches")
        
        total = calling_count + marketing_count + payment_count
        print(f"\n📈 Total Records: {total:,}")
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")


def clear_data() -> None:
    """Clear all data from database."""
    
    print("\n⚠️  WARNING: This will delete ALL data from the database!")
    response = input("Type 'YES' to confirm: ").strip().upper()
    
    if response != "YES":
        print("❌ Cancelled - data not cleared")
        return
    
    print("🗑️  Clearing database...")
    
    try:
        loader = ExcelDataLoader()
        loader.clear_all_data(confirm=True)
        print("✅ Database cleared successfully!")
    
    except Exception as e:
        print(f"❌ Error clearing data: {e}")


def init_database() -> None:
    """Initialize database."""
    
    print("\n🔧 Initializing database...")
    
    try:
        db = DatabaseManager()
        print("✅ Database initialized successfully!")
    
    except Exception as e:
        print(f"❌ Error initializing database: {e}")


def main():
    """Main command-line interface."""
    
    parser = argparse.ArgumentParser(
        description="Database Setup & Data Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup.py load --calling calling_data.xlsx
  python setup.py load --marketing marketing_data.xlsx
  python setup.py load --payment payment_data.xlsx
  python setup.py status
  python setup.py init
  python setup.py clear
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Load command
    load_parser = subparsers.add_parser("load", help="Load data from Excel file")
    load_group = load_parser.add_mutually_exclusive_group(required=True)
    load_group.add_argument("--calling", metavar="FILE", help="Load calling data")
    load_group.add_argument("--marketing", metavar="FILE", help="Load marketing data")
    load_group.add_argument("--payment", metavar="FILE", help="Load payment data")
    
    # Status command
    subparsers.add_parser("status", help="Show database status")
    
    # Init command
    subparsers.add_parser("init", help="Initialize database")
    
    # Clear command
    subparsers.add_parser("clear", help="Clear all data (caution!)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "load":
        if args.calling:
            load_data("calling", args.calling)
        elif args.marketing:
            load_data("marketing", args.marketing)
        elif args.payment:
            load_data("payment", args.payment)
    
    elif args.command == "status":
        show_status()
    
    elif args.command == "init":
        init_database()
    
    elif args.command == "clear":
        clear_data()


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════╗
║         Database Setup & Data Management Tool                ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    main()
