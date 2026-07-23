from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict

from src.schemas.enums import SexFilterState, SexEnum


class ProfileSchema(BaseModel):
    id: Annotated[int, Field()]
    tg_id: Annotated[int, Field()]

    name: Annotated[str, Field(min_length=1, max_length=100)]
    age: Annotated[int, Field(ge=14, le=80)]
    sex: Annotated[SexEnum, Field()]
    town: Annotated[str, Field(min_length=2, max_length=100)]
    description: Annotated[str, Field(max_length=1024)]

    is_active: Annotated[bool, Field(default=True)]
    s3_path: Annotated[str | None, Field()]
    sex_filter: Annotated[SexFilterState, Field()]

    created_at: Annotated[datetime, Field()]
    modified_at: Annotated[datetime, Field()]

    model_config = ConfigDict(from_attributes=True)

class ProfileCreateDTO(BaseModel):
    tg_id: int
    name: str = Field(min_length=2, max_length=64)
    age: int = Field(ge=14, le=67)
    sex: SexEnum
    town: str = Field(min_length=2, max_length=30)
    description: str = Field(max_length=1024)
    s3_path: str | None = None

class ProfileUpdateDTO(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    age: int = Field(ge=14, le=67)
    sex: SexEnum
    town: str = Field(min_length=2, max_length=30)
    description: str = Field(max_length=1024)
    s3_path: str