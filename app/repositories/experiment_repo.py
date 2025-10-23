import uuid
import json
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.models.orm.event import (
    EventORM,
)  # Import the ORM model from the file we created
from app.models.orm.experiment import ExperimentORM, VariantORM, ExperimentStatus
from app.models.schemas.experiment import ExperimentCreateModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


class ExperimentRepository:
    def __init__(self, db: Session):
        """Initializes the repository with a database session."""
        self.db = db

    def create_experiment(
        self, experiment_data: ExperimentCreateModel
    ) -> ExperimentORM:
        """
        Creates a new event record in the database.

        Args:
            event_data: The Pydantic model containing event details.
            experiment_id: The ID of the experiment the user is currently in (set by service).

        Returns:
            The created EventORM object.


        Experiments will have variantconfigs attached to them, variant configs can be parsed and then a variant can be created
        alongside the experiment
        """

        # --- 1. Validate total allocation (Business Rule) ---
        total_allocation = sum(
            v.traffic_allocation_percent for v in experiment_data.variants
        )
        if total_allocation != 100.0:
            # Raise an appropriate error for the service layer to catch
            raise ValueError(
                f"Total traffic allocation must be 100%. Got: {total_allocation}%"
            )

            # --- 2. Begin Transaction and Provision Data ---
        try:
            # Use the session's transaction context manager for safety (commit on success, rollback on error)
            # The 'with' statement is the preferred way to manage transactions safely.
            with self.db.begin():

                # Generate a unique ID for the new experiment
                experiment_id = str(uuid.uuid4())

                # --- a) Create the Experiment (Parent) Record ---
                experiment_data_dict = experiment_data.model_dump(
                    exclude={"variants"}, exclude_unset=True
                )

                # Set ORM-specific fields and defaults
                experiment_data_dict["experiment_id"] = experiment_id

                db_experiment = ExperimentORM(**experiment_data_dict)
                self.db.add(db_experiment)

                # --- b) Create the Variants (Children) Records ---
                for variant_data in experiment_data.variants:

                    # 1. Prepare Variant Data
                    variant_dict = variant_data.model_dump(exclude_unset=True)

                    # 2. Assign Foreign Key and Primary Key
                    variant_dict["variant_id"] = str(uuid.uuid4())
                    variant_dict["experiment_id"] = (
                        experiment_id  # ⬅️ Link to the parent
                    )

                    # 3. Handle the JSON field serialization
                    if variant_dict.get("configuration_json") is not None:
                        # Ensures the Dict is converted to JSON string if the ORM uses Text/String
                        # If using native JSON/JSONB type, this step might be optional/handled by SQLAlchemy
                        variant_dict["configuration_json"] = json.dumps(
                            variant_dict["configuration_json"]
                        )

                    # 4. Create and Add ORM Instance
                    db_variant = VariantORM(**variant_dict)
                    self.db.add(db_variant)

            # The transaction commits automatically here due to the 'with self.db.begin():' block

            # Since we used ORM objects, we can now refresh the parent object to load the variants
            # (Requires the relationship to be defined on the ORM models)
            self.db.refresh(db_experiment)

            return db_experiment

        except IntegrityError as e:
            # Handle unique constraint violations (e.g., experiment name already exists)
            # The rollback is handled by the 'with' block exiting due to the exception
            raise ValueError(f"Database integrity error (e.g., duplicate name): {e}")

        except SQLAlchemyError as e:
            # Catch all other DB errors
            raise RuntimeError(
                f"A database error occurred during experiment creation: {e}"
            )

        except Exception:
            # The 'with' block handles rollback for any exception
            raise

    def get_experiment_with_variants(self, experiment_id: str) -> ExperimentORM | None:
        """
        Fetches a single Experiment by experiment_id and eagerly loads all
        associated VariantORM objects in a single query.
        """

        # 1. Start the select statement for the Experiment model
        stmt = select(ExperimentORM).where(ExperimentORM.experiment_id == experiment_id)

        # 2. Use joinedload() to fetch the 'variants' relationship (defined in ExperimentORM)
        #    This prevents the N+1 query problem.
        stmt = stmt.options(joinedload(ExperimentORM.variants))

        # 3. Execute the query
        result = self.db.scalars(stmt).unique().one_or_none()

        return result
