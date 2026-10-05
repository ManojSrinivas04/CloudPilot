from datetime import datetime, timezone
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from backend.app.database import Base


class Resource(Base):
    """SQLAlchemy model for a cloud resource owned by an application user."""

    __tablename__ = "resources"
    __table_args__ = (
        CheckConstraint("vcpu > 0", name="ck_resources_vcpu_positive"),
        CheckConstraint("ram_gb > 0", name="ck_resources_ram_positive"),
        CheckConstraint("storage_gb >= 0", name="ck_resources_storage_nonnegative"),
        CheckConstraint("hourly_cost >= 0", name="ck_resources_cost_nonnegative"),
        CheckConstraint(
            "cloud_provider IN ('AWS', 'Azure', 'GCP')",
            name="ck_resources_cloud_provider",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(150), nullable=False)
    cloud_provider = Column(String(32), nullable=False)
    region = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    vcpu = Column(Integer, nullable=False)
    ram_gb = Column(Numeric(10, 2), nullable=False)
    storage_gb = Column(Integer, nullable=False)
    hourly_cost = Column(Numeric(12, 6), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", back_populates="resources")

    def __repr__(self) -> str:
        return f"<Resource id={self.id} user_id={self.user_id} name='{self.name}'>"