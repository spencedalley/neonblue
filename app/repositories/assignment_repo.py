# repositories/assignment_repo.py
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.orm.assignment import AssignmentORM  # Your previously defined ORM model
from typing import Optional
import uuid
from datetime import datetime


class AssignmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_assignment(
        self, experiment_id: str, user_id: str
    ) -> Optional[AssignmentORM]:
        """Retrieves a persistent assignment for a user in a specific experiment."""
        return (
            self.db.query(AssignmentORM)
            .filter(
                AssignmentORM.experiment_id == experiment_id,
                AssignmentORM.user_id == user_id,
            )
            .one_or_none()
        )

    def get_assignments_for_experiment(self, experiment_id: str) -> list[AssignmentORM]:
        """Retrieves a persistent assignment for a user in a specific experiment."""
        stmt = select(AssignmentORM).where(AssignmentORM.experiment_id == experiment_id)

        return self.db.scalars(stmt).all()

    def create_assignment(
        self, experiment_id: str, user_id: str, variant_id: str
    ) -> AssignmentORM:
        """
        Creates a new assignment record.
        Note: The ExperimentService must ensure this isn't a duplicate.
        """
        try:
            db_assignment = AssignmentORM(
                experiment_id=experiment_id,
                user_id=user_id,
                variant_id=variant_id,
                assignment_timestamp=datetime.utcnow(),
            )

            self.db.add(db_assignment)
            self.db.commit()
            self.db.refresh(db_assignment)

            return db_assignment

        except IntegrityError:
            # Should not happen if the service checks first, but good for safety
            self.db.rollback()
            raise ValueError("Assignment already exists for this user and experiment.")
        except Exception as e:
            self.db.rollback()
            print(f"Exception occurred creating assignment: {e}")
            raise RuntimeError("Exception occurred during assignment creation")
