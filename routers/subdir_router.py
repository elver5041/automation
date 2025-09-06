from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path
import string

router = APIRouter(tags=["file_browser"])

@router.get("/list")
def list_files(path: str = ""):
    # Accept absolute or relative paths
    target = Path(path).expanduser().resolve()

    if not target.exists() or not target.is_dir():
        return {"error": "Invalid path"}

    files = []
    try:
        for p in target.iterdir():
            try:
                files.append({
                    "name": p.name,
                    "is_dir": p.is_dir()
                })
            except PermissionError:
                # Skip entries we can’t access
                continue
    except PermissionError:
        return {"error": f"Access denied: {str(target)}"}

    return {"path": str(target), "files": files}

@router.get("/download")
def download_file(path: str):
    target = Path(path).expanduser().resolve()
    if target.exists() and target.is_file():
        return FileResponse(target)
    return {"error": "Invalid file"}

@router.get("/drives")
def list_drives():
    drives = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if Path(drive).exists():
            drives.append(drive)
    return {"drives": drives}
