import uuid
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.orm.event import (
    EventORM,
)  # Import the ORM model from the file we created
from app.models.schemas.event import EventCreateModel


class EventRepository:
    def __init__(self, db: Session):
        """Initializes the repository with a database session."""
        self.db = db

    def get_events_for_experiment(self, experiment_id: str, **kwargs) -> list[EventORM]:
        """
        Retrieves events for a specific experiment, applying optional filters
        for event type and time range.
        """
        stmt = select(EventORM).where(EventORM.experiment_id == experiment_id)

        if event_type := kwargs.get("event_type"):
            stmt = stmt.where(EventORM.type == event_type)

        if start_date := kwargs.get("start_date"):
            stmt = stmt.where(EventORM.timestamp >= start_date)

        if end_date := kwargs.get("end_date"):
            stmt = stmt.where(EventORM.timestamp <= end_date)

        return self.db.scalars(stmt).all()

    def create_event(self, event_data: EventCreateModel) -> EventORM:
        """
        Creates a new event record in the database.

        Args:
            event_data: The Pydantic model containing event details.
            experiment_id: The ID of the experiment the user is currently in (set by service).

        Returns:
            The created EventORM object.
        """

        event_dict = event_data.model_dump(exclude_unset=True)

        if "event_id" not in event_dict:
            event_dict["event_id"] = str(uuid.uuid4())

        if "timestamp" not in event_dict:
            event_dict["timestamp"] = datetime.utcnow()

        event_dict["event_id"] = str(uuid.uuid4())

        db_event = EventORM(**event_dict)
        try:
            self.db.add(db_event)
            self.db.commit()
            self.db.refresh(
                db_event
            )  # Refresh to get auto-generated fields if any (like the final timestamp)

        except IntegrityError as e:
            self.db.rollback()
            print(f"Database Integrity Error during event creation: {e}")

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event data: A required field is missing or a foreign key reference is invalid. Details: {str(e).splitlines()[0]}",
            )

        except OperationalError as e:
            self.db.rollback()
            print(f"Database Operational Error: {e}")

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection failed. Please try again shortly.",
            )

        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"Unexpected SQLAlchemy Error: {e}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected database error occurred.",
            )

        except Exception as e:
            self.db.rollback()
            print(f"General Error during event creation: {e}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected server error occurred during event creation.",
            )

        return db_event
