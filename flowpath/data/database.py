"""
Database module for FlowPath application.

Provides SQLite database initialization and connection management.
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional
from contextlib import contextmanager


class Database:
    """
    Manages SQLite database connections and schema initialization.

    Usage:
        db = Database()  # Uses default location
        db.initialize()  # Create tables if needed

        with db.connection() as conn:
            cursor = conn.execute("SELECT * FROM paths")
    """

    DEFAULT_DB_NAME = "flowpath.db"

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file.
                     If None, uses the default location in user's data directory.
        """
        if db_path is None:
            db_path = self._get_default_db_path()

        self.db_path = db_path
        self._ensure_directory_exists()

    def _get_default_db_path(self) -> str:
        """Get the default database path based on the platform."""
        # Use XDG_DATA_HOME on Linux, fallback to ~/.local/share
        if os.name == 'posix':
            data_home = os.environ.get('XDG_DATA_HOME',
                                       os.path.expanduser('~/.local/share'))
        else:
            # Windows: use APPDATA
            data_home = os.environ.get('APPDATA',
                                       os.path.expanduser('~'))

        app_dir = os.path.join(data_home, 'flowpath')
        return os.path.join(app_dir, self.DEFAULT_DB_NAME)

    def _ensure_directory_exists(self) -> None:
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    @contextmanager
    def connection(self):
        """
        Context manager for database connections.

        Yields:
            sqlite3.Connection: Active database connection

        Example:
            with db.connection() as conn:
                conn.execute("INSERT INTO paths ...")
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like row access
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key support
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        """
        Initialize the database schema.

        Creates all tables if they don't exist.
        """
        with self.connection() as conn:
            self._create_paths_table(conn)
            self._create_steps_table(conn)
            self._create_categories_table(conn)
            self._create_tags_table(conn)
            self._create_indexes(conn)

    def _create_paths_table(self, conn: sqlite3.Connection) -> None:
        """Create the paths table."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS paths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT DEFAULT '',
                tags TEXT DEFAULT '',
                description TEXT DEFAULT '',
                creator TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def _create_steps_table(self, conn: sqlite3.Connection) -> None:
        """Create the steps table."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path_id INTEGER NOT NULL,
                step_number INTEGER NOT NULL,
                instructions TEXT DEFAULT '',
                screenshot_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (path_id) REFERENCES paths(id) ON DELETE CASCADE
            )
        """)

    def _create_categories_table(self, conn: sqlite3.Connection) -> None:
        """Create the categories table for admin-managed categories."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT '#666666',
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def _create_tags_table(self, conn: sqlite3.Connection) -> None:
        """Create the tags table for admin-managed tags."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def _create_indexes(self, conn: sqlite3.Connection) -> None:
        """Create database indexes for performance."""
        # Index for finding steps by path
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_steps_path_id
            ON steps(path_id)
        """)

        # Index for ordering steps
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_steps_path_step
            ON steps(path_id, step_number)
        """)

        # Index for category filtering
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_paths_category
            ON paths(category)
        """)

    def reset(self) -> None:
        """
        Reset the database by dropping all tables and recreating them.

        WARNING: This will delete all data!
        """
        with self.connection() as conn:
            conn.execute("DROP TABLE IF EXISTS steps")
            conn.execute("DROP TABLE IF EXISTS paths")

        self.initialize()

    def backup(self, backup_path: str) -> None:
        """
        Create a backup of the database.

        Args:
            backup_path: Path where the backup will be saved
        """
        import shutil
        shutil.copy2(self.db_path, backup_path)

    @property
    def exists(self) -> bool:
        """Check if the database file exists."""
        return os.path.exists(self.db_path)

    def __repr__(self) -> str:
        return f"Database(path='{self.db_path}')"
