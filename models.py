
from pydantic import BaseModel, ConfigDict, model_validator
from enum import Enum
from typing import Optional

class Status(Enum):
    Closed = "Closed"
    Loading = "Loading"
    Running = "Running"
    Served = "Served"

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