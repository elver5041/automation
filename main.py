import os
import asyncio

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from routers.process_router  import router as process_router , check_loading_processes
from routers.hardware_router import router as hardware_router, force_terminal_color

ROUTERS = [hardware_router, process_router]
CALLABLE_TASKS = [check_loading_processes]


async def process_periodic_tasks():
    while True:
        await asyncio.sleep(1)
        for func in CALLABLE_TASKS:
            await func()


@asynccontextmanager
async def lifespan(_: FastAPI):
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

for router in ROUTERS:
    app.include_router(router)


if __name__ == "__main__":
    force_terminal_color()
    uvicorn.run(app=f"{os.path.splitext(os.path.basename(__file__))[0]}:app",
                host="0.0.0.0",
                port=5041,
                reload=True)
