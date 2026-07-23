from typing import Optional

from pydantic import BaseModel, ConfigDict

from src.schemas.profile import ProfileSchema


class LikeDTO(BaseModel):
    liker_profile: ProfileSchema
    liked_profile: Optional[ProfileSchema]
    is_match: bool

    model_config = ConfigDict(from_attributes=True)