#!/usr/bin/env python3
"""
Startup script for the Jarvis AI Assistant (Smart Scheduler)
This script ensures the application starts correctly with proper error handling.
"""

import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_requirements():
    """Check if all required dependencies are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'pydantic',
        'pydantic-settings',
        'jinja2',
        'python-multipart'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        logger.error("Please install them with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_project_structure():
    """Check if the project structure is correct"""
    required_paths = [
        "smart_scheduler",
        "smart_scheduler/main.py",
        "smart_scheduler/core",
        "smart_scheduler/models",
        "smart_scheduler/services",
        "smart_scheduler/templates",
        "smart_scheduler/static"
    ]
    
    missing_paths = []
    for path in required_paths:
        if not Path(path).exists():
            missing_paths.append(path)
    
    if missing_paths:
        logger.error(f"Missing required paths: {', '.join(missing_paths)}")
        logger.error("Please ensure you're running this from the project root directory")
        return False
    
    return True

def create_missing_files():
    """Create any missing essential files"""
    
    # Create __init__.py files if missing
    init_files = [
        "smart_scheduler/__init__.py",
        "smart_scheduler/core/__init__.py",
        "smart_scheduler/models/__init__.py", 
        "smart_scheduler/services/__init__.py"
    ]
    
    for init_file in init_files:
        path = Path(init_file)
        if not path.exists():
            logger.info(f"Creating missing {init_file}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()

def main():
    """Main startup function"""
    logger.info("🚀 Starting Jarvis AI Assistant (Smart Scheduler)")
    
    # Check current working directory
    current_dir = Path.cwd()
    logger.info(f"Current directory: {current_dir}")
    
    # Check if we're in the right directory
    if not Path("smart_scheduler").exists():
        logger.error("❌ smart_scheduler directory not found!")
        logger.error("Please make sure you're running this script from the project root directory")
        logger.error("Your project structure should look like:")
        logger.error("  project_root/")
        logger.error("  ├── smart_scheduler/")
        logger.error("  ├── main.py (this script)")
        logger.error("  └── .env")
        sys.exit(1)
    
    # Check requirements
    logger.info("📦 Checking dependencies...")
    if not check_requirements():
        sys.exit(1)
    
    # Check project structure
    logger.info("📁 Checking project structure...")
    if not check_project_structure():
        sys.exit(1)
    
    # Create missing files
    logger.info("🔧 Creating missing files...")
    create_missing_files()
    
    # Add current directory to Python path
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    try:
        # Import and run the application
        logger.info("⚡ Starting FastAPI server...")
        
        import uvicorn
        from smart_scheduler.main import app
        from smart_scheduler.core.config import settings
        
        logger.info(f"🌐 Server will start at: http://{settings.host}:{settings.port}")
        logger.info(f"📋 Tasks page: http://{settings.host}:{settings.port}/tasks")
        logger.info(f"📊 Dashboard: http://{settings.host}:{settings.port}/")
        
        if settings.debug:
            logger.info(f"📚 API Documentation: http://{settings.host}:{settings.port}/docs")
        
        uvicorn.run(
            "smart_scheduler.main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.debug,
            log_level=settings.log_level.lower()
        )
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("This usually means there's an issue with the project structure or dependencies")
        logger.error("Please check that all files are in the correct locations")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()