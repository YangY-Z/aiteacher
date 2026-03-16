#!/usr/bin/env python3
"""Run script for the AI Teacher backend server."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8008,
        reload=True,
        workers=1,
    )
