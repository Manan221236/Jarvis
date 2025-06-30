#!/usr/bin/env python3
"""
Simple server startup script
Save as start_server.py and run: python start_server.py
"""

import os
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    try:
        print("🚀 Starting Jarvis AI Assistant...")
        
        # Import uvicorn
        import uvicorn
        
        # Start server
        uvicorn.run(
            "smart_scheduler.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the smart-scheduler directory")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Try: pip install uvicorn fastapi")

if __name__ == "__main__":
    main()