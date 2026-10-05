from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.deps import get_current_user
from backend.app.database import get_db
from backend.app.models.resource import Resource
from backend.app.models.user import User
from backend.app.schemas.resource import ResourceCostResponse
from backend.app.schemas.resource import (
    ResourceCreate,
    ResourceResponse,
    ResourceUpdate,
)
from backend.app.services.cost import cost_calculation_service


router = APIRouter(prefix="/resources", tags=["Resources"])


@router.post(
    "",
    response_model=ResourceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_resource(
    request: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Resource:
    resource = Resource(**request.model_dump(), user_id=current_user.id)
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


@router.get("", response_model=List[ResourceResponse])
def list_resources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Resource]:
    return (
        db.query(Resource)
        .filter(Resource.user_id == current_user.id)
        .order_by(Resource.created_at.desc(), Resource.id.desc())
        .all()
    )


def get_owned_resource(db: Session, user_id: int, resource_id: int) -> Resource:
    resource = (
        db.query(Resource)
        .filter(Resource.id == resource_id, Resource.user_id == user_id)
        .first()
    )
    if resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found",
        )
    return resource


@router.get("/{resource_id}", response_model=ResourceResponse)
def get_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Resource:
    return get_owned_resource(db, current_user.id, resource_id)


@router.get("/{resource_id}/cost", response_model=ResourceCostResponse)
def get_resource_cost(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResourceCostResponse:
    resource = get_owned_resource(db, current_user.id, resource_id)
    return cost_calculation_service.calculate_resource_cost(resource)


@router.patch("/{resource_id}", response_model=ResourceResponse)
def update_resource(
    resource_id: int,
    request: ResourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Resource:
    resource = get_owned_resource(db, current_user.id, resource_id)
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(resource, field, value)
    db.commit()
    db.refresh(resource)
    return resource


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    resource = get_owned_resource(db, current_user.id, resource_id)
    db.delete(resource)
    db.commit()