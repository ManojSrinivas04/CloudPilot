from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


CloudProvider = Literal["AWS", "Azure", "GCP"]


class ResourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    cloud_provider: CloudProvider
    region: str = Field(..., min_length=1, max_length=100)
    resource_type: str = Field(..., min_length=1, max_length=100)
    vcpu: int = Field(..., gt=0)
    ram_gb: float = Field(..., gt=0)
    storage_gb: int = Field(..., ge=0)
    hourly_cost: float = Field(..., ge=0)

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        allow_inf_nan=False,
    )


class ResourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    cloud_provider: Optional[CloudProvider] = None
    region: Optional[str] = Field(None, min_length=1, max_length=100)
    resource_type: Optional[str] = Field(None, min_length=1, max_length=100)
    vcpu: Optional[int] = Field(None, gt=0)
    ram_gb: Optional[float] = Field(None, gt=0)
    storage_gb: Optional[int] = Field(None, ge=0)
    hourly_cost: Optional[float] = Field(None, ge=0)

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        allow_inf_nan=False,
    )

    @model_validator(mode="after")
    def validate_patch_fields(self):
        if not self.model_fields_set:
            raise ValueError("At least one resource field must be provided")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Resource fields cannot be null")
        return self


class ResourceResponse(BaseModel):
    id: int
    user_id: int
    name: str
    cloud_provider: CloudProvider
    region: str
    resource_type: str
    vcpu: int
    ram_gb: float
    storage_gb: int
    hourly_cost: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResourceCostResponse(BaseModel):
    resource_id: int
    cloud_provider: CloudProvider
    region: str
    storage_type: str
    hourly_cost: float
    monthly_compute_cost: float
    monthly_storage_cost: float
    total_monthly_cost: float
    yearly_cost: float