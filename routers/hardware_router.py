import os
import ctypes
from fastapi import APIRouter


router = APIRouter(tags=["hardware"])

@router.get("/shutdown")
def shutdown():
    os.system("shutdown /s /t 0")
    return "computer shut down sucesssfully"


@router.get("/monitors/off")
def sleep_monitors():
    ctypes.windll.user32.PostMessageW(0xFFFF, 0x0112, 0xF170, 2)


@router.get("/monitors/on")
def wake_monitors():
    ctypes.windll.user32.mouse_event(0x0001, 0, 0, 0, 0)

def force_terminal_color():
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
