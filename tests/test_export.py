"""
Tests for the FlowPath export functionality.

Run with: python -m pytest tests/test_export.py -v
Or simply: python tests/test_export.py
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flowpath.models import Path, Step
from flowpath.services.export_service import ExportService, _markdown_to_html


class TestMarkdownToHtml(unittest.TestCase):
    """Test markdown to HTML conversion."""

    def test_empty_string(self):
        """Test empty string returns empty."""
        self.assertEqual(_markdown_to_html(""), "")

    def test_plain_text(self):
        """Test plain text is preserved."""
        result = _markdown_to_html("Hello world")
        self.assertIn("Hello world", result)

    def test_bold_asterisks(self):
        """Test bold with asterisks."""
        result = _markdown_to_html("This is **bold** text")
        self.assertIn("<strong>bold</strong>", result)

    def test_bold_underscores(self):
        """Test bold with underscores."""
        result = _markdown_to_html("This is __bold__ text")
        self.assertIn("<strong>bold</strong>", result)

    def test_italic_asterisks(self):
        """Test italic with asterisks."""
        result = _markdown_to_html("This is *italic* text")
        self.assertIn("<em>italic</em>", result)

    def test_links(self):
        """Test link conversion."""
        result = _markdown_to_html("Click [here](https://example.com)")
        self.assertIn('<a href="https://example.com">here</a>', result)

    def test_line_breaks(self):
        """Test line break conversion."""
        result = _markdown_to_html("Line 1\nLine 2")
        self.assertIn("<br>", result)

    def test_html_escaping(self):
        """Test HTML special characters are escaped."""
        result = _markdown_to_html("Use <tag> & 'quotes'")
        self.assertIn("&lt;tag&gt;", result)
        self.assertIn("&amp;", result)


class TestExportJson(unittest.TestCase):
    """Test JSON export functionality."""

    def setUp(self):
        """Create test data."""
        self.path = Path(
            id=1,
            title="Test Path",
            category="Testing",
            tags="test, unit",
            description="A test path for unit testing",
            creator="TestUser",
            created_at=datetime(2024, 1, 15, 10, 30),
            updated_at=datetime(2024, 1, 15, 11, 45)
        )
        self.steps = [
            Step(
                id=1,
                path_id=1,
                step_number=1,
                instructions="First step instructions",
                screenshot_path=None
            ),
            Step(
                id=2,
                path_id=1,
                step_number=2,
                instructions="Second step with **bold** text",
                screenshot_path=None
            )
        ]
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_json_export_creates_file(self):
        """Test that JSON export creates a file."""
        output_path = os.path.join(self.temp_dir, "test.json")
        result = ExportService.export_json(
            self.path, self.steps, output_path, embed_images=False
        )
        self.assertTrue(result)
        self.assertTrue(os.path.exists(output_path))

    def test_json_export_content(self):
        """Test that JSON export contains correct data."""
        output_path = os.path.join(self.temp_dir, "test.json")
        ExportService.export_json(
            self.path, self.steps, output_path, embed_images=False
        )

        with open(output_path, 'r') as f:
            data = json.load(f)

        self.assertEqual(data['version'], '1.0')
        self.assertIn('exported_at', data)
        self.assertEqual(data['path']['title'], 'Test Path')
        self.assertEqual(data['path']['category'], 'Testing')
        self.assertEqual(len(data['steps']), 2)
        self.assertEqual(data['steps'][0]['instructions'], 'First step instructions')

    def test_json_export_timestamps(self):
        """Test that timestamps are serialized correctly."""
        output_path = os.path.join(self.temp_dir, "test.json")
        ExportService.export_json(
            self.path, self.steps, output_path, embed_images=False
        )

        with open(output_path, 'r') as f:
            data = json.load(f)

        self.assertIn('2024-01-15', data['path']['created_at'])


class TestExportHtml(unittest.TestCase):
    """Test HTML export functionality."""

    def setUp(self):
        """Create test data."""
        self.path = Path(
            id=1,
            title="Test Path",
            category="Testing",
            tags="test, unit",
            description="A **bold** description",
            creator="TestUser",
            created_at=datetime(2024, 1, 15, 10, 30),
            updated_at=datetime(2024, 1, 15, 11, 45)
        )
        self.steps = [
            Step(
                id=1,
                path_id=1,
                step_number=1,
                instructions="Step with *italic* text",
                screenshot_path=None
            )
        ]
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_html_export_creates_file(self):
        """Test that HTML export creates a file."""
        output_path = os.path.join(self.temp_dir, "test.html")
        result = ExportService.export_html(self.path, self.steps, output_path)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(output_path))

    def test_html_export_content(self):
        """Test that HTML export contains correct elements."""
        output_path = os.path.join(self.temp_dir, "test.html")
        ExportService.export_html(self.path, self.steps, output_path)

        with open(output_path, 'r') as f:
            html = f.read()

        # Check basic structure
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('<title>Test Path</title>', html)
        self.assertIn('<h1>Test Path</h1>', html)

        # Check metadata
        self.assertIn('Testing', html)  # category
        self.assertIn('TestUser', html)  # creator

        # Check tags are rendered
        self.assertIn('test', html)
        self.assertIn('unit', html)

        # Check markdown is converted
        self.assertIn('<strong>bold</strong>', html)  # in description
        self.assertIn('<em>italic</em>', html)  # in step instructions

        # Check step is present
        self.assertIn('Step 1', html)

    def test_html_export_is_valid_html5(self):
        """Test that HTML export produces valid HTML5."""
        output_path = os.path.join(self.temp_dir, "test.html")
        ExportService.export_html(self.path, self.steps, output_path)

        with open(output_path, 'r') as f:
            html = f.read()

        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('<html lang="en">', html)
        self.assertIn('<meta charset="UTF-8">', html)
        self.assertIn('</html>', html)

    def test_html_export_has_print_styles(self):
        """Test that HTML export includes print media query."""
        output_path = os.path.join(self.temp_dir, "test.html")
        ExportService.export_html(self.path, self.steps, output_path)

        with open(output_path, 'r') as f:
            html = f.read()

        self.assertIn('@media print', html)


class TestSuggestedFilename(unittest.TestCase):
    """Test filename suggestion."""

    def test_basic_title(self):
        """Test basic title conversion."""
        path = Path(title="My Test Path")
        filename = ExportService.get_suggested_filename(path, 'html')
        self.assertEqual(filename, 'My-Test-Path.html')

    def test_special_characters(self):
        """Test special characters are removed."""
        path = Path(title="Path: Test (v2)")
        filename = ExportService.get_suggested_filename(path, 'json')
        self.assertNotIn(':', filename)
        self.assertNotIn('(', filename)
        self.assertTrue(filename.endswith('.json'))

    def test_empty_title(self):
        """Test empty title fallback."""
        path = Path(title="")
        filename = ExportService.get_suggested_filename(path, 'pdf')
        self.assertEqual(filename, 'flowpath-export.pdf')

    def test_whitespace_normalization(self):
        """Test multiple spaces are normalized."""
        path = Path(title="Multiple   Spaces   Here")
        filename = ExportService.get_suggested_filename(path, 'html')
        self.assertNotIn('  ', filename)  # No double spaces


if __name__ == '__main__':
    unittest.main()
