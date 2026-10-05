from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.deps import get_current_user
from backend.app.database import get_db
from backend.app.models.recommendation import Recommendation
from backend.app.models.user import User
from backend.app.schemas.recommendation import (
    RecommendationCreate,
    RecommendationResponse,
)
from backend.app.services.ml_engine import ml_engine
from backend.app.services.recommendation import (
    CapacityExceededError,
    UnsupportedRegionError,
    recommendation_service,
)


router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post(
    "",
    response_model=RecommendationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_recommendation(
    request: RecommendationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Recommendation:
    if request.application_type not in ml_engine.application_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unsupported application_type",
        )
    if request.traffic_pattern not in ml_engine.traffic_patterns:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unsupported traffic_pattern",
        )

    predicted_vcpu, predicted_ram = ml_engine.predict_resources(
        application_type=request.application_type,
        expected_users_per_day=request.expected_users_per_day,
        concurrent_users=request.concurrent_users,
        storage_required_gb=request.storage_required_gb,
        deployment_region=request.deployment_region,
        traffic_pattern=request.traffic_pattern,
    )

    try:
        comparison = recommendation_service.compare_all_providers(
            predicted_vcpu=predicted_vcpu,
            predicted_ram=predicted_ram,
            deployment_region=request.deployment_region,
            storage_required_gb=request.storage_required_gb,
        )
    except UnsupportedRegionError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except CapacityExceededError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    recommendation_data = {
        **request.model_dump(),
        **comparison.model_dump(),
    }
    recommendation = Recommendation(
        user_id=current_user.id,
        **recommendation_data,
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    return recommendation


@router.get("", response_model=List[RecommendationResponse])
def list_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Recommendation]:
    return (
        db.query(Recommendation)
        .filter(Recommendation.user_id == current_user.id)
        .order_by(Recommendation.created_at.desc(), Recommendation.id.desc())
        .all()
    )


def get_owned_recommendation(
    db: Session,
    user_id: int,
    recommendation_id: int,
) -> Recommendation:
    recommendation = (
        db.query(Recommendation)
        .filter(
            Recommendation.id == recommendation_id,
            Recommendation.user_id == user_id,
        )
        .first()
    )
    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )
    return recommendation


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
def get_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Recommendation:
    return get_owned_recommendation(db, current_user.id, recommendation_id)