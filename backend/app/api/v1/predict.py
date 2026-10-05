from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.prediction import (
    CloudComparisonResponse,
    PredictionRequest,
    PredictionResponse,
    SupportedOptionsResponse,
)
from backend.app.services.ml_engine import ml_engine
from backend.app.services.recommendation import (
    CapacityExceededError,
    UnsupportedRegionError,
    recommendation_service,
)

router = APIRouter()


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict resources and recommend cheapest VM",
    description=(
        "Uses the trained Random Forest model to predict vCPU and RAM requirements "
        "and evaluates cloud catalogs to recommend the most cost-effective VM."
    ),
)
def predict_cloud_resources(request: PredictionRequest) -> PredictionResponse:
    """Evaluates workload specifications and returns the cheapest suitable VM recommendation."""
    try:
        # Step 1: ML Resource Prediction
        predicted_vcpu, predicted_ram = ml_engine.predict_resources(
            application_type=request.application_type,
            expected_users_per_day=request.expected_users_per_day,
            concurrent_users=request.concurrent_users,
            storage_required_gb=request.storage_required_gb,
            deployment_region=request.deployment_region,
            traffic_pattern=request.traffic_pattern,
        )

        # Step 2: Catalog matching & cost calculation
        result = recommendation_service.recommend_cheapest_vm(
            predicted_vcpu=predicted_vcpu,
            predicted_ram=predicted_ram,
            deployment_region=request.deployment_region,
            storage_required_gb=request.storage_required_gb,
        )

        return PredictionResponse(**result)

    except UnsupportedRegionError as ure:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ure)
        )

    except CapacityExceededError as cee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(cee)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during prediction: {str(e)}"
        )


@router.post(
    "/predict/compare",
    response_model=CloudComparisonResponse,
    summary="Compare recommendations across AWS, Azure, and GCP",
    description="Returns the best matching VM and total cost breakdown for AWS, Azure, and GCP side-by-side.",
)
def compare_cloud_providers(request: PredictionRequest) -> CloudComparisonResponse:
    """Returns side-by-side recommendations across AWS, Azure, and GCP."""
    try:
        # Step 1: ML Resource Prediction
        predicted_vcpu, predicted_ram = ml_engine.predict_resources(
            application_type=request.application_type,
            expected_users_per_day=request.expected_users_per_day,
            concurrent_users=request.concurrent_users,
            storage_required_gb=request.storage_required_gb,
            deployment_region=request.deployment_region,
            traffic_pattern=request.traffic_pattern,
        )

        # Step 2: Multi-provider comparison
        comparison = recommendation_service.compare_all_providers(
            predicted_vcpu=predicted_vcpu,
            predicted_ram=predicted_ram,
            deployment_region=request.deployment_region,
            storage_required_gb=request.storage_required_gb,
        )

        return comparison

    except UnsupportedRegionError as ure:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ure)
        )

    except CapacityExceededError as cee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(cee)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during multi-cloud comparison: {str(e)}"
        )


@router.get(
    "/supported-options",
    response_model=SupportedOptionsResponse,
    summary="Get supported application types, regions, and traffic patterns",
)
def get_supported_options() -> SupportedOptionsResponse:
    """Returns the valid choices for form dropdowns in frontends."""
    return SupportedOptionsResponse(
        application_types=ml_engine.application_types,
        deployment_regions=recommendation_service.supported_regions,
        traffic_patterns=ml_engine.traffic_patterns,
    )
