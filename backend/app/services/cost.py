from typing import Dict, Union

from backend.app.models.resource import Resource
from backend.app.services.recommendation import recommendation_service


class CostCalculationService:
    """Calculate estimated resource costs using the existing storage catalog."""

    def calculate_resource_cost(self, resource: Resource) -> Dict[str, Union[int, float, str]]:
        monthly_compute_cost = round(float(resource.hourly_cost) * 24 * 30, 2)
        storage_type, monthly_storage_cost = recommendation_service.calculate_storage_cost(
            resource.cloud_provider,
            resource.storage_gb,
        )
        total_monthly_cost = round(monthly_compute_cost + monthly_storage_cost, 2)

        return {
            "resource_id": resource.id,
            "cloud_provider": resource.cloud_provider,
            "region": resource.region,
            "storage_type": storage_type,
            "hourly_cost": float(resource.hourly_cost),
            "monthly_compute_cost": monthly_compute_cost,
            "monthly_storage_cost": monthly_storage_cost,
            "total_monthly_cost": total_monthly_cost,
            "yearly_cost": round(total_monthly_cost * 12, 2),
        }


cost_calculation_service = CostCalculationService()