from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from enum import Enum


class ContactCategory(str, Enum):
    personal = "personal"
    work = "work"
    family = "family"


class ContactCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: str
    phone: Optional[str] = Field(default=None, min_length=10, max_length=15)
    category: ContactCategory

    @field_validator("email")
    @classmethod
    def email_must_contain_at(cls, v):
        if "@" not in v:
            raise ValueError("email must contain @")
        return v


class ContactUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    email: Optional[str] = None
    phone: Optional[str] = Field(default=None, min_length=10, max_length=15)
    category: Optional[ContactCategory] = None

    @field_validator("email")
    @classmethod
    def email_must_contain_at(cls, v):
        if v is not None and "@" not in v:
            raise ValueError("email must contain @")
        return v


class ContactResponse(ContactCreate):
    id: int
    created_at: str

    model_config = ConfigDict(from_attributes=True)
