from enum import Enum


class UserGrade(str, Enum):
    GRADE_10 = "10"
    GRADE_11 = "11"
    GRADE_UNDEFINED = "undefined"