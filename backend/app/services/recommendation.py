from typing import Dict, List, Optional, Tuple
import pandas as pd

from backend.app.config import REGION_PRICING_PATH, STORAGE_CATALOG_PATH, VM_CATALOG_PATH
from backend.app.schemas.prediction import CloudComparisonResponse, VMOption


class UnsupportedRegionError(ValueError):
    """Raised when the requested deployment region is not in the pricing/catalog data."""

    def __init__(self, region: str, supported_regions: List[str]):
        self.region = region
        self.supported_regions = supported_regions
        super().__init__(
            f"Unsupported deployment region '{region}'. "
            f"Supported regions are: {', '.join(sorted(supported_regions))}."
        )


class CapacityExceededError(ValueError):
    """Raised when predicted resource requirements exceed all available VM instances."""

    def __init__(
        self,
        predicted_vcpu: int,
        predicted_ram: int,
        region: str,
        max_vcpu: int,
        max_ram: int,
    ):
        self.predicted_vcpu = predicted_vcpu
        self.predicted_ram = predicted_ram
        self.region = region
        self.max_vcpu = max_vcpu
        self.max_ram = max_ram
        super().__init__(
            f"Predicted workload ({predicted_vcpu} vCPU, {predicted_ram} GB RAM) exceeds "
            f"the maximum available single VM capacity in region '{region}' "
            f"({max_vcpu} vCPU, {max_ram} GB RAM). "
            f"Consider horizontal scaling or multi-instance deployment."
        )


class RecommendationService:
    """Service to evaluate VM catalogs, regional multipliers, and storage pricing."""

    def __init__(self) -> None:
        if not VM_CATALOG_PATH.exists():
            raise FileNotFoundError(f"VM catalog not found at: {VM_CATALOG_PATH}")
        if not STORAGE_CATALOG_PATH.exists():
            raise FileNotFoundError(f"Storage catalog not found at: {STORAGE_CATALOG_PATH}")
        if not REGION_PRICING_PATH.exists():
            raise FileNotFoundError(f"Region pricing not found at: {REGION_PRICING_PATH}")

        self.vm_catalog: pd.DataFrame = pd.read_csv(VM_CATALOG_PATH)
        self.storage_catalog: pd.DataFrame = pd.read_csv(STORAGE_CATALOG_PATH)
        self.region_pricing: pd.DataFrame = pd.read_csv(REGION_PRICING_PATH)

        self.supported_regions: List[str] = sorted(
            self.region_pricing["region"].dropna().unique().tolist()
        )

    def validate_region(self, deployment_region: str) -> float:
        """Validates that a region is supported and returns its price multiplier."""
        region_row = self.region_pricing[self.region_pricing["region"] == deployment_region]
        if region_row.empty:
            raise UnsupportedRegionError(deployment_region, self.supported_regions)

        return float(region_row.iloc[0]["price_multiplier"])

    def calculate_storage_cost(
        self, provider: str, storage_required_gb: int
    ) -> Tuple[str, float]:
        """Calculates the cheapest storage cost for the given provider."""
        suitable_storage = self.storage_catalog[
            self.storage_catalog["provider"] == provider
        ].copy()

        if suitable_storage.empty:
            # Fallback standard storage rate ($0.10/GB-month)
            return "Standard Block Storage", round(0.10 * storage_required_gb, 2)

        suitable_storage["total_storage_cost"] = (
            suitable_storage["price_per_gb_month"] * storage_required_gb
        )

        best_storage = suitable_storage.sort_values("total_storage_cost").iloc[0]
        storage_type = str(best_storage["storage_type"])
        storage_cost = float(round(best_storage["total_storage_cost"], 2))

        return storage_type, storage_cost

    def get_suitable_vms(
        self, predicted_vcpu: int, predicted_ram: int, deployment_region: str
    ) -> pd.DataFrame:
        """Filters VMs in the given region that satisfy vCPU and RAM requirements."""
        multiplier = self.validate_region(deployment_region)

        regional_vms = self.vm_catalog[
            self.vm_catalog["region"] == deployment_region
        ].copy()

        if regional_vms.empty:
            raise UnsupportedRegionError(deployment_region, self.supported_regions)

        suitable = regional_vms[
            (regional_vms["vcpu"] >= predicted_vcpu)
            & (regional_vms["ram_gb"] >= predicted_ram)
        ].copy()

        if suitable.empty:
            max_vcpu = int(regional_vms["vcpu"].max())
            max_ram = int(regional_vms["ram_gb"].max())
            raise CapacityExceededError(
                predicted_vcpu=predicted_vcpu,
                predicted_ram=predicted_ram,
                region=deployment_region,
                max_vcpu=max_vcpu,
                max_ram=max_ram,
            )

        suitable["regional_price_per_hour"] = suitable["price_per_hour"] * multiplier
        return suitable

    def recommend_cheapest_vm(
        self,
        predicted_vcpu: int,
        predicted_ram: int,
        deployment_region: str,
        storage_required_gb: int,
    ) -> Dict:
        """Finds the absolute cheapest suitable VM across all providers in the target region."""
        suitable = self.get_suitable_vms(predicted_vcpu, predicted_ram, deployment_region)

        # Sort by regional price per hour ascending
        best_vm = suitable.sort_values("regional_price_per_hour").iloc[0]

        cloud_provider = str(best_vm["provider"])
        vm_type = str(best_vm["vm_type"])
        price_per_hour = float(round(best_vm["regional_price_per_hour"], 4))

        storage_type, storage_cost = self.calculate_storage_cost(
            cloud_provider, storage_required_gb
        )

        compute_monthly_cost = float(round(price_per_hour * 24 * 30, 2))
        total_monthly_cost = float(round(compute_monthly_cost + storage_cost, 2))
        yearly_cost = float(round(total_monthly_cost * 12, 2))

        return {
            "predicted_vcpu": predicted_vcpu,
            "predicted_ram_gb": predicted_ram,
            "cloud_provider": cloud_provider,
            "recommended_vm": vm_type,
            "price_per_hour_usd": price_per_hour,
            "storage_type": storage_type,
            "compute_monthly_cost_usd": compute_monthly_cost,
            "storage_monthly_cost_usd": storage_cost,
            "monthly_cost_usd": total_monthly_cost,
            "yearly_cost_usd": yearly_cost,
            "notes": None,
        }

    def compare_all_providers(
        self,
        predicted_vcpu: int,
        predicted_ram: int,
        deployment_region: str,
        storage_required_gb: int,
    ) -> CloudComparisonResponse:
        """Compares the best matching VM instance across AWS, Azure, and GCP side-by-side."""
        multiplier = self.validate_region(deployment_region)

        regional_vms = self.vm_catalog[
            self.vm_catalog["region"] == deployment_region
        ].copy()

        providers = regional_vms["provider"].unique()
        options: List[VMOption] = []
        any_provider_suitable = False

        for provider in sorted(providers):
            provider_vms = regional_vms[
                (regional_vms["provider"] == provider)
                & (regional_vms["vcpu"] >= predicted_vcpu)
                & (regional_vms["ram_gb"] >= predicted_ram)
            ].copy()

            if provider_vms.empty:
                continue

            any_provider_suitable = True
            provider_vms["regional_price_per_hour"] = (
                provider_vms["price_per_hour"] * multiplier
            )
            best_vm = provider_vms.sort_values("regional_price_per_hour").iloc[0]

            hourly_price = float(round(best_vm["regional_price_per_hour"], 4))
            compute_monthly = float(round(hourly_price * 24 * 30, 2))
            storage_type, storage_cost = self.calculate_storage_cost(
                provider, storage_required_gb
            )
            total_monthly = float(round(compute_monthly + storage_cost, 2))
            yearly = float(round(total_monthly * 12, 2))

            options.append(
                VMOption(
                    cloud_provider=str(provider),
                    vm_type=str(best_vm["vm_type"]),
                    vcpu=int(best_vm["vcpu"]),
                    ram_gb=int(best_vm["ram_gb"]),
                    price_per_hour_usd=hourly_price,
                    compute_monthly_cost_usd=compute_monthly,
                    storage_type=storage_type,
                    storage_monthly_cost_usd=storage_cost,
                    total_monthly_cost_usd=total_monthly,
                    yearly_cost_usd=yearly,
                    is_cheapest=False,
                )
            )

        if not any_provider_suitable:
            max_vcpu = int(regional_vms["vcpu"].max())
            max_ram = int(regional_vms["ram_gb"].max())
            raise CapacityExceededError(
                predicted_vcpu=predicted_vcpu,
                predicted_ram=predicted_ram,
                region=deployment_region,
                max_vcpu=max_vcpu,
                max_ram=max_ram,
            )

        # Mark the cheapest provider option
        cheapest_option = min(options, key=lambda opt: opt.total_monthly_cost_usd)
        cheapest_option.is_cheapest = True

        return CloudComparisonResponse(
            predicted_vcpu=predicted_vcpu,
            predicted_ram_gb=predicted_ram,
            deployment_region=deployment_region,
            storage_required_gb=storage_required_gb,
            options=options,
            recommended_provider=cheapest_option.cloud_provider,
            cheapest_vm=cheapest_option.vm_type,
            cheapest_monthly_cost_usd=cheapest_option.total_monthly_cost_usd,
            notes=None,
        )


# Global singleton instance
recommendation_service = RecommendationService()
