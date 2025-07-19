from typing import Dict

from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, JSON, CheckConstraint, func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import pytz  # для работы с timezone-aware датами
from sqlalchemy.orm import mapped_column, Mapped

Base = declarative_base()

class UserProfile(Base):
    __tablename__ = 'user_profiles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, unique=True)
    img_id = Column(String(250), nullable=True, unique=False)
    gender = Column(String(10), nullable=False)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=True)  # можно сделать nullable=False, если нужно
    about = Column(Text, nullable=True)
    meta = Column('meta', JSON, nullable=True)  # 'metadata' — ключевое слово в SQLAlchemy
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=func.now()
    )
    updated_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=func.now()
    )

    # Ограничение на возраст
    __table_args__ = (
        CheckConstraint("age > 0 AND age < 150", name="check_age_range"),
    )