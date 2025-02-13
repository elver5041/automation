
import subprocess
import psutil
import asyncio
import requests

from utils import get_ip

from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, RedirectResponse

from typing import Callable
from models import Process, Task, Status


processes: dict[str,Process] = {}
loading_processes: list[str] = []
callable_tasks:list[Callable[[], None]]= []

EXECS: dict[str,tuple[str,str,int|None]] = {
    "text ai":(r"D:\ai\kobold\KoboldAI-Client","play.bat", 5000),
    "image ai":(r"D:\ai\sd.webui","automate.bat", 7860), 
    "elverbot":(r"C:\Users\joe20\Desktop\elverbot","run.bat"),
}

EXECS = {key: value + (None,) * (3 - len(value)) for key, value in EXECS.items()}


async def check_loading_processes() -> None:
    for process_name in loading_processes:
        pro = processes[process_name]
        try:
            response = requests.get(f"http://{get_ip()}:{pro.port}", timeout=1)
            if response.status_code == 200:
                loading_processes.remove(process_name)
                pro.status = Status.Served
        except requests.exceptions.RequestException as e:
            pass

router = APIRouter(tags=["tasks"])

@router.get("/tasks", response_model=list[str])
def get_exec_names():
    return JSONResponse(content=[k for k in EXECS.keys()])

@router.get("/processes", response_model=list[Task])
def get_tasks():
    return JSONResponse(content=[Task(**process.model_dump()).model_dump() for process in processes.values()])


@router.post("/open/{name}")
async def open_process(name:str):
    if name in processes:
        raise HTTPException(status_code=400, detail=f"Process {name} is already running")
    if name not in EXECS:
        raise HTTPException(status_code=404, detail=f"Process {name} not found in database")
    
    try:
        (dir, file, port) = EXECS.get(name)
        process = subprocess.Popen(f'start cmd.exe /K "{file}"', shell=True, cwd=dir)
        parent_process = psutil.Process(process.pid)
        await asyncio.sleep(1)
        children = parent_process.children(recursive=True)
        pids = [c.pid for c in children]
        status = Status.Loading if EXECS[name][2] else Status.Running
        processes[name] = Process(name = name,  port = port, pids = pids, status = status)
        if status == Status.Loading:
            loading_processes.append(name)
        return JSONResponse(content={"status": "success", "message": f"Started {name}"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/close/{name}")
def kill_process(name: str):
    process = processes.get(name)
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    for pid in process.pids:
        try:
            cProcess = psutil.Process(pid)
            cProcess.terminate() 
            cProcess.wait() 
        except psutil.NoSuchProcess:
            pass
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    del processes[name]
    if name in loading_processes:
        loading_processes.remove(name)
    return JSONResponse(content={"status": "success", "message": f"Killed process {name} with PID {pid}"})

@router.get("/redirect/{name}")
def redirect_to(name: str):
    process = processes.get(name)
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    return RedirectResponse(url=f"http://{get_ip()}:{process.port}")