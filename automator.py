import os
import asyncio
import ctypes

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from contextlib import asynccontextmanager

from process_router import check_loading_processes, router as process_router
from hardware_router import router as hardware_router
import uvicorn

routers = [hardware_router, process_router]
callable_tasks = [check_loading_processes]


async def process_periodic_tasks():
    while True:
        await asyncio.sleep(1)
        for func in callable_tasks:
            await func()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(process_periodic_tasks())
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

for router in routers:
    app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(f"{os.path.splitext(os.path.basename(__file__))[0]}:app", host="0.0.0.0", port=5041, reload=True)