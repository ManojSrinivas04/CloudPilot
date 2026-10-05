from datetime import datetime

from pydantic import ConfigDict

from backend.app.schemas.prediction import CloudComparisonResponse, PredictionRequest


class RecommendationCreate(PredictionRequest):
    model_config = ConfigDict(extra="forbid")


class RecommendationResponse(CloudComparisonResponse):
    id: int
    user_id: int
    application_type: str
    expected_users_per_day: int
    concurrent_users: int
    traffic_pattern: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)