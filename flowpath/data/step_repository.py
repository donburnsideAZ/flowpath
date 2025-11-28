"""
Step Repository for FlowPath application.

Provides CRUD operations for Step entities.
"""

from typing import List, Optional
from datetime import datetime

from .database import Database
from ..models import Step


class StepRepository:
    """
    Repository for managing Step entities in the database.

    Usage:
        db = Database()
        db.initialize()
        repo = StepRepository(db)

        # Create
        step = Step(path_id=1, step_number=1, instructions="Click the button")
        step_id = repo.create(step)

        # Read
        step = repo.get_by_id(step_id)
        path_steps = repo.get_by_path_id(1)

        # Update
        step.instructions = "Updated instructions"
        repo.update(step)

        # Delete
        repo.delete(step_id)
    """

    def __init__(self, database: Database):
        """
        Initialize the repository.

        Args:
            database: Database instance for connections
        """
        self.db = database

    def create(self, step: Step) -> int:
        """
        Create a new step in the database.

        Args:
            step: Step object to create

        Returns:
            int: The ID of the newly created step
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO steps (path_id, step_number, instructions, screenshot_path, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    step.path_id,
                    step.step_number,
                    step.instructions,
                    step.screenshot_path,
                    step.created_at,
                    step.updated_at,
                )
            )
            step.id = cursor.lastrowid
            return step.id

    def get_by_id(self, step_id: int) -> Optional[Step]:
        """
        Get a step by its ID.

        Args:
            step_id: The ID of the step to retrieve

        Returns:
            Step object if found, None otherwise
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM steps WHERE id = ?",
                (step_id,)
            )
            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_step(row)

    def get_by_path_id(self, path_id: int) -> List[Step]:
        """
        Get all steps for a specific path, ordered by step number.

        Args:
            path_id: The ID of the path

        Returns:
            List of Step objects for the path
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM steps WHERE path_id = ? ORDER BY step_number",
                (path_id,)
            )
            return [self._row_to_step(row) for row in cursor.fetchall()]

    def get_step_at_position(self, path_id: int, step_number: int) -> Optional[Step]:
        """
        Get a specific step by its position in the path.

        Args:
            path_id: The ID of the path
            step_number: The step number (1-indexed)

        Returns:
            Step object if found, None otherwise
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM steps WHERE path_id = ? AND step_number = ?",
                (path_id, step_number)
            )
            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_step(row)

    def update(self, step: Step) -> bool:
        """
        Update an existing step.

        Args:
            step: Step object with updated values

        Returns:
            True if update was successful, False if step not found
        """
        if step.id is None:
            raise ValueError("Cannot update step without an ID")

        step.updated_at = datetime.now()

        with self.db.connection() as conn:
            cursor = conn.execute(
                """
                UPDATE steps
                SET step_number = ?, instructions = ?, screenshot_path = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    step.step_number,
                    step.instructions,
                    step.screenshot_path,
                    step.updated_at,
                    step.id,
                )
            )
            return cursor.rowcount > 0

    def delete(self, step_id: int) -> bool:
        """
        Delete a step by its ID.

        Args:
            step_id: ID of the step to delete

        Returns:
            True if deletion was successful, False if step not found
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "DELETE FROM steps WHERE id = ?",
                (step_id,)
            )
            return cursor.rowcount > 0

    def delete_by_path_id(self, path_id: int) -> int:
        """
        Delete all steps for a specific path.

        Args:
            path_id: ID of the path whose steps should be deleted

        Returns:
            Number of steps deleted
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "DELETE FROM steps WHERE path_id = ?",
                (path_id,)
            )
            return cursor.rowcount

    def count_by_path_id(self, path_id: int) -> int:
        """
        Get the number of steps in a path.

        Args:
            path_id: ID of the path

        Returns:
            Number of steps in the path
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM steps WHERE path_id = ?",
                (path_id,)
            )
            return cursor.fetchone()[0]

    def get_next_step_number(self, path_id: int) -> int:
        """
        Get the next available step number for a path.

        Args:
            path_id: ID of the path

        Returns:
            Next step number (current max + 1, or 1 if no steps exist)
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "SELECT MAX(step_number) FROM steps WHERE path_id = ?",
                (path_id,)
            )
            max_num = cursor.fetchone()[0]
            return (max_num or 0) + 1

    def reorder_steps(self, path_id: int, step_ids: List[int]) -> bool:
        """
        Reorder steps in a path based on a list of step IDs.

        Args:
            path_id: ID of the path
            step_ids: List of step IDs in desired order

        Returns:
            True if reorder was successful
        """
        with self.db.connection() as conn:
            for index, step_id in enumerate(step_ids, start=1):
                conn.execute(
                    """
                    UPDATE steps
                    SET step_number = ?, updated_at = ?
                    WHERE id = ? AND path_id = ?
                    """,
                    (index, datetime.now(), step_id, path_id)
                )
            return True

    def move_step(self, step_id: int, new_position: int) -> bool:
        """
        Move a step to a new position within its path.

        Args:
            step_id: ID of the step to move
            new_position: New step number (1-indexed)

        Returns:
            True if move was successful
        """
        step = self.get_by_id(step_id)
        if step is None:
            return False

        path_id = step.path_id
        old_position = step.step_number

        if old_position == new_position:
            return True

        with self.db.connection() as conn:
            if new_position > old_position:
                # Moving down: shift steps up
                conn.execute(
                    """
                    UPDATE steps
                    SET step_number = step_number - 1, updated_at = ?
                    WHERE path_id = ? AND step_number > ? AND step_number <= ?
                    """,
                    (datetime.now(), path_id, old_position, new_position)
                )
            else:
                # Moving up: shift steps down
                conn.execute(
                    """
                    UPDATE steps
                    SET step_number = step_number + 1, updated_at = ?
                    WHERE path_id = ? AND step_number >= ? AND step_number < ?
                    """,
                    (datetime.now(), path_id, new_position, old_position)
                )

            # Update the moved step
            conn.execute(
                """
                UPDATE steps
                SET step_number = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_position, datetime.now(), step_id)
            )

        return True

    def create_bulk(self, steps: List[Step]) -> List[int]:
        """
        Create multiple steps at once.

        Args:
            steps: List of Step objects to create

        Returns:
            List of created step IDs
        """
        ids = []
        with self.db.connection() as conn:
            for step in steps:
                cursor = conn.execute(
                    """
                    INSERT INTO steps (path_id, step_number, instructions, screenshot_path, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        step.path_id,
                        step.step_number,
                        step.instructions,
                        step.screenshot_path,
                        step.created_at,
                        step.updated_at,
                    )
                )
                step.id = cursor.lastrowid
                ids.append(step.id)
        return ids

    def _row_to_step(self, row) -> Step:
        """Convert a database row to a Step object."""
        return Step(
            id=row['id'],
            path_id=row['path_id'],
            step_number=row['step_number'],
            instructions=row['instructions'],
            screenshot_path=row['screenshot_path'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )
