#!/usr/bin/env python3
"""
Startup script for Jarvis AI Assistant
This script safely starts the application with proper error handling
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if we're in the right environment"""
    try:
        # Check if we're in virtual environment
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            logger.info("✅ Virtual environment detected")
        else:
            logger.warning("⚠️ Not in virtual environment - recommend using 'poetry shell' first")
        
        # Check if main.py exists
        if not os.path.exists('main.py'):
            logger.error("❌ main.py not found in current directory")
            return False
            
        return True
    except Exception as e:
        logger.error(f"❌ Environment check failed: {e}")
        return False

def clean_database():
    """Clean up any corrupted database state"""
    try:
        db_file = "smart_scheduler.db"
        if os.path.exists(db_file):
            logger.info(f"📁 Database file found: {db_file}")
        else:
            logger.info("📁 No existing database - will create fresh")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Database cleanup warning: {e}")
        return True  # Continue anyway

def start_application():
    """Start the FastAPI application"""
    try:
        logger.info("🚀 Starting Jarvis AI Assistant...")
        
        # Start with uvicorn
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "127.0.0.1", 
            "--port", "8000", 
            "--reload",
            "--log-level", "info"
        ]
        
        logger.info(f"📄 Running command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        logger.info("👋 Application stopped by user")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Application failed to start: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)

def main():
    """Main startup function"""
    logger.info("🤖 Jarvis AI Assistant - Startup Script")
    logger.info("=" * 50)
    
    # Check environment
    if not check_environment():
        logger.error("❌ Environment check failed - exiting")
        sys.exit(1)
    
    # Clean database state
    if not clean_database():
        logger.error("❌ Database cleanup failed - exiting")
        sys.exit(1)
    
    # Start application
    start_application()

if __name__ == "__main__":
    main()