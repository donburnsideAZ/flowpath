"""Data persistence layer for FlowPath application."""

import json
import os
from pathlib import Path as FilePath
from typing import Optional
from .models import Path, Step


class DataStore:
    """Handles saving and loading paths to/from JSON files."""

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            # Default to ~/.flowpath/data
            self.data_dir = FilePath.home() / ".flowpath" / "data"
        else:
            self.data_dir = FilePath(data_dir)

        self.paths_file = self.data_dir / "paths.json"
        self.screenshots_dir = self.data_dir / "screenshots"

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self):
        """Create data directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    def save_paths(self, paths: list[Path]) -> bool:
        """Save all paths to the JSON file."""
        try:
            data = {
                "version": "1.0",
                "paths": [p.to_dict() for p in paths]
            }
            with open(self.paths_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving paths: {e}")
            return False

    def load_paths(self) -> list[Path]:
        """Load all paths from the JSON file."""
        if not self.paths_file.exists():
            return self._create_sample_paths()

        try:
            with open(self.paths_file, 'r') as f:
                data = json.load(f)
            return [Path.from_dict(p) for p in data.get("paths", [])]
        except Exception as e:
            print(f"Error loading paths: {e}")
            return []

    def save_path(self, path: Path) -> bool:
        """Save or update a single path."""
        paths = self.load_paths()

        # Find existing path by ID and update, or append new
        found = False
        for i, p in enumerate(paths):
            if p.path_id == path.path_id:
                paths[i] = path
                found = True
                break

        if not found:
            paths.append(path)

        return self.save_paths(paths)

    def delete_path(self, path_id: str) -> bool:
        """Delete a path by ID."""
        paths = self.load_paths()
        paths = [p for p in paths if p.path_id != path_id]
        return self.save_paths(paths)

    def get_path(self, path_id: str) -> Optional[Path]:
        """Get a single path by ID."""
        paths = self.load_paths()
        for p in paths:
            if p.path_id == path_id:
                return p
        return None

    def get_screenshot_path(self, filename: str) -> str:
        """Get the full path for a screenshot file."""
        return str(self.screenshots_dir / filename)

    def get_categories(self) -> list[str]:
        """Get all unique categories from stored paths."""
        paths = self.load_paths()
        categories = set()
        for p in paths:
            if p.category:
                categories.add(p.category)
        return sorted(list(categories))

    def get_all_tags(self) -> list[str]:
        """Get all unique tags from stored paths."""
        paths = self.load_paths()
        tags = set()
        for p in paths:
            for tag in p.tags:
                tags.add(tag)
        return sorted(list(tags))

    def search_paths(self, query: str, category: Optional[str] = None,
                     tag: Optional[str] = None) -> list[Path]:
        """Search paths by query string, category, and/or tag."""
        paths = self.load_paths()
        results = []

        query = query.lower().strip()

        for p in paths:
            # Category filter
            if category and p.category != category:
                continue

            # Tag filter
            if tag and tag not in p.tags:
                continue

            # Text search (if query provided)
            if query:
                searchable = f"{p.title} {p.description} {' '.join(p.tags)}".lower()
                if query not in searchable:
                    continue

            results.append(p)

        return results

    def _create_sample_paths(self) -> list[Path]:
        """Create sample paths for initial data."""
        sample_paths = [
            Path(
                title="How to Reset Password",
                category="LMS",
                tags=["authentication", "troubleshooting"],
                description="Step-by-step guide for resetting user passwords.",
                is_creator=True,
                steps=[
                    Step(instructions="Navigate to the login page and click on the 'Forgot Password' link below the password field."),
                    Step(instructions="Enter your email address in the form and click 'Submit'. Check your inbox for the reset link."),
                    Step(instructions="Click the reset link in your email. You'll be taken to a page where you can enter a new password."),
                    Step(instructions="Enter your new password twice to confirm, then click 'Reset Password'. You can now log in."),
                ]
            ),
            Path(
                title="Creating Video Content",
                category="Content Creation",
                tags=["video", "setup"],
                description="How to create and upload video content.",
                is_creator=True,
                steps=[
                    Step(instructions="Open the content creation dashboard and select 'New Video'."),
                    Step(instructions="Upload your video file or record directly using the built-in recorder."),
                    Step(instructions="Add title, description, and tags for your video."),
                    Step(instructions="Click 'Publish' to make the video available."),
                ]
            ),
            Path(
                title="Admin Panel Overview",
                category="Admin",
                tags=["setup", "admin"],
                description="Overview of the admin panel features.",
                is_creator=False,
                steps=[
                    Step(instructions="Access the admin panel from the main menu."),
                    Step(instructions="Review the dashboard for key metrics."),
                    Step(instructions="Navigate through the settings sections."),
                ]
            ),
            Path(
                title="Troubleshooting Login Issues",
                category="Troubleshooting",
                tags=["authentication", "troubleshooting"],
                description="Common login issues and their solutions.",
                is_creator=True,
                steps=[
                    Step(instructions="Check if the user's account is active."),
                    Step(instructions="Verify the email address is correct."),
                    Step(instructions="Reset the password if needed."),
                    Step(instructions="Check for browser cache issues."),
                ]
            ),
            Path(
                title="Upload Course Materials",
                category="LMS",
                tags=["content", "upload"],
                description="How to upload course materials to the LMS.",
                is_creator=False,
                steps=[
                    Step(instructions="Navigate to the course management section."),
                    Step(instructions="Select the course to add materials to."),
                    Step(instructions="Click 'Add Materials' and select your files."),
                ]
            ),
            Path(
                title="Export Reports",
                category="Admin",
                tags=["reports", "export"],
                description="How to export various reports from the system.",
                is_creator=True,
                steps=[
                    Step(instructions="Go to the Reports section in the admin panel."),
                    Step(instructions="Select the report type and date range."),
                    Step(instructions="Click 'Export' and choose your format (PDF, CSV, Excel)."),
                ]
            ),
        ]

        # Save the sample paths
        self.save_paths(sample_paths)
        return sample_paths
