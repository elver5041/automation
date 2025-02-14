
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, model_validator

class Status(Enum):
    CLOSED  = "Closed"
    LOADING = "Loading"
    RUNNING = "Running"
    SERVED  = "Served"

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

class Process(BaseModel):
    name:str
    port: Optional[int]
    pids: list[int]
    status: Status
