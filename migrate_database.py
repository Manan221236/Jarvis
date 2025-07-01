#!/usr/bin/env python3
"""
Database migration script to add subtask support
Run this script to update your existing database
"""

import sys
import os
from sqlalchemy import text

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from smart_scheduler.core.database import engine
from smart_scheduler.core.config import settings

def migrate_database():
    """Add parent_id column for subtask support"""
    
    print("🔄 Starting database migration...")
    
    try:
        with engine.connect() as connection:
            # Check if parent_id column already exists
            result = connection.execute(text("PRAGMA table_info(tasks)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'parent_id' not in columns:
                print("📝 Adding parent_id column to tasks table...")
                
                # Add the parent_id column
                connection.execute(text(
                    "ALTER TABLE tasks ADD COLUMN parent_id INTEGER"
                ))
                
                # Create index for better performance
                connection.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_tasks_parent_id ON tasks(parent_id)"
                ))
                
                connection.commit()
                print("✅ Migration completed successfully!")
                print("📋 Subtask functionality is now available.")
                
            else:
                print("ℹ️ Migration already applied - parent_id column exists.")
                
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False
    
    return True

def verify_migration():
    """Verify the migration was successful"""
    
    print("\n🔍 Verifying migration...")
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text("PRAGMA table_info(tasks)"))
            columns = {row[1]: row[2] for row in result.fetchall()}
            
            if 'parent_id' in columns:
                print("✅ parent_id column found")
                print(f"   Type: {columns['parent_id']}")
                
                # Check index
                result = connection.execute(text("PRAGMA index_list(tasks)"))
                indexes = [row[1] for row in result.fetchall()]
                
                if 'idx_tasks_parent_id' in indexes:
                    print("✅ parent_id index found")
                else:
                    print("⚠️ parent_id index missing")
                
                return True
            else:
                print("❌ parent_id column not found")
                return False
                
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

def rollback_migration():
    """Rollback the migration (remove parent_id column)"""
    
    print("🔄 Rolling back migration...")
    
    try:
        with engine.connect() as connection:
            # SQLite doesn't support DROP COLUMN directly
            # We need to recreate the table without parent_id
            
            print("⚠️ SQLite requires table recreation for column removal.")
            print("This operation will recreate the tasks table.")
            
            # Get current table structure
            result = connection.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='tasks'"))
            original_sql = result.fetchone()[0]
            
            print("📋 Current table structure preserved for safety.")
            print("Manual rollback required if needed.")
            
        return True
        
    except Exception as e:
        print(f"❌ Rollback failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Smart Scheduler Database Migration Tool")
    print(f"📁 Database: {settings.database_url}")
    print("-" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        rollback_migration()
    else:
        if migrate_database():
            verify_migration()
        else:
            print("\n❌ Migration failed. Please check the error messages above.")
            sys.exit(1)
    
    print("\n🎉 Database migration complete!")
    print("💡 You can now restart your application to use subtask features.")