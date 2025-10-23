# services/experiment_service.py

import random

from sqlalchemy.dialects.postgresql import psycopg2
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.orm.event import EventORM
from app.models.schemas.experiment import ExperimentCreateModel, ExperimentResponseModel, AssignmentModel
from app.repositories.assignment_repo import AssignmentRepository
from app.repositories.event_repo import EventRepository
from app.repositories.experiment_repo import ExperimentRepository  # We need this to get variants
from app.models.orm.assignment import AssignmentORM
from app.models.orm.experiment import VariantORM, ExperimentORM
from fastapi import HTTPException, status
from typing import Dict, List, Tuple


class ExperimentService:
    def __init__(self, db: Session):
        self.assignment_repo = AssignmentRepository(db)
        self.experiment_repo = ExperimentRepository(db)
        self.event_repo = EventRepository(db)
        self.db = db

    def create_experiment(self, experiment_data: ExperimentCreateModel) -> ExperimentResponseModel:
        """
        Handles the business logic and delegation for creating a new experiment.

        This method delegates creation and provisioning to the ExperimentRepository
        and handles potential validation errors (e.g., total allocation).
        """
        try:
            # Delegate the transactional database operation to the Repository
            experiment_orm = self.experiment_repo.create_experiment(experiment_data)

            experiment_response_model = ExperimentResponseModel.model_validate(experiment_orm)

            return experiment_response_model

        except ValueError as e:
            # Catch business validation errors raised by the Repository (e.g., 100% traffic check)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            # Catch other unexpected errors
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create experiment: {str(e)}"
            )

    # Helper function for traffic allocation (simplified)
    def _allocate_variant(self, variants: List[VariantORM]) -> VariantORM:
        """
        Selects a variant based on configured traffic allocation percentages.
        """
        # Create a list of tuples: (traffic_allocation_percent, VariantORM)
        choices = [(v.traffic_allocation_percent, v) for v in variants]

        # Build the cumulative distribution for weighted random selection
        total_weight = sum(w for w, v in choices)
        if total_weight == 0:
            # Should not happen if experiment creation validates to 100%
            raise ValueError("Experiment has no allocated traffic.")

        # Simple weighted random selection
        r = random.uniform(0, total_weight)
        cumulative_weight = 0
        for weight, variant in choices:
            cumulative_weight += weight
            if r <= cumulative_weight:
                return variant

        # Fallback (should not be reached)
        return variants[-1][1]

    def get_user_assignment(self, experiment_id: str, user_id: str) -> AssignmentModel:
        """
        Gets a user's variant assignment, ensuring idempotency.

        1. Check for existing assignment (idempotency rule).
        2. If none, determine assignment based on traffic.
        3. Persist the new assignment.
        """

        # 1. Check for existing assignment (Idempotency)
        existing_assignment = self.assignment_repo.get_assignment(experiment_id, user_id)
        if existing_assignment:
            print(f"User {user_id} already assigned to variant {existing_assignment.variant_id}. Returning existing.")
            return AssignmentModel.model_validate(existing_assignment)

        # --- If no existing assignment, proceed to allocation ---

        # Fetch the variants and their configurations from the experiment (requires joins/queries)
        experiment = self.experiment_repo.get_experiment_with_variants(experiment_id)  # Assuming this method exists
        if not experiment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment {experiment_id} not found.")

        # Filter to only RUNNING experiments in a real-world scenario
        # if experiment.status != ExperimentStatus.RUNNING:
        #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Experiment is not running.")

        # 2. Determine Assignment
        assigned_variant = self._allocate_variant(experiment.variants)

        # 3. Persist the new assignment
        print(f"Assigning user {user_id} to new variant {assigned_variant.variant_id} for persistence.")
        new_assignment = self.assignment_repo.create_assignment(
            experiment_id=experiment_id,
            user_id=user_id,
            variant_id=assigned_variant.variant_id
        )

        return AssignmentModel.model_validate(new_assignment)

    def get_experiment_results(self, experiment_id: str, config: dict[str, str]):
        """
        Get the following:

        experiment_total_enrollment
        experiment overview: start_date, end_date, total_enrollment, days running, experiment status

        Daily event volume
        Weekly event volume
        Variant Level analysis:
        - Raw count of a specific EventORM.type (e.g., "click") per variant.
        -
        :param experiment_id:
        :param config:
        :return:
        """
        experiment_orm = self.experiment_repo.get_experiment_with_variants(experiment_id)
        variants_orm = experiment_orm.variants
        assignment_orm = self.assignment_repo.get_assignments_for_experiment(experiment_id)
        experiment_events_orm = self.event_repo.get_events_for_experiment(experiment_id)

        # filter out events based on timestamp
        filtered_events: list[EventORM] = [event for event in experiment_events_orm if event.timestamp >= experiment_orm.start_time]

        days_running = (experiment_orm.end_time - experiment_orm.start_time).days if experiment_orm.end_time and datetime.utcnow() > experiment_orm.end_time else (datetime.utcnow() - experiment_orm.start_time).days

        variant_stats = {}  # {variant_name: {users: set(), primary_metric_events_unique_users: set(), events: {event_name: count}}

        global_conversion_rate = len(set([event.user_id for event in experiment_events_orm if event.type == experiment_orm.primary_metric_name])) // len(assignment_orm)



        for event in filtered_events:
            if event.va
            pass

        # conversion_rate = (unique users who fired primary metric / total users in experiment)
        result = {
            "name": experiment_orm.name,
            "description": experiment_orm.description,
            "start_time": experiment_orm.start_time,
            "end_time": experiment_orm.end_time,
            "experiment_days_running": days_running,
            "status": experiment_orm.status,
            "count_variants": len(variants_orm),
            "count_events": len(filtered_events),
            "primary_metric_name": experiment_orm.primary_metric_name,
            "total_users_in_experiment": len(assignment_orm),
            "global_conversion_rate": global_conversion_rate

            # conversion rate, number of users in variant, agg count event type
            "variant_stats": [
                {
                    "variant_name": variant_name,
                    "event_breakdown": {},
                    "conversion_rate": 0.0,
                    "total_users": 0.0,
                 }
            ]

        }

        pass