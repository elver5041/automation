
import subprocess
import asyncio
import json
from typing import Callable

import requests
import psutil

from fastapi import APIRouter, WebSocket
from fastapi.websockets import WebSocketDisconnect
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, RedirectResponse

from utils import get_ip
from models import Process, Task, Status, Executable


processes: dict[str,Process] = {}
loading_processes: list[str] = []
callable_tasks:list[Callable[[], None]]= []

EXECS: dict[str,Executable] = {
    "comfyUI":      Executable(port=8188, route=r"D:\ai\ComfyUI_windows_portable", exe="automate.bat"),
    "automatic111": Executable(port=7860, route=r"D:\ai\sd.webui",exe="automate.bat"), 
    "koboldAi":     Executable(port=5000, route=r"D:\ai\kobold\KoboldAI-Client",exe="play.bat"),
    "elverbot":     Executable(port=None, route=r"C:\Users\joe20\Desktop\elverbot",exe="run.bat"),
}


async def check_loading_processes() -> None:
    for process_name in list(loading_processes):
        pro = processes[process_name]
        try:
            response = requests.get(f"http://{get_ip()}:{pro.port}", timeout=1)
            if response.status_code == 200:
                loading_processes.remove(process_name)
                pro.status = Status.SERVED
                await notify_clients(Status.SERVED, process_name)
        except requests.exceptions.RequestException:
            pass

router = APIRouter(tags=["tasks"])

connections: list[WebSocket] = []

async def notify_clients(status:Status, name):
    payload = {"name":name, "status":status.value}
    for ws in connections:
        try:
            await ws.send_text(json.dumps(payload))
            print("sent"+json.dumps(payload))
        except Exception:
            connections.remove(ws)

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connections.append(ws)
    try:
        while True:
            await ws.receive_text() 
    except WebSocketDisconnect:
        connections.remove(ws)

@router.get("/tasks", response_model=list[str])
def get_exec_names():
    return JSONResponse(content=list(EXECS.keys()))

@router.get("/processes", response_model=list[Task])
def get_running_procesess():
    return JSONResponse(content=[process.to_task().model_dump() for process in processes.values()])


@router.delete("/processes")
def kill_all_processes():
    global processes
    processes = {}



@router.post("/processes/{name}")
async def open_process(name:str):
    if name in processes:
        raise HTTPException(status_code=400, detail=f"Process {name} is already running")
    if name not in EXECS:
        raise HTTPException(status_code=404, detail=f"Process {name} not found in database")

    try:
        task = EXECS.get(name)
        process = subprocess.Popen(f'start cmd.exe /K "{task.exe}"', shell=True, cwd=task.route)
        parent_process = psutil.Process(process.pid)
        await asyncio.sleep(1)
        children = parent_process.children(recursive=True)
        pids = [c.pid for c in children]
        status = Status.LOADING if task.port else Status.RUNNING
        processes[name] = Process(name = name,  port = task.port, pids = pids, status = status)
        if status == Status.LOADING:
            loading_processes.append(name)
        await notify_clients(status, name)
        return JSONResponse(content={"status": "success", 
                                     "message": f"Started {name}"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/processes/{name}")
async def kill_process(name: str):
    process = processes.get(name)
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    for pid in process.pids:
        try:
            found_process = psutil.Process(pid)
            found_process.terminate()
            found_process.wait()
        except psutil.NoSuchProcess:
            pass
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    del processes[name]
    if name in loading_processes:
        loading_processes.remove(name)
    await notify_clients(Status.CLOSED, name)
    return JSONResponse(content={"status": "success", 
                                 "message": f"Killed process {name} with PID {pid}"})


@router.get("/processes/{name}", response_model=Task)
def get_process(name: str):
    if proc := processes.get(name):
        return JSONResponse(content=proc.to_task().model_dump())
    elif task := EXECS.get(name):
        return JSONResponse(content=Task(name=name, port=task.port, status=Status.CLOSED).model_dump())
    else:
        return HTTPException(status_code=404, detail="no task with that name")


@router.get("/processes/{name}/redirect")
def redirect_to(name: str):
    process = processes.get(name)
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    return RedirectResponse(url=f"http://{get_ip()}:{process.port}")
