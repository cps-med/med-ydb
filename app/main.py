# ---------------------------------------------------------------------------
# main.py
# ---------------------------------------------------------------------------
# Starting point for med-ydb FastAPI/HTMX/Jinja2 application, which will run
# from within the Docker vehu-311 container and will be accessed via a web
# browser at URL: http://localhost:8010.
#
# Dependencies:
# pip install fastapi "uvicorn[standard]"
# pip install jinja2 python-multipart python-dotenv
#
# Terminal command to start uvicorn:
# docker exec -it vehu-311 bash -lc 'cd /opt/med-ydb && uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload'
#
# Access via: localhost:8010
# Stop server: CTRL + C
# ---------------------------------------------------------------------------

import logging
from pathlib import Path
from app.constants_config import *
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
CSS_DIR = BASE_DIR / "static"

# Routers
from app.routers import check

# Initialize FastAPI app
app = FastAPI()

# Mount static files directory
app.mount("/static", StaticFiles(directory=str(CSS_DIR)), name="static")

# Set up Jinja2 template directory with auto-load for development
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.auto_reload = True

# Register all routers
app.include_router(check.router, tags=["check"])

# -----------------------------------------------------------------
# Configure Python Logging
# -----------------------------------------------------------------
# Configure the root logger to use the level specified.
# Application loggers (e.g., in services, routes) inherit this level.
# Values: DEBUG, INFO, WARNING, ERROR, CRITICAL
# -----------------------------------------------------------------

logging.basicConfig(
    level='DEBUG',
    format='[%(levelname)-7s] %(asctime)s %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


@app.get("/")
async def root():
    return {
        "hello": "world",
        "Message": "Nice to see you!"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": "Med-YDB"}
