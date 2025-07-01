#!/usr/bin/env python3
"""
Smart Scheduler - Startup Script
===============================

This script provides environment checking and easy startup options for the Smart Scheduler application.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - **%(name)s** - %(levelname)s - %(message)s'
)
logger = logging.getLogger("main")

def check_virtual_environment():
    """Check if we're running in a virtual environment"""
    if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
        logger.warning("⚠️ Not in virtual environment - recommend using 'poetry shell' first")
        return False
    return True

def check_main_module():
    """Check if the main module exists"""
    main_paths = [
        "smart_scheduler/main.py",  # Correct location
        "main.py"                   # Alternative location
    ]
    
    for path in main_paths:
        if Path(path).exists():
            logger.info(f"✅ Found main module at: {path}")
            return path
    
    logger.error("❌ main.py not found. Expected locations:")
    for path in main_paths:
        logger.error(f"   - {path}")
    return None

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import smart_scheduler
        logger.info("✅ Core dependencies available")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.error("   Run 'poetry install' to install dependencies")
        return False

def run_development_server():
    """Start the development server"""
    try:
        # Import and run the server
        from smart_scheduler.main import run_server
        logger.info("🚀 Starting development server...")
        run_server()
    except ImportError as e:
        logger.error(f"❌ Failed to import server: {e}")
        logger.error("   Try running: poetry run scheduler-server")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        sys.exit(1)

def main():
    """Main startup function"""
    logger.info("🤖 Jarvis AI Assistant - Startup Script")
    logger.info("==================================================")
    
    # Environment checks
    check_virtual_environment()
    
    main_module = check_main_module()
    if not main_module:
        logger.error("❌ Environment check failed - exiting")
        sys.exit(1)
    
    if not check_dependencies():
        logger.error("❌ Dependency check failed - exiting")
        sys.exit(1)
    
    # If we get here, try to start the server
    logger.info("✅ Environment checks passed")
    logger.info("🚀 Starting server...")
    
    run_development_server()

if __name__ == "__main__":
    main()