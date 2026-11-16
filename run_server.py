#!/usr/bin/env python3
"""
Simple script to run the FastAPI subway map server
"""

import logging
import uvicorn
from app import app

if __name__ == "__main__":
    logging.debug("🚇 Starting Subway Map Server...")
    logging.debug("📍 Open your browser to: http://localhost:8008")
    logging.debug("🛑 Press Ctrl+C to stop the server")

    uvicorn.run(
        "app:app",  # Use import string for reload to work
        host="0.0.0.0", 
        port=8008, 
        reload=True,  # Auto-reload on file changes
        reload_dirs=["app", "templates", "static"],
        log_level="info"
    )
