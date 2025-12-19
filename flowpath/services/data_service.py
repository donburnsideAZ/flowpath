"""
DataService for FlowPath application.

Provides a centralized, singleton-style access point for all data operations.
This is the primary interface that UI components use to interact with the database.
"""

import os
from pathlib import Path as FilePath
from typing import List, Optional, Tuple
from ..models import Path, Step, LegacyDocument, LEGACY_EXTENSIONS
from ..data import Database, PathRepository, StepRepository


class DataService:
    """
    Centralized data service for the FlowPath application.

    This service provides a clean API for all data operations and manages
    the database connection and repositories.

    Usage:
        # Get the singleton instance
        service = DataService.instance()

        # Create a new path
        path = Path(title="My Guide", category="LMS")
        path_id = service.create_path(path)

        # Add steps
        step = Step(path_id=path_id, step_number=1, instructions="Click here")
        service.create_step(step)

        # Retrieve paths
        all_paths = service.get_all_paths()
        path = service.get_path_with_steps(path_id)
    """

    _instance: Optional['DataService'] = None

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the data service.

        Args:
            db_path: Optional path to the database file.
                     If None, uses the default location.
        """
        self.db = Database(db_path)
        self.db.initialize()
        self._path_repo = PathRepository(self.db)
        self._step_repo = StepRepository(self.db)
        self._team_folder: Optional[str] = None

    @property
    def team_folder(self) -> Optional[str]:
        """Get the current team folder path."""
        return self._team_folder
    
    @team_folder.setter
    def team_folder(self, path: Optional[str]) -> None:
        """Set the team folder path."""
        self._team_folder = path

    @classmethod
    def instance(cls, db_path: Optional[str] = None) -> 'DataService':
        """
        Get the singleton instance of the DataService.

        Args:
            db_path: Optional path to database (only used on first call)

        Returns:
            The DataService singleton instance
        """
        if cls._instance is None:
            cls._instance = cls(db_path)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None

    # ==================== Path Operations ====================

    def create_path(self, path: Path) -> int:
        """
        Create a new path.

        Args:
            path: Path object to create

        Returns:
            The ID of the created path
        """
        return self._path_repo.create(path)

    def get_path(self, path_id: int) -> Optional[Path]:
        """
        Get a path by its ID.

        Args:
            path_id: The ID of the path

        Returns:
            Path object if found, None otherwise
        """
        return self._path_repo.get_by_id(path_id)

    def get_path_with_steps(self, path_id: int) -> Optional[Tuple[Path, List[Step]]]:
        """
        Get a path along with all its steps.

        Args:
            path_id: The ID of the path

        Returns:
            Tuple of (Path, List[Step]) if found, None otherwise
        """
        path = self._path_repo.get_by_id(path_id)
        if path is None:
            return None
        steps = self._step_repo.get_by_path_id(path_id)
        return (path, steps)

    def get_all_paths(self) -> List[Path]:
        """
        Get all paths, ordered by most recently updated.

        Returns:
            List of all Path objects
        """
        return self._path_repo.get_all()

    def get_paths_by_category(self, category: str) -> List[Path]:
        """
        Get paths filtered by category.

        Args:
            category: Category to filter by

        Returns:
            List of Path objects in the category
        """
        return self._path_repo.get_by_category(category)

    def get_paths_by_tag(self, tag: str) -> List[Path]:
        """
        Get paths containing a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            List of Path objects with the tag
        """
        return self._path_repo.get_by_tag(tag)

    def search_paths(self, query: str) -> List[Path]:
        """
        Search paths by title, description, or tags.

        Args:
            query: Search query

        Returns:
            List of matching Path objects
        """
        return self._path_repo.search(query)

    def update_path(self, path: Path) -> bool:
        """
        Update an existing path.

        Args:
            path: Path object with updated values

        Returns:
            True if update was successful
        """
        return self._path_repo.update(path)

    def delete_path(self, path_id: int) -> bool:
        """
        Delete a path and all its steps.

        Args:
            path_id: ID of the path to delete

        Returns:
            True if deletion was successful
        """
        return self._path_repo.delete(path_id)

    def get_categories(self) -> List[str]:
        """
        Get all unique categories.

        Returns:
            List of category names
        """
        return self._path_repo.get_categories()

    def get_all_tags(self) -> List[str]:
        """
        Get all unique tags across all paths.

        Returns:
            List of tag names
        """
        return self._path_repo.get_all_tags()

    def count_paths(self) -> int:
        """
        Get the total number of paths.

        Returns:
            Number of paths
        """
        return self._path_repo.count()

    # ==================== Step Operations ====================

    def create_step(self, step: Step) -> int:
        """
        Create a new step.

        Args:
            step: Step object to create

        Returns:
            The ID of the created step
        """
        return self._step_repo.create(step)

    def get_step(self, step_id: int) -> Optional[Step]:
        """
        Get a step by its ID.

        Args:
            step_id: The ID of the step

        Returns:
            Step object if found, None otherwise
        """
        return self._step_repo.get_by_id(step_id)

    def get_steps_for_path(self, path_id: int) -> List[Step]:
        """
        Get all steps for a path, ordered by step number.

        Args:
            path_id: The ID of the path

        Returns:
            List of Step objects
        """
        return self._step_repo.get_by_path_id(path_id)

    def update_step(self, step: Step) -> bool:
        """
        Update an existing step.

        Args:
            step: Step object with updated values

        Returns:
            True if update was successful
        """
        return self._step_repo.update(step)

    def delete_step(self, step_id: int) -> bool:
        """
        Delete a step.

        Args:
            step_id: ID of the step to delete

        Returns:
            True if deletion was successful
        """
        return self._step_repo.delete(step_id)

    def get_next_step_number(self, path_id: int) -> int:
        """
        Get the next available step number for a path.

        Args:
            path_id: ID of the path

        Returns:
            Next step number
        """
        return self._step_repo.get_next_step_number(path_id)

    def count_steps(self, path_id: int) -> int:
        """
        Get the number of steps in a path.

        Args:
            path_id: ID of the path

        Returns:
            Number of steps
        """
        return self._step_repo.count_by_path_id(path_id)

    # ==================== Convenience Methods ====================

    def save_path_with_steps(self, path: Path, steps: List[Step]) -> int:
        """
        Save a path along with all its steps in a single operation.

        If the path already exists (has an ID), it will be updated.
        Steps are replaced entirely with the new list.

        Args:
            path: Path object to save
            steps: List of Step objects for the path

        Returns:
            The ID of the saved path
        """
        if path.id is None:
            # New path
            path_id = self.create_path(path)
        else:
            # Existing path - update it
            self.update_path(path)
            path_id = path.id
            # Delete existing steps
            self._step_repo.delete_by_path_id(path_id)

        # Create new steps
        for i, step in enumerate(steps, start=1):
            step.path_id = path_id
            step.step_number = i
            self.create_step(step)

        return path_id

    def duplicate_path(self, path_id: int, new_title: Optional[str] = None) -> Optional[int]:
        """
        Duplicate a path and all its steps.

        Args:
            path_id: ID of the path to duplicate
            new_title: Optional new title (defaults to "Copy of <original>")

        Returns:
            ID of the new path, or None if original not found
        """
        result = self.get_path_with_steps(path_id)
        if result is None:
            return None

        original_path, original_steps = result

        # Create new path
        new_path = Path(
            title=new_title or f"Copy of {original_path.title}",
            category=original_path.category,
            tags=original_path.tags,
            description=original_path.description,
            creator=original_path.creator,
        )
        new_path_id = self.create_path(new_path)

        # Duplicate steps
        for step in original_steps:
            new_step = Step(
                path_id=new_path_id,
                step_number=step.step_number,
                instructions=step.instructions,
                screenshot_path=step.screenshot_path,
            )
            self.create_step(new_step)

        return new_path_id

    # ==================== Legacy Document Operations ====================

    def get_legacy_documents(self) -> List[LegacyDocument]:
        """
        Scan the team folder for legacy documents.
        
        Returns:
            List of LegacyDocument objects found in the team folder
        """
        if not self._team_folder or not os.path.isdir(self._team_folder):
            return []
        
        legacy_docs = []
        team_path = FilePath(self._team_folder)
        
        # Scan for legacy files (not in paths/ subdirectory, not .md files)
        for item in team_path.iterdir():
            if item.is_file():
                # Skip markdown files (those are FlowPath paths)
                if item.suffix.lower() == '.md':
                    continue
                # Skip hidden files
                if item.name.startswith('.'):
                    continue
                # Skip JSON config files
                if item.suffix.lower() == '.json':
                    continue
                    
                doc = LegacyDocument.from_path(str(item))
                if doc:
                    legacy_docs.append(doc)
        
        # Sort by modified date, newest first
        legacy_docs.sort(key=lambda d: d.modified_at, reverse=True)
        return legacy_docs

    def search_legacy_documents(self, query: str) -> List[LegacyDocument]:
        """
        Search legacy documents by filename.
        
        Args:
            query: Search string to match against filenames
            
        Returns:
            List of matching LegacyDocument objects
        """
        query_lower = query.lower()
        all_docs = self.get_legacy_documents()
        return [doc for doc in all_docs if query_lower in doc.filename.lower()]

    def get_legacy_documents_by_type(self, file_type: str) -> List[LegacyDocument]:
        """
        Get legacy documents filtered by type.

        Args:
            file_type: Type to filter by (word, pdf, powerpoint, etc.)

        Returns:
            List of LegacyDocument objects of the specified type
        """
        all_docs = self.get_legacy_documents()
        return [doc for doc in all_docs if doc.file_type == file_type]

    # ==================== Admin: Category Management ====================

    def get_managed_categories(self) -> List[dict]:
        """
        Get all admin-managed categories.

        Returns:
            List of category dicts with id, name, color, sort_order
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "SELECT id, name, color, sort_order FROM categories ORDER BY sort_order, name"
            )
            return [dict(row) for row in cursor.fetchall()]

    def add_category(self, name: str, color: str = "#666666") -> int:
        """
        Add a new category.

        Args:
            name: Category name
            color: Hex color code for the category

        Returns:
            ID of the created category
        """
        with self.db.connection() as conn:
            # Get max sort_order
            cursor = conn.execute("SELECT MAX(sort_order) FROM categories")
            max_order = cursor.fetchone()[0] or 0

            cursor = conn.execute(
                "INSERT INTO categories (name, color, sort_order) VALUES (?, ?, ?)",
                (name.strip(), color, max_order + 1)
            )
            return cursor.lastrowid

    def update_category(self, category_id: int, name: str, color: str) -> bool:
        """
        Update an existing category.

        Args:
            category_id: ID of the category to update
            name: New name
            color: New color

        Returns:
            True if update was successful
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "UPDATE categories SET name = ?, color = ? WHERE id = ?",
                (name.strip(), color, category_id)
            )
            return cursor.rowcount > 0

    def delete_category(self, category_id: int) -> bool:
        """
        Delete a category.

        Args:
            category_id: ID of the category to delete

        Returns:
            True if deletion was successful
        """
        with self.db.connection() as conn:
            cursor = conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            return cursor.rowcount > 0

    def reorder_categories(self, category_ids: List[int]) -> None:
        """
        Reorder categories based on the provided ID list.

        Args:
            category_ids: List of category IDs in desired order
        """
        with self.db.connection() as conn:
            for order, cat_id in enumerate(category_ids):
                conn.execute(
                    "UPDATE categories SET sort_order = ? WHERE id = ?",
                    (order, cat_id)
                )

    # ==================== Admin: Tag Management ====================

    def get_managed_tags(self) -> List[dict]:
        """
        Get all admin-managed tags.

        Returns:
            List of tag dicts with id and name
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "SELECT id, name FROM tags ORDER BY name"
            )
            return [dict(row) for row in cursor.fetchall()]

    def add_tag(self, name: str) -> int:
        """
        Add a new tag.

        Args:
            name: Tag name

        Returns:
            ID of the created tag
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "INSERT INTO tags (name) VALUES (?)",
                (name.strip(),)
            )
            return cursor.lastrowid

    def delete_tag(self, tag_id: int) -> bool:
        """
        Delete a tag.

        Args:
            tag_id: ID of the tag to delete

        Returns:
            True if deletion was successful
        """
        with self.db.connection() as conn:
            cursor = conn.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
            return cursor.rowcount > 0

    def rename_tag(self, tag_id: int, new_name: str) -> bool:
        """
        Rename a tag.

        Args:
            tag_id: ID of the tag to rename
            new_name: New name for the tag

        Returns:
            True if rename was successful
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "UPDATE tags SET name = ? WHERE id = ?",
                (new_name.strip(), tag_id)
            )
            return cursor.rowcount > 0

    def get_category_usage_count(self, category_name: str) -> int:
        """
        Get the number of paths using a category.

        Args:
            category_name: Name of the category

        Returns:
            Number of paths using this category
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM paths WHERE category = ?",
                (category_name,)
            )
            return cursor.fetchone()[0]

    def get_tag_usage_count(self, tag_name: str) -> int:
        """
        Get the number of paths using a tag.

        Args:
            tag_name: Name of the tag

        Returns:
            Number of paths using this tag
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM paths WHERE tags LIKE ?",
                (f"%{tag_name}%",)
            )
            return cursor.fetchone()[0]
