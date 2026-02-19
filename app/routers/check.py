# -----------------------------------------------------------------
# app/routers/check.py
# -----------------------------------------------------------------
# Environment check route
# -----------------------------------------------------------------

import platform
import psutil
import os
import logging
from datetime import datetime

from app.services.check import get_yottadb_values
from app.constants_config import *

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

# Tell the router where the templates are
templates = Jinja2Templates(directory="app/templates")

# Create router instance
router = APIRouter(tags=["Env Check"])

@router.get("/check", response_class=HTMLResponse)
async def env_check(request: Request, probe_global: str = "^DIC"):
    # Verify global value to be processed
    logger.info(f"{MAGENTA}The Probe Global to be processed is: {probe_global}.{RESET}")

    logger.info(f"{MAGENTA}Calculate a few monitoring display values.{RESET}")

    # Calculate Uptime
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time

    # Format Disk Usage (e.g., for the DB partition)
    disk = psutil.disk_usage('/')

    ydb_probe = get_yottadb_values(probe_global)

    # Data to pass to the template
    context = {
        "request": request,
        "system": "YottaDB r2.0.0 VEHU VistA",
        "status": "Operational",
        "platform": platform.system(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        # --- New Monitoring Data ---
        "uptime": str(uptime).split('.')[0], # Returns "Days, HH:MM:SS"
        "cpu_usage": f"{psutil.cpu_percent()}%",
        "memory_usage": f"{psutil.virtual_memory().percent}%",
        "disk_free": f"{disk.free // (2**30)} GB", # Free space in Gigabytes
        "load_avg": os.getloadavg() if hasattr(os, 'getloadavg') else "N/A", # (1, 5, 15 min)
        "process_count": len(psutil.pids()),

        # --- Even More ---
        "container_name": os.getenv("CONTAINER_NAME", "Unknown"),
        "image_name": os.getenv("IMAGE_NAME", "Unknown"),
        "process_user": os.getenv("USER") or os.getenv("USERNAME") or "Unknown",
        "working_dir": os.getenv("PWD") or os.getcwd(),
        "ydb_gbldir": os.getenv("ydb_gbldir", "Unknown"),
        "ydb_val_1": ydb_probe["root_value"],
        "ydb_val_2": ydb_probe["first_child"],
        "ydb_val_3": ydb_probe["first_child_value"],
        "probe_global": ydb_probe["probe_global"],
        "ydb_error": ydb_probe["error"],
    }

    logger.info(f"{MAGENTA}The system value is {context['system']}.{RESET}")
    logger.info(f"{MAGENTA}The container name is {context['container_name']}.{RESET}")
    logger.info(f"{MAGENTA}The Python version is {context['python']}.{RESET}")

    return templates.TemplateResponse("environment_check.html", context)


    
