#!/usr/bin/env python3
"""Application entry point for local development.

Usage: `python run.py`
"""
import sys
import uvicorn
from src.core.cli import main


def run():
    """Run the application."""
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        print("Starting Big Data RAG API...")
        uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
    else:
        main()


if __name__ == "__main__":
    run()
