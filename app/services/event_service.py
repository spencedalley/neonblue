# services/event_service.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.repositories.event_repo import EventRepository
from app.models.schemas.event import EventCreateModel, EventResponseModel
from app.models.orm.event import EventORM
from app.repositories.assignment_repo import (
    AssignmentRepository,
)  # Assuming an Assignment Repository exists


class EventService:
    def __init__(self, db: Session):
        """Initializes the service with repositories it needs."""
        self.event_repo = EventRepository(db)
        # We need the AssignmentRepo to look up the user's experiment context
        self.assignment_repo = AssignmentRepository(db)

    def record_event(self, event_data: EventCreateModel) -> EventResponseModel:
        """
        Handles the business logic for recording an event.
        1. Finds the active experiment assignment for the user.
        2. Records the event with the correct experiment context.
        """
        try:
            recorded_event = self.event_repo.create_event(event_data=event_data)

            return EventResponseModel(
                event_id=recorded_event.event_id, experiment_id=recorded_event.experiment_id
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create event",
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Encountered error when creating event",
            )
