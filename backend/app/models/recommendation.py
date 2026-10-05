from datetime import datetime, timezone
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from backend.app.database import Base


class Recommendation(Base):
    """Persisted workload inputs and multi-cloud recommendation results."""

    __tablename__ = "recommendations"
    __table_args__ = (
        CheckConstraint(
            "expected_users_per_day > 0",
            name="ck_recommendations_expected_users_positive",
        ),
        CheckConstraint(
            "concurrent_users > 0",
            name="ck_recommendations_concurrent_users_positive",
        ),
        CheckConstraint(
            "storage_required_gb > 0",
            name="ck_recommendations_storage_positive",
        ),
        CheckConstraint("predicted_vcpu > 0", name="ck_recommendations_vcpu_positive"),
        CheckConstraint("predicted_ram_gb > 0", name="ck_recommendations_ram_positive"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    application_type = Column(String(100), nullable=False)
    expected_users_per_day = Column(Integer, nullable=False)
    concurrent_users = Column(Integer, nullable=False)
    storage_required_gb = Column(Integer, nullable=False)
    deployment_region = Column(String(100), nullable=False)
    traffic_pattern = Column(String(32), nullable=False)
    predicted_vcpu = Column(Integer, nullable=False)
    predicted_ram_gb = Column(Integer, nullable=False)
    options = Column(JSON, nullable=False)
    recommended_provider = Column(String(32), nullable=False)
    cheapest_vm = Column(String(100), nullable=False)
    cheapest_monthly_cost_usd = Column(Numeric(12, 2), nullable=False)
    notes = Column(String(500), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", back_populates="recommendations")

    def __repr__(self) -> str:
        return f"<Recommendation id={self.id} user_id={self.user_id}>"