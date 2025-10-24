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

        total_allocation = sum(
            v.traffic_allocation_percent for v in experiment_data.variants
        )
        if total_allocation != 100.0:

            raise ValueError(
                f"Total traffic allocation must be 100%. Got: {total_allocation}%"
            )

        try:

            with self.db.begin():

                experiment_id = str(uuid.uuid4())

                experiment_data_dict = experiment_data.model_dump(
                    exclude={"variants"}, exclude_unset=True
                )

                experiment_data_dict["experiment_id"] = experiment_id

                db_experiment = ExperimentORM(**experiment_data_dict)
                self.db.add(db_experiment)

                for variant_data in experiment_data.variants:

                    variant_dict = variant_data.model_dump(exclude_unset=True)

                    variant_dict["variant_id"] = str(uuid.uuid4())
                    variant_dict["experiment_id"] = (
                        experiment_id  # ⬅️ Link to the parent
                    )

                    if variant_dict.get("configuration_json") is not None:
                        variant_dict["configuration_json"] = json.dumps(
                            variant_dict["configuration_json"]
                        )

                    db_variant = VariantORM(**variant_dict)
                    self.db.add(db_variant)

            self.db.refresh(db_experiment)

            return db_experiment

        except IntegrityError as e:
            raise ValueError(f"Database integrity error (e.g., duplicate name): {e}")

        except SQLAlchemyError as e:
            raise RuntimeError(
                f"A database error occurred during experiment creation: {e}"
            )

        except Exception:
            raise

    def get_experiment_with_variants(self, experiment_id: str) -> ExperimentORM | None:
        """
        Fetches a single Experiment by experiment_id and eagerly loads all
        associated VariantORM objects in a single query.
        """
        stmt = select(ExperimentORM).where(ExperimentORM.experiment_id == experiment_id)

        # 2. Use joinedload() to fetch the 'variants' relationship (defined in ExperimentORM). This prevents the N+1 query problem.
        stmt = stmt.options(joinedload(ExperimentORM.variants))

        result = self.db.scalars(stmt).unique().one_or_none()

        return result
