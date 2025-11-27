"""SQLite database layer for FlowPath application."""

import sqlite3
from datetime import datetime
from pathlib import Path as FilePath
from typing import Optional

from .models import Path, Step


class Database:
    """SQLite database manager for FlowPath."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file. Defaults to user data directory.
        """
        if db_path is None:
            # Default to user's home directory
            data_dir = FilePath.home() / ".flowpath"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "flowpath.db")

        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create paths table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT DEFAULT '',
                tags TEXT DEFAULT '',
                description TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create steps table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path_id INTEGER NOT NULL,
                step_number INTEGER NOT NULL,
                screenshot_path TEXT,
                instructions TEXT DEFAULT '',
                FOREIGN KEY (path_id) REFERENCES paths(id) ON DELETE CASCADE
            )
        """)

        # Create index for faster step lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_steps_path_id ON steps(path_id)
        """)

        conn.commit()
        conn.close()

    # ==================== PATH OPERATIONS ====================

    def create_path(self, path: Path) -> Path:
        """Create a new path in the database.

        Args:
            path: Path object to create.

        Returns:
            Path with assigned ID.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now()
        cursor.execute("""
            INSERT INTO paths (title, category, tags, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (path.title, path.category, path.tags, path.description, now, now))

        path.id = cursor.lastrowid
        path.created_at = now
        path.updated_at = now

        # Save steps if any
        for i, step in enumerate(path.steps):
            step.path_id = path.id
            step.step_number = i + 1
            self._create_step(cursor, step)

        conn.commit()
        conn.close()

        return path

    def get_path(self, path_id: int) -> Optional[Path]:
        """Get a path by ID.

        Args:
            path_id: ID of the path to retrieve.

        Returns:
            Path object or None if not found.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM paths WHERE id = ?", (path_id,))
        row = cursor.fetchone()

        if row is None:
            conn.close()
            return None

        path = self._row_to_path(row)
        path.steps = self._get_steps_for_path(cursor, path_id)

        conn.close()
        return path

    def get_all_paths(self) -> list[Path]:
        """Get all paths (without steps for performance).

        Returns:
            List of all paths.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM paths ORDER BY updated_at DESC")
        rows = cursor.fetchall()

        paths = [self._row_to_path(row) for row in rows]

        conn.close()
        return paths

    def get_paths_by_category(self, category: str) -> list[Path]:
        """Get paths filtered by category.

        Args:
            category: Category to filter by.

        Returns:
            List of matching paths.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM paths WHERE category = ? ORDER BY updated_at DESC",
            (category,)
        )
        rows = cursor.fetchall()

        paths = [self._row_to_path(row) for row in rows]

        conn.close()
        return paths

    def search_paths(self, query: str) -> list[Path]:
        """Search paths by title, tags, or description.

        Args:
            query: Search query string.

        Returns:
            List of matching paths.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        search_term = f"%{query}%"
        cursor.execute("""
            SELECT * FROM paths
            WHERE title LIKE ? OR tags LIKE ? OR description LIKE ?
            ORDER BY updated_at DESC
        """, (search_term, search_term, search_term))
        rows = cursor.fetchall()

        paths = [self._row_to_path(row) for row in rows]

        conn.close()
        return paths

    def update_path(self, path: Path) -> Path:
        """Update an existing path.

        Args:
            path: Path object with updated data.

        Returns:
            Updated path.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now()
        cursor.execute("""
            UPDATE paths
            SET title = ?, category = ?, tags = ?, description = ?, updated_at = ?
            WHERE id = ?
        """, (path.title, path.category, path.tags, path.description, now, path.id))

        path.updated_at = now

        # Update steps: delete existing and recreate
        cursor.execute("DELETE FROM steps WHERE path_id = ?", (path.id,))
        for i, step in enumerate(path.steps):
            step.path_id = path.id
            step.step_number = i + 1
            self._create_step(cursor, step)

        conn.commit()
        conn.close()

        return path

    def delete_path(self, path_id: int) -> bool:
        """Delete a path and its steps.

        Args:
            path_id: ID of the path to delete.

        Returns:
            True if deleted, False if not found.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Delete steps first (cascade would handle this, but being explicit)
        cursor.execute("DELETE FROM steps WHERE path_id = ?", (path_id,))
        cursor.execute("DELETE FROM paths WHERE id = ?", (path_id,))

        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted

    # ==================== STEP OPERATIONS ====================

    def _create_step(self, cursor: sqlite3.Cursor, step: Step) -> Step:
        """Create a step (internal, uses existing cursor)."""
        cursor.execute("""
            INSERT INTO steps (path_id, step_number, screenshot_path, instructions)
            VALUES (?, ?, ?, ?)
        """, (step.path_id, step.step_number, step.screenshot_path, step.instructions))

        step.id = cursor.lastrowid
        return step

    def _get_steps_for_path(self, cursor: sqlite3.Cursor, path_id: int) -> list[Step]:
        """Get all steps for a path (internal, uses existing cursor)."""
        cursor.execute(
            "SELECT * FROM steps WHERE path_id = ? ORDER BY step_number",
            (path_id,)
        )
        rows = cursor.fetchall()

        return [self._row_to_step(row) for row in rows]

    # ==================== CATEGORY OPERATIONS ====================

    def get_all_categories(self) -> list[str]:
        """Get all unique categories.

        Returns:
            List of category names.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT category FROM paths
            WHERE category != ''
            ORDER BY category
        """)
        rows = cursor.fetchall()

        categories = [row["category"] for row in rows]

        conn.close()
        return categories

    def get_all_tags(self) -> list[str]:
        """Get all unique tags across all paths.

        Returns:
            List of unique tags.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT tags FROM paths WHERE tags != ''")
        rows = cursor.fetchall()

        all_tags = set()
        for row in rows:
            tags = row["tags"].split(",")
            for tag in tags:
                tag = tag.strip()
                if tag:
                    all_tags.add(tag)

        conn.close()
        return sorted(list(all_tags))

    # ==================== HELPER METHODS ====================

    def _row_to_path(self, row: sqlite3.Row) -> Path:
        """Convert a database row to a Path object."""
        created_at = row["created_at"]
        updated_at = row["updated_at"]

        # Handle datetime parsing
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return Path(
            id=row["id"],
            title=row["title"],
            category=row["category"],
            tags=row["tags"],
            description=row["description"],
            created_at=created_at,
            updated_at=updated_at
        )

    def _row_to_step(self, row: sqlite3.Row) -> Step:
        """Convert a database row to a Step object."""
        return Step(
            id=row["id"],
            path_id=row["path_id"],
            step_number=row["step_number"],
            screenshot_path=row["screenshot_path"],
            instructions=row["instructions"]
        )


# Global database instance
_db: Optional[Database] = None


def get_database() -> Database:
    """Get the global database instance."""
    global _db
    if _db is None:
        _db = Database()
    return _db


def init_database(db_path: Optional[str] = None) -> Database:
    """Initialize the database with a custom path.

    Args:
        db_path: Optional custom database path.

    Returns:
        Database instance.
    """
    global _db
    _db = Database(db_path)
    return _db
