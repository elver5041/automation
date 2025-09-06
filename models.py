
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, model_validator

class Status(Enum):
    CLOSED  = "closed"
    LOADING = "loading"
    RUNNING = "running"
    SERVED  = "served"

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class Task(BaseSchema):
    name: str
    port: Optional[int]
    status: str

    @model_validator(mode='before')
    def convert_status(cls, values):
        status = values.get('status')
        if isinstance(status, Status):
            values['status'] = status.value
        return values

class Executable(BaseModel):
    route: str
    exe: str
    port: Optional[int]

class Process(BaseModel):
    name: str
    port: Optional[int]
    pids: list[int]
    status: Status

    def to_task(self) -> Task:
        return Task(**self.model_dump())
