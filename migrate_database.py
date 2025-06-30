#!/usr/bin/env python3
"""
Database migration script to add time scheduling fields
Save this as migrate_database.py in your project root and run it
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_database():
    """Add new columns for time scheduling"""
    
    try:
        from smart_scheduler.core.database import engine
        from sqlalchemy import text
        
        logger.info("🚀 Starting database migration...")
        
        # List of migration queries
        migration_queries = [
            # Add new scheduling columns to tasks table
            "ALTER TABLE tasks ADD COLUMN scheduled_date DATE;",
            "ALTER TABLE tasks ADD COLUMN start_time TIME;", 
            "ALTER TABLE tasks ADD COLUMN end_time TIME;",
            "ALTER TABLE tasks ADD COLUMN all_day BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE tasks ADD COLUMN location VARCHAR(255);",
            "ALTER TABLE tasks ADD COLUMN energy_level VARCHAR(50);",
            "ALTER TABLE tasks ADD COLUMN focus_time_required BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE tasks ADD COLUMN notes TEXT;",
            "ALTER TABLE tasks ADD COLUMN attachment_urls TEXT;",
            "ALTER TABLE tasks ADD COLUMN task_type VARCHAR(50) DEFAULT 'task';",
            "ALTER TABLE tasks ADD COLUMN recurrence_type VARCHAR(50) DEFAULT 'none';",
            "ALTER TABLE tasks ADD COLUMN recurrence_interval INTEGER DEFAULT 1;",
            "ALTER TABLE tasks ADD COLUMN recurrence_end_date DATE;",
            "ALTER TABLE tasks ADD COLUMN parent_task_id INTEGER;",
            "ALTER TABLE tasks ADD COLUMN project_id INTEGER;",
        ]
        
        with engine.connect() as connection:
            # Start transaction
            trans = connection.begin()
            
            try:
                for query in migration_queries:
                    try:
                        connection.execute(text(query))
                        logger.info(f"✅ Executed: {query.strip()}")
                    except Exception as e:
                        error_msg = str(e).lower()
                        if any(phrase in error_msg for phrase in [
                            "duplicate column", "already exists", "column already exists"
                        ]):
                            logger.info(f"⏭️  Skipped (already exists): {query.strip()}")
                        else:
                            logger.error(f"❌ Failed: {query.strip()} - {e}")
                            raise
                
                # Commit transaction
                trans.commit()
                logger.info("🎉 Database migration completed successfully!")
                
                return True
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                logger.error(f"❌ Migration failed, rolling back: {e}")
                return False
                
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("Make sure you're running this from the project root directory")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def verify_migration():
    """Verify that migration was successful"""
    try:
        from smart_scheduler.core.database import engine
        from sqlalchemy import text
        
        logger.info("🔍 Verifying migration...")
        
        with engine.connect() as connection:
            # Check if new columns exist
            result = connection.execute(text("PRAGMA table_info(tasks);"))
            columns = [row[1] for row in result.fetchall()]
            
            new_columns = [
                'scheduled_date', 'start_time', 'end_time', 'all_day', 
                'location', 'energy_level', 'focus_time_required'
            ]
            
            missing_columns = []
            for col in new_columns:
                if col in columns:
                    logger.info(f"✅ Column exists: {col}")
                else:
                    missing_columns.append(col)
            
            if missing_columns:
                logger.error(f"❌ Missing columns: {missing_columns}")
                return False
            else:
                logger.info("🎉 All new columns verified successfully!")
                return True
                
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

def main():
    """Main migration function"""
    print("=" * 60)
    print("🤖 JARVIS AI Assistant - Database Migration")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("smart_scheduler"):
        print("❌ Error: smart_scheduler directory not found!")
        print("Please run this script from the project root directory.")
        sys.exit(1)
    
    # Run migration
    if migrate_database():
        # Verify migration
        if verify_migration():
            print("\n✅ Migration completed successfully!")
            print("You can now use the new time scheduling features.")
        else:
            print("\n❌ Migration verification failed!")
            sys.exit(1)
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()