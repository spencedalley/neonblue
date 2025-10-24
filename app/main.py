from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, Query
import uvicorn
from sqlalchemy.orm import Session
from starlette import status

from app.core.auth import require_auth_token
from app.core.db import get_db
from app.models.schemas.event import EventResponseModel, EventCreateModel
from app.models.schemas.experiment import (
    ExperimentResponseModel,
    ExperimentCreateModel,
    AssignmentModel,
)
from app.services.event_service import EventService
from fastapi import APIRouter, Depends, status, Path

from app.services.experiment_service import ExperimentService

# 1. Create the FastAPI application instance
app = FastAPI(
    title="Neonblue ai assessment",
    description="Asssessment for neonblueai",
    version="0.0.1",
    dependencies=[Depends(require_auth_token)],
)


@app.post(
    "/experiments",
    response_model=ExperimentResponseModel,  # Defines the expected structure of the successful response
    status_code=status.HTTP_201_CREATED,
)
def post_experiments(
    experiment_data: ExperimentCreateModel,
    db: Session = Depends(get_db),
):
    experiment_service = ExperimentService(db)
    created_experiment = experiment_service.create_experiment(experiment_data)
    return created_experiment


@app.get(
    "/experiments/{experiment_id}/assignment/{user_id}",
    response_model=AssignmentModel,
    status_code=status.HTTP_200_OK,
    summary="Get user assignment",
)
def get_user_variant_assignment(
    experiment_id: str = Path(..., description="The ID of the experiment."),
    user_id: str = Path(..., description="The ID of the user."),
    db: Session = Depends(get_db),
):
    """
    Retrieves a user's variant assignment. If no assignment exists, a new,
    persistent assignment is generated based on traffic allocation rules.
    """
    experiment_service = ExperimentService(db)

    # Delegate core logic to the service
    assignment_model = experiment_service.get_user_assignment(
        experiment_id=experiment_id, user_id=user_id
    )

    return assignment_model


@app.post(
    "/events",
    response_model=EventResponseModel,  # Defines the expected structure of the successful response
    status_code=status.HTTP_201_CREATED,
    summary="Record a new user event.",
)
def post_events(event_data: EventCreateModel, db: Session = Depends(get_db)):
    try:
        # 3. Business Logic: Pass the request data to the Service Layer
        # The Service is instantiated here, injecting the database session
        event_service = EventService(db)

        # The service handles context lookup (assignment) and calls the repository
        event_response_model = event_service.record_event(event_data)

        # 4. Response Serialization: Convert the ORM object back into the Pydantic response model
        return event_response_model

    except Exception as e:
        # 5. Error Handling: Catch exceptions (e.g., database errors) and return a 500
        # In a real app, you'd log the full exception details.
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while recording the event: {str(e)}",
        )


@app.get(
    "/experiments/{experiment_id}/results",
    status_code=status.HTTP_200_OK,
    summary="Get statistics for experiments",
)
def get_experiment_results(
    experiment_id: str,
    event_type: str | None = Query(
        None,
    ),
    start_date: datetime | None = Query(
        None,
    ),
    end_date: datetime | None = Query(
        None,
    ),
    db: Session = Depends(get_db),
):
    filter_params = {
        "event_type": event_type,
        "start_date": start_date,
        "end_date": end_date,
    }
    experiment_service = ExperimentService(db)
    experiment_results = experiment_service.get_experiment_results(
        experiment_id, filter_params
    )
    return experiment_results


# Optional: Entry point for running the application directly (useful for local development)
if __name__ == "__main__":
    # The host and port are the default settings, often used for local development
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    # The format "main:app" means: look in the 'main.py' file and find the 'app' object
