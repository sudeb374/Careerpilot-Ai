"""
CareerPilot AI — SQLAlchemy Base Model

All ORM models should inherit from Base.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy models."""

