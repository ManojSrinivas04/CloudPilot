from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from backend.app.database import Base


class User(Base):
    """SQLAlchemy model representing an application user."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    resources = relationship(
        "Resource",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    recommendations = relationship(
        "Recommendation",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email='{self.email}'>"
