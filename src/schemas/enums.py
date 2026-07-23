from enum import Enum


class SexEnum(Enum):
    MALE = "Мальчик"
    FEMALE = "Девочка"

class SexFilterState(Enum):
    OFF = 0
    ONLY_GIRLS = 1
    ONLY_BOYS = 2