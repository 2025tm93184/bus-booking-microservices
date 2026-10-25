
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    total_seats: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "total_seats > 0",
            name="ck_trip_positive_capacity",
        ),
    )


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id"), nullable=False
    )
    seat_number: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="RESERVED"
    )

    __table_args__ = (
        UniqueConstraint(
            "trip_id",
            "seat_number",
            name="uq_trip_seat",
        ),
        CheckConstraint(
            "seat_number > 0",
            name="ck_positive_seat_number",
        ),
    )
