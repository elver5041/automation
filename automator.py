import os
import asyncio
import ctypes

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from contextlib import asynccontextmanager

from process_router import check_loading_processes, router as process_router




callable_tasks = [check_loading_processes]

async def process_task():
    while True:
        await asyncio.sleep(1)
        for func in callable_tasks:
            await func()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(process_task())
    try:
        yield
    finally:
        task.cancel()
        await task 

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return RedirectResponse(url="/docs")

@app.get("/shutdown")
def shutdown():
    os.system("shutdown /s /t 0")
    return "computer shut down sucesssfully"


@app.get("/monitors/off")
def sleep_monitors():
    ctypes.windll.user32.PostMessageW(0xFFFF, 0x0112, 0xF170, 2)
 

@app.get("/monitors/on")
def wake_monitors():
    ctypes.windll.user32.mouse_event(0x0001, 0, 0, 0, 0) 

app.include_router(process_router)


if __name__ == "__main__":
    import uvicorn
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

    uvicorn.run(f"{os.path.splitext(os.path.basename(__file__))[0]}:app", host="0.0.0.0", port=5041, reload=True)