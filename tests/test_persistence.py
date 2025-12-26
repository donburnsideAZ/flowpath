"""
Tests for the FlowPath persistence layer.

Run with: python -m pytest tests/test_persistence.py -v
Or simply: python tests/test_persistence.py
"""

import os
import sys
import tempfile
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flowpath.models import Path, Step
from flowpath.data import Database, PathRepository, StepRepository


class TestDatabase(unittest.TestCase):
    """Test the Database class."""

    def setUp(self):
        """Create a temporary database for testing."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_file.close()
        self.db = Database(self.temp_file.name)
        self.db.initialize()

    def tearDown(self):
        """Clean up the temporary database."""
        os.unlink(self.temp_file.name)

    def test_database_creation(self):
        """Test that the database file is created."""
        self.assertTrue(os.path.exists(self.temp_file.name))
        self.assertTrue(self.db.exists)

    def test_tables_created(self):
        """Test that tables are created correctly."""
        with self.db.connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]
            self.assertIn('paths', tables)
            self.assertIn('steps', tables)


class TestPathModel(unittest.TestCase):
    """Test the Path model."""

    def test_path_creation(self):
        """Test creating a Path object."""
        path = Path(title="Test Path", category="LMS")
        self.assertEqual(path.title, "Test Path")
        self.assertEqual(path.category, "LMS")
        self.assertIsNotNone(path.created_at)
        self.assertIsNotNone(path.updated_at)

    def test_tag_list(self):
        """Test tag parsing."""
        path = Path(title="Test", tags="auth, video, setup")
        self.assertEqual(path.tag_list, ['auth', 'video', 'setup'])

    def test_add_remove_tag(self):
        """Test adding and removing tags."""
        path = Path(title="Test", tags="tag1")
        path.add_tag("tag2")
        self.assertEqual(path.tag_list, ['tag1', 'tag2'])
        path.remove_tag("tag1")
        self.assertEqual(path.tag_list, ['tag2'])

    def test_to_dict_from_dict(self):
        """Test serialization and deserialization."""
        path = Path(title="Test", category="Admin", tags="test")
        data = path.to_dict()
        restored = Path.from_dict(data)
        self.assertEqual(restored.title, path.title)
        self.assertEqual(restored.category, path.category)
        self.assertEqual(restored.tags, path.tags)


class TestStepModel(unittest.TestCase):
    """Test the Step model."""

    def test_step_creation(self):
        """Test creating a Step object."""
        step = Step(path_id=1, step_number=1, instructions="Click button")
        self.assertEqual(step.path_id, 1)
        self.assertEqual(step.step_number, 1)
        self.assertEqual(step.instructions, "Click button")
        self.assertIsNotNone(step.created_at)

    def test_to_dict_from_dict(self):
        """Test serialization and deserialization."""
        step = Step(path_id=1, step_number=2, instructions="Test")
        data = step.to_dict()
        restored = Step.from_dict(data)
        self.assertEqual(restored.path_id, step.path_id)
        self.assertEqual(restored.step_number, step.step_number)
        self.assertEqual(restored.instructions, step.instructions)


class TestPathRepository(unittest.TestCase):
    """Test the PathRepository class."""

    def setUp(self):
        """Create a temporary database for testing."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_file.close()
        self.db = Database(self.temp_file.name)
        self.db.initialize()
        self.repo = PathRepository(self.db)

    def tearDown(self):
        """Clean up the temporary database."""
        os.unlink(self.temp_file.name)

    def test_create_path(self):
        """Test creating a path."""
        path = Path(title="Test Path", category="LMS", creator="user1")
        path_id = self.repo.create(path)
        self.assertIsNotNone(path_id)
        self.assertGreater(path_id, 0)

    def test_get_by_id(self):
        """Test retrieving a path by ID."""
        path = Path(title="Test Path", category="Admin")
        path_id = self.repo.create(path)

        retrieved = self.repo.get_by_id(path_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.title, "Test Path")
        self.assertEqual(retrieved.category, "Admin")

    def test_get_all(self):
        """Test retrieving all paths."""
        self.repo.create(Path(title="Path 1"))
        self.repo.create(Path(title="Path 2"))
        self.repo.create(Path(title="Path 3"))

        paths = self.repo.get_all()
        self.assertEqual(len(paths), 3)

    def test_get_by_category(self):
        """Test filtering by category."""
        self.repo.create(Path(title="Path 1", category="LMS"))
        self.repo.create(Path(title="Path 2", category="Admin"))
        self.repo.create(Path(title="Path 3", category="LMS"))

        lms_paths = self.repo.get_by_category("LMS")
        self.assertEqual(len(lms_paths), 2)

    def test_search(self):
        """Test searching paths."""
        self.repo.create(Path(title="Password Reset Guide"))
        self.repo.create(Path(title="User Setup", description="How to reset account"))
        self.repo.create(Path(title="Other Guide"))

        results = self.repo.search("reset")
        self.assertEqual(len(results), 2)

    def test_update_path(self):
        """Test updating a path."""
        path = Path(title="Original Title")
        path_id = self.repo.create(path)

        path.title = "Updated Title"
        self.repo.update(path)

        retrieved = self.repo.get_by_id(path_id)
        self.assertEqual(retrieved.title, "Updated Title")

    def test_delete_path(self):
        """Test deleting a path."""
        path = Path(title="To Delete")
        path_id = self.repo.create(path)

        self.assertTrue(self.repo.delete(path_id))
        self.assertIsNone(self.repo.get_by_id(path_id))

    def test_get_categories(self):
        """Test getting all unique categories."""
        self.repo.create(Path(title="P1", category="LMS"))
        self.repo.create(Path(title="P2", category="Admin"))
        self.repo.create(Path(title="P3", category="LMS"))

        categories = self.repo.get_categories()
        self.assertEqual(sorted(categories), ['Admin', 'LMS'])

    def test_get_all_tags(self):
        """Test getting all unique tags."""
        self.repo.create(Path(title="P1", tags="auth, video"))
        self.repo.create(Path(title="P2", tags="setup, auth"))

        tags = self.repo.get_all_tags()
        self.assertEqual(sorted(tags), ['auth', 'setup', 'video'])


class TestStepRepository(unittest.TestCase):
    """Test the StepRepository class."""

    def setUp(self):
        """Create a temporary database for testing."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_file.close()
        self.db = Database(self.temp_file.name)
        self.db.initialize()
        self.path_repo = PathRepository(self.db)
        self.step_repo = StepRepository(self.db)

        # Create a test path
        self.test_path = Path(title="Test Path")
        self.path_id = self.path_repo.create(self.test_path)

    def tearDown(self):
        """Clean up the temporary database."""
        os.unlink(self.temp_file.name)

    def test_create_step(self):
        """Test creating a step."""
        step = Step(path_id=self.path_id, step_number=1, instructions="Step 1")
        step_id = self.step_repo.create(step)
        self.assertIsNotNone(step_id)
        self.assertGreater(step_id, 0)

    def test_get_by_id(self):
        """Test retrieving a step by ID."""
        step = Step(path_id=self.path_id, step_number=1, instructions="Test step")
        step_id = self.step_repo.create(step)

        retrieved = self.step_repo.get_by_id(step_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.instructions, "Test step")

    def test_get_by_path_id(self):
        """Test retrieving all steps for a path."""
        self.step_repo.create(Step(path_id=self.path_id, step_number=1, instructions="Step 1"))
        self.step_repo.create(Step(path_id=self.path_id, step_number=2, instructions="Step 2"))
        self.step_repo.create(Step(path_id=self.path_id, step_number=3, instructions="Step 3"))

        steps = self.step_repo.get_by_path_id(self.path_id)
        self.assertEqual(len(steps), 3)
        self.assertEqual(steps[0].step_number, 1)
        self.assertEqual(steps[2].step_number, 3)

    def test_get_next_step_number(self):
        """Test getting the next step number."""
        self.assertEqual(self.step_repo.get_next_step_number(self.path_id), 1)

        self.step_repo.create(Step(path_id=self.path_id, step_number=1))
        self.assertEqual(self.step_repo.get_next_step_number(self.path_id), 2)

        self.step_repo.create(Step(path_id=self.path_id, step_number=2))
        self.assertEqual(self.step_repo.get_next_step_number(self.path_id), 3)

    def test_update_step(self):
        """Test updating a step."""
        step = Step(path_id=self.path_id, step_number=1, instructions="Original")
        step_id = self.step_repo.create(step)

        step.instructions = "Updated"
        self.step_repo.update(step)

        retrieved = self.step_repo.get_by_id(step_id)
        self.assertEqual(retrieved.instructions, "Updated")

    def test_delete_step(self):
        """Test deleting a step."""
        step = Step(path_id=self.path_id, step_number=1)
        step_id = self.step_repo.create(step)

        self.assertTrue(self.step_repo.delete(step_id))
        self.assertIsNone(self.step_repo.get_by_id(step_id))

    def test_cascade_delete(self):
        """Test that deleting a path cascades to steps."""
        self.step_repo.create(Step(path_id=self.path_id, step_number=1))
        self.step_repo.create(Step(path_id=self.path_id, step_number=2))

        # Delete the path
        self.path_repo.delete(self.path_id)

        # Steps should be gone
        steps = self.step_repo.get_by_path_id(self.path_id)
        self.assertEqual(len(steps), 0)

    def test_create_bulk(self):
        """Test creating multiple steps at once."""
        steps = [
            Step(path_id=self.path_id, step_number=1, instructions="Step 1"),
            Step(path_id=self.path_id, step_number=2, instructions="Step 2"),
            Step(path_id=self.path_id, step_number=3, instructions="Step 3"),
        ]
        ids = self.step_repo.create_bulk(steps)
        self.assertEqual(len(ids), 3)

        all_steps = self.step_repo.get_by_path_id(self.path_id)
        self.assertEqual(len(all_steps), 3)


if __name__ == '__main__':
    print("Running FlowPath Persistence Layer Tests...")
    print("=" * 60)
    unittest.main(verbosity=2)
