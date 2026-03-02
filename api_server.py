"""
FastAPI server entry point for Ziora Data Imports
Run with: uvicorn api_server:app --host 0.0.0.0 --port 8080
"""

import uvicorn
from ziora_imports.api.service import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )

