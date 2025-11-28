"""
Path Repository for FlowPath application.

Provides CRUD operations for Path entities.
"""

from typing import List, Optional
from datetime import datetime

from .database import Database
from ..models import Path


class PathRepository:
    """
    Repository for managing Path entities in the database.

    Usage:
        db = Database()
        db.initialize()
        repo = PathRepository(db)

        # Create
        path = Path(title="My Guide", category="LMS")
        path_id = repo.create(path)

        # Read
        path = repo.get_by_id(path_id)
        all_paths = repo.get_all()

        # Update
        path.title = "Updated Title"
        repo.update(path)

        # Delete
        repo.delete(path_id)
    """

    def __init__(self, database: Database):
        """
        Initialize the repository.

        Args:
            database: Database instance for connections
        """
        self.db = database

    def create(self, path: Path) -> int:
        """
        Create a new path in the database.

        Args:
            path: Path object to create

        Returns:
            int: The ID of the newly created path
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO paths (title, category, tags, description, creator, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    path.title,
                    path.category,
                    path.tags,
                    path.description,
                    path.creator,
                    path.created_at,
                    path.updated_at,
                )
            )
            path.id = cursor.lastrowid
            return path.id

    def get_by_id(self, path_id: int) -> Optional[Path]:
        """
        Get a path by its ID.

        Args:
            path_id: The ID of the path to retrieve

        Returns:
            Path object if found, None otherwise
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM paths WHERE id = ?",
                (path_id,)
            )
            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_path(row)

    def get_all(self, order_by: str = "updated_at DESC") -> List[Path]:
        """
        Get all paths from the database.

        Args:
            order_by: SQL ORDER BY clause (default: most recently updated first)

        Returns:
            List of Path objects
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM paths ORDER BY {order_by}"
            )
            return [self._row_to_path(row) for row in cursor.fetchall()]

    def get_by_category(self, category: str) -> List[Path]:
        """
        Get all paths in a specific category.

        Args:
            category: Category name to filter by

        Returns:
            List of Path objects in the category
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM paths WHERE category = ? ORDER BY updated_at DESC",
                (category,)
            )
            return [self._row_to_path(row) for row in cursor.fetchall()]

    def get_by_creator(self, creator: str) -> List[Path]:
        """
        Get all paths by a specific creator.

        Args:
            creator: Creator name to filter by

        Returns:
            List of Path objects by the creator
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM paths WHERE creator = ? ORDER BY updated_at DESC",
                (creator,)
            )
            return [self._row_to_path(row) for row in cursor.fetchall()]

    def search(self, query: str) -> List[Path]:
        """
        Search paths by title, description, or tags.

        Args:
            query: Search query string

        Returns:
            List of Path objects matching the query
        """
        search_pattern = f"%{query}%"
        with self.db.connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM paths
                WHERE title LIKE ? OR description LIKE ? OR tags LIKE ?
                ORDER BY updated_at DESC
                """,
                (search_pattern, search_pattern, search_pattern)
            )
            return [self._row_to_path(row) for row in cursor.fetchall()]

    def get_by_tag(self, tag: str) -> List[Path]:
        """
        Get all paths containing a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            List of Path objects with the tag
        """
        # Search for tag with various possible formats
        with self.db.connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM paths
                WHERE tags LIKE ? OR tags LIKE ? OR tags LIKE ? OR tags = ?
                ORDER BY updated_at DESC
                """,
                (
                    f"%{tag},%",      # tag at start or middle
                    f"%, {tag},%",    # tag in middle with space
                    f"%, {tag}",      # tag at end with space
                    tag               # exact match (single tag)
                )
            )
            return [self._row_to_path(row) for row in cursor.fetchall()]

    def update(self, path: Path) -> bool:
        """
        Update an existing path.

        Args:
            path: Path object with updated values

        Returns:
            True if update was successful, False if path not found
        """
        if path.id is None:
            raise ValueError("Cannot update path without an ID")

        path.updated_at = datetime.now()

        with self.db.connection() as conn:
            cursor = conn.execute(
                """
                UPDATE paths
                SET title = ?, category = ?, tags = ?, description = ?,
                    creator = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    path.title,
                    path.category,
                    path.tags,
                    path.description,
                    path.creator,
                    path.updated_at,
                    path.id,
                )
            )
            return cursor.rowcount > 0

    def delete(self, path_id: int) -> bool:
        """
        Delete a path by its ID.

        Note: This will also delete all associated steps due to CASCADE.

        Args:
            path_id: ID of the path to delete

        Returns:
            True if deletion was successful, False if path not found
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "DELETE FROM paths WHERE id = ?",
                (path_id,)
            )
            return cursor.rowcount > 0

    def get_categories(self) -> List[str]:
        """
        Get a list of all unique categories.

        Returns:
            List of category names
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "SELECT DISTINCT category FROM paths WHERE category != '' ORDER BY category"
            )
            return [row[0] for row in cursor.fetchall()]

    def get_all_tags(self) -> List[str]:
        """
        Get a list of all unique tags across all paths.

        Returns:
            List of unique tag names
        """
        with self.db.connection() as conn:
            cursor = conn.execute("SELECT tags FROM paths WHERE tags != ''")
            all_tags = set()
            for row in cursor.fetchall():
                tags = row[0].split(',')
                for tag in tags:
                    tag = tag.strip()
                    if tag:
                        all_tags.add(tag)
            return sorted(list(all_tags))

    def count(self) -> int:
        """
        Get the total number of paths.

        Returns:
            Number of paths in the database
        """
        with self.db.connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM paths")
            return cursor.fetchone()[0]

    def _row_to_path(self, row) -> Path:
        """Convert a database row to a Path object."""
        return Path(
            id=row['id'],
            title=row['title'],
            category=row['category'],
            tags=row['tags'],
            description=row['description'],
            creator=row['creator'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )
