from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class UserRegisterRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Full name of user",
        json_schema_extra={"example": "Jane Doe"}
    )
    email: str = Field(
        ...,
        description="Valid email address",
        json_schema_extra={"example": "jane@example.com"}
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="Account password (minimum 6 characters)",
        json_schema_extra={"example": "SecretPass123"}
    )


class UserLoginRequest(BaseModel):
    email: str = Field(
        ...,
        description="Registered email address",
        json_schema_extra={"example": "jane@example.com"}
    )
    password: str = Field(
        ...,
        description="Account password",
        json_schema_extra={"example": "SecretPass123"}
    )


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
