from typing import List, Optional
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    application_type: str = Field(
        ...,
        description="Type of application (e.g., E-Commerce, Blog, Web App)",
        json_schema_extra={"example": "E-Commerce"}
    )
    expected_users_per_day: int = Field(
        ...,
        gt=0,
        description="Expected number of daily unique users",
        json_schema_extra={"example": 25000}
    )
    concurrent_users: int = Field(
        ...,
        gt=0,
        description="Expected peak concurrent users",
        json_schema_extra={"example": 600}
    )
    storage_required_gb: int = Field(
        ...,
        gt=0,
        description="Storage required in GB",
        json_schema_extra={"example": 300}
    )
    deployment_region: str = Field(
        ...,
        description="Cloud deployment region (e.g., asia-south, us-east, europe-west)",
        json_schema_extra={"example": "asia-south"}
    )
    traffic_pattern: str = Field(
        ...,
        description="Traffic pattern: Low, Medium, High",
        json_schema_extra={"example": "High"}
    )


class PredictionResponse(BaseModel):
    # Preserved backward-compatible fields
    predicted_vcpu: int = Field(..., description="Predicted number of vCPUs required")
    predicted_ram_gb: int = Field(..., description="Predicted RAM in GB required")
    cloud_provider: Optional[str] = Field(None, description="Recommended Cloud Provider")
    recommended_vm: Optional[str] = Field(None, description="Recommended VM instance type")
    price_per_hour_usd: Optional[float] = Field(None, description="Estimated hourly compute cost in USD")
    monthly_cost_usd: Optional[float] = Field(None, description="Estimated total monthly cost in USD")
    yearly_cost_usd: Optional[float] = Field(None, description="Estimated yearly cost in USD")

    # Granular cost breakdown fields
    storage_type: Optional[str] = Field(None, description="Selected storage volume type")
    compute_monthly_cost_usd: Optional[float] = Field(None, description="Monthly compute component cost in USD")
    storage_monthly_cost_usd: Optional[float] = Field(None, description="Monthly storage component cost in USD")
    notes: Optional[str] = Field(None, description="Recommendations or capacity notices")


class VMOption(BaseModel):
    cloud_provider: str = Field(..., description="Cloud provider (AWS, Azure, GCP)")
    vm_type: str = Field(..., description="Virtual machine instance type")
    vcpu: int = Field(..., description="Number of vCPUs")
    ram_gb: int = Field(..., description="RAM in GB")
    price_per_hour_usd: float = Field(..., description="Regional hourly rate in USD")
    compute_monthly_cost_usd: float = Field(..., description="Monthly compute cost in USD")
    storage_type: str = Field(..., description="Storage volume type")
    storage_monthly_cost_usd: float = Field(..., description="Monthly storage cost in USD")
    total_monthly_cost_usd: float = Field(..., description="Total monthly cost in USD")
    yearly_cost_usd: float = Field(..., description="Yearly cost in USD")
    is_cheapest: bool = Field(False, description="Flag indicating if this option is the cheapest")


class CloudComparisonResponse(BaseModel):
    predicted_vcpu: int = Field(..., description="Predicted vCPU requirements")
    predicted_ram_gb: int = Field(..., description="Predicted RAM requirements in GB")
    deployment_region: str = Field(..., description="Evaluated deployment region")
    storage_required_gb: int = Field(..., description="Storage volume size in GB")
    options: List[VMOption] = Field(..., description="Suitable VM options from each cloud provider")
    recommended_provider: Optional[str] = Field(None, description="Provider with the lowest total cost")
    cheapest_vm: Optional[str] = Field(None, description="Instance type of cheapest option")
    cheapest_monthly_cost_usd: Optional[float] = Field(None, description="Monthly cost of the cheapest option")
    notes: Optional[str] = Field(None, description="Additional context or recommendations")


class SupportedOptionsResponse(BaseModel):
    application_types: List[str]
    deployment_regions: List[str]
    traffic_patterns: List[str]
