# services/experiment_service.py

import random
from collections import defaultdict
from sqlalchemy.dialects.postgresql import psycopg2
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.orm.event import EventORM
from app.models.schemas.experiment import (
    ExperimentCreateModel,
    ExperimentResponseModel,
    AssignmentModel,
)
from app.repositories.assignment_repo import AssignmentRepository
from app.repositories.event_repo import EventRepository
from app.repositories.experiment_repo import ExperimentRepository
from app.models.orm.assignment import AssignmentORM
from app.models.orm.experiment import VariantORM, ExperimentORM
from fastapi import HTTPException, status
from typing import Dict, List, Tuple, Optional


class ExperimentService:
    def __init__(self, db: Session):
        self.assignment_repo = AssignmentRepository(db)
        self.experiment_repo = ExperimentRepository(db)
        self.event_repo = EventRepository(db)
        self.db = db

    def create_experiment(
        self, experiment_data: ExperimentCreateModel
    ) -> ExperimentResponseModel:
        """
        Handles the business logic and delegation for creating a new experiment.

        This method delegates creation and provisioning to the ExperimentRepository
        and handles potential validation errors (e.g., total allocation).
        """
        try:
            # Delegate the transactional database operation to the Repository
            experiment_orm = self.experiment_repo.create_experiment(experiment_data)

            experiment_response_model = ExperimentResponseModel.model_validate(
                experiment_orm
            )

            return experiment_response_model

        except ValueError as e:
            # Catch business validation errors raised by the Repository (e.g., 100% traffic check)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            # Catch other unexpected errors
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create experiment: {str(e)}",
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
        existing_assignment = self.assignment_repo.get_assignment(
            experiment_id, user_id
        )
        if existing_assignment:
            print(
                f"User {user_id} already assigned to variant {existing_assignment.variant_id}. Returning existing."
            )
            return AssignmentModel.model_validate(existing_assignment)

        # --- If no existing assignment, proceed to allocation ---

        # Fetch the variants and their configurations from the experiment (requires joins/queries)
        experiment = self.experiment_repo.get_experiment_with_variants(
            experiment_id
        )  # Assuming this method exists
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment {experiment_id} not found.",
            )

        # Filter to only RUNNING experiments in a real-world scenario
        # if experiment.status != ExperimentStatus.RUNNING:
        #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Experiment is not running.")

        # 2. Determine Assignment
        assigned_variant = self._allocate_variant(experiment.variants)

        # 3. Persist the new assignment
        print(
            f"Assigning user {user_id} to new variant {assigned_variant.variant_id} for persistence."
        )
        new_assignment = self.assignment_repo.create_assignment(
            experiment_id=experiment_id,
            user_id=user_id,
            variant_id=assigned_variant.variant_id,
        )

        return AssignmentModel.model_validate(new_assignment)

    def _generate_user_stats(self):
        pass

    def _filter_events(
        self,
        events: list[EventORM],
        user_to_variant_assignment_lookup: dict[str, dict[str, str]],
    ) -> list[EventORM]:
        filtered_events: list[EventORM] = []
        for event in events:
            user_assignment_timestamp = user_to_variant_assignment_lookup[
                event.user_id
            ]["assignment_timestamp"]
            if event.timestamp >= user_assignment_timestamp:
                filtered_events.append(event)
        return filtered_events

    def _generate_variant_agg_stats(
        self,
        assignment_orm: list[AssignmentORM],
        experiment_events_orm: list[EventORM],
        variant_id_to_variant_name: dict[str, dict[str, str]],
        user_to_variant_assignment: dict[str, str],
        primary_metric_name: str,
    ):
        # aggregate event stats on variant level
        variant_stats = {}  # {variant_id: {total_users, metric_counts, conversion_users

        # go over every assignment for the experiment and populate the variant stats
        for assignment in assignment_orm:
            variant_id = assignment.variant_id
            variant_name = variant_id_to_variant_name[variant_id]
            user_id = assignment.user_id

            if variant_name not in variant_stats:
                variant_stats[variant_name] = {
                    "users": set(),
                    "event_type_counts": defaultdict(int),
                    "conversion_users": set(),
                }

            variant_stats[variant_name]["users"].add(user_id)

        # user_stats = {} # count of number of events by user

        for event in experiment_events_orm:
            user_id = event.user_id
            metric = event.type
            variant_id = user_to_variant_assignment.get(user_id).get("variant_id")
            variant_name = variant_id_to_variant_name.get(variant_id)

            variant_stats[variant_name]["event_type_counts"][metric] += 1

            if metric == primary_metric_name:
                variant_stats[variant_name]["conversion_users"].add(user_id)

        # clean up variant stats
        agg_variant_stats = {}
        for variant_name, stats in variant_stats.items():
            total_users = len(stats.get("users"))
            conversion_users = len(stats.get("conversion_users"))
            conversion_rate = conversion_users / total_users

            agg_variant_stats[variant_name] = {
                "total_users": total_users,
                "conversion_rate": conversion_rate,
                "event_counts": stats.get("event_type_counts"),
            }

        return agg_variant_stats

    def get_experiment_results(
        self, experiment_id: str, config: Optional[dict[str, str]] = None
    ):
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
        # Retrieve relevant data
        experiment_orm = self.experiment_repo.get_experiment_with_variants(
            experiment_id
        )
        variants_orm = experiment_orm.variants
        assignment_orm = self.assignment_repo.get_assignments_for_experiment(
            experiment_id
        )
        experiment_events_orm = self.event_repo.get_events_for_experiment(experiment_id)

        # lookup tables
        user_to_variant_assignment = {
            assignment.user_id: {
                "variant_id": assignment.variant_id,
                "assignment_timestamp": assignment.assignment_timestamp,
            }
            for assignment in assignment_orm
        }
        variant_id_to_variant_name = {
            variant.variant_id: variant.variant_name for variant in variants_orm
        }

        # filter out events based on user assignment timestamp
        filtered_events: list[EventORM] = self._filter_events(
            experiment_events_orm, user_to_variant_assignment
        )

        # global experiment stats
        days_running = (
            (experiment_orm.end_time - experiment_orm.start_time).days
            if experiment_orm.end_time and datetime.utcnow() > experiment_orm.end_time
            else (datetime.utcnow() - experiment_orm.start_time).days
        )
        global_conversion_rate = len(
            set(
                [
                    event.user_id
                    for event in filtered_events
                    if event.type == experiment_orm.primary_metric_name
                ]
            )
        ) / len(assignment_orm)

        variant_agg_stats = self._generate_variant_agg_stats(
            assignment_orm,
            experiment_events_orm,
            variant_id_to_variant_name,
            user_to_variant_assignment,
            experiment_orm.primary_metric_name,
        )

        result = {
            "name": experiment_orm.name,
            "description": experiment_orm.description,
            "start_time": experiment_orm.start_time,
            "end_time": experiment_orm.end_time,
            "experiment_days_running": days_running,
            "status": experiment_orm.status,
            "total_variants": len(variants_orm),
            "total_events": len(filtered_events),
            "primary_metric_name": experiment_orm.primary_metric_name,
            "total_users_in_experiment": len(assignment_orm),
            "global_conversion_rate": global_conversion_rate,
            # variant drill down stats
            "variant_stats": variant_agg_stats,
        }

        return result
