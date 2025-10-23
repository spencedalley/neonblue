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

    def get_events_for_experiment(self, experiment_id: str) -> list[EventORM]:

        stmt = select(EventORM).where(EventORM.experiment_id == experiment_id)

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

        # 1. Convert Pydantic data to a dictionary, ensuring 'timestamp' is present
        event_dict = event_data.model_dump(exclude_unset=True)

        # Ensure ID is set
        if "event_id" not in event_dict:
            event_dict["event_id"] = str(uuid.uuid4())

        # Ensure timestamp is set if not provided by Pydantic model
        if "timestamp" not in event_dict:
            event_dict["timestamp"] = datetime.utcnow()

        # 2. Add required database fields
        event_dict["event_id"] = str(uuid.uuid4())

        # 3. Create the ORM instance
        db_event = EventORM(**event_dict)
        try:
            # 4. Save to the database
            self.db.add(db_event)
            self.db.commit()
            self.db.refresh(
                db_event
            )  # Refresh to get auto-generated fields if any (like the final timestamp)
            # 🎯 Targeted Error Handling: Mapping database errors to HTTP errors
        except IntegrityError as e:
            # Catch errors like Foreign Key or NOT NULL constraint violations (bad user input)
            self.db.rollback()
            print(f"Database Integrity Error during event creation: {e}")

            # 400 Bad Request: The request data violates a database rule
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event data: A required field is missing or a foreign key reference is invalid. Details: {str(e).splitlines()[0]}",
            )

        except OperationalError as e:
            # Catch errors related to connectivity (e.g., database is down)
            self.db.rollback()
            print(f"Database Operational Error: {e}")

            # 503 Service Unavailable: The database is currently unreachable
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection failed. Please try again shortly.",
            )

        except SQLAlchemyError as e:
            # Catch all other SQLAlchemy-related errors (e.g., query execution issues)
            self.db.rollback()
            print(f"Unexpected SQLAlchemy Error: {e}")

            # 500 Internal Server Error: General database processing failure
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected database error occurred.",
            )

        except Exception as e:
            # Catch all non-SQLAlchemy errors (e.g., errors in Python logic)
            self.db.rollback()
            print(f"General Error during event creation: {e}")

            # 500 Internal Server Error: General application failure
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected server error occurred during event creation.",
            )

        return db_event
