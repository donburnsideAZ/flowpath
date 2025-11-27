"""JSON export/import functionality for team folder sharing."""

import json
import shutil
from datetime import datetime
from pathlib import Path as FilePath
from typing import Optional

from .models import Path, Step
from .database import get_database


class PathExporter:
    """Handles exporting and importing paths as JSON for team folders."""

    # JSON format version for compatibility checking
    FORMAT_VERSION = "1.0"

    @classmethod
    def export_path(cls, path: Path, output_dir: str, include_screenshots: bool = True) -> str:
        """Export a single path to a JSON file.

        Args:
            path: Path object to export.
            output_dir: Directory to export to.
            include_screenshots: Whether to copy screenshots to export folder.

        Returns:
            Path to the exported JSON file.
        """
        output_path = FilePath(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Create safe filename from title
        safe_title = cls._safe_filename(path.title)
        json_file = output_path / f"{safe_title}.json"

        # Prepare export data
        export_data = {
            "format_version": cls.FORMAT_VERSION,
            "exported_at": datetime.now().isoformat(),
            "path": path.to_dict()
        }

        # Handle screenshots if requested
        if include_screenshots and path.steps:
            screenshots_dir = output_path / f"{safe_title}_screenshots"
            screenshots_dir.mkdir(exist_ok=True)

            for step in path.steps:
                if step.screenshot_path:
                    src = FilePath(step.screenshot_path)
                    if src.exists():
                        dst = screenshots_dir / src.name
                        shutil.copy2(src, dst)
                        # Update path in export to relative path
                        step_dict = export_data["path"]["steps"][step.step_number - 1]
                        step_dict["screenshot_path"] = f"{safe_title}_screenshots/{src.name}"

        # Write JSON file
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return str(json_file)

    @classmethod
    def export_multiple_paths(cls, paths: list[Path], output_dir: str,
                               include_screenshots: bool = True) -> list[str]:
        """Export multiple paths to a folder.

        Args:
            paths: List of Path objects to export.
            output_dir: Directory to export to.
            include_screenshots: Whether to copy screenshots.

        Returns:
            List of exported JSON file paths.
        """
        exported_files = []
        for path in paths:
            file_path = cls.export_path(path, output_dir, include_screenshots)
            exported_files.append(file_path)
        return exported_files

    @classmethod
    def export_all_paths(cls, output_dir: str, include_screenshots: bool = True) -> list[str]:
        """Export all paths from the database.

        Args:
            output_dir: Directory to export to.
            include_screenshots: Whether to copy screenshots.

        Returns:
            List of exported JSON file paths.
        """
        db = get_database()
        paths = db.get_all_paths()

        # Load full path data with steps
        full_paths = []
        for path in paths:
            full_path = db.get_path(path.id)
            if full_path:
                full_paths.append(full_path)

        return cls.export_multiple_paths(full_paths, output_dir, include_screenshots)

    @classmethod
    def import_path(cls, json_file: str, base_dir: Optional[str] = None) -> Path:
        """Import a path from a JSON file.

        Args:
            json_file: Path to the JSON file.
            base_dir: Base directory for resolving relative screenshot paths.
                     Defaults to the directory containing the JSON file.

        Returns:
            Imported Path object (not yet saved to database).
        """
        json_path = FilePath(json_file)

        if base_dir is None:
            base_dir = str(json_path.parent)

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check format version
        format_version = data.get("format_version", "1.0")
        if format_version != cls.FORMAT_VERSION:
            # Future: handle version migrations
            pass

        # Create path from data
        path = Path.from_dict(data["path"])

        # Resolve relative screenshot paths
        for step in path.steps:
            if step.screenshot_path and not FilePath(step.screenshot_path).is_absolute():
                abs_path = FilePath(base_dir) / step.screenshot_path
                if abs_path.exists():
                    step.screenshot_path = str(abs_path)

        return path

    @classmethod
    def import_path_to_database(cls, json_file: str, base_dir: Optional[str] = None,
                                 copy_screenshots_to: Optional[str] = None) -> Path:
        """Import a path from JSON and save to database.

        Args:
            json_file: Path to the JSON file.
            base_dir: Base directory for resolving relative screenshot paths.
            copy_screenshots_to: If provided, copy screenshots to this directory
                                and update paths accordingly.

        Returns:
            Imported and saved Path object.
        """
        path = cls.import_path(json_file, base_dir)

        # Copy screenshots to local storage if requested
        if copy_screenshots_to:
            screenshots_dir = FilePath(copy_screenshots_to)
            screenshots_dir.mkdir(parents=True, exist_ok=True)

            for step in path.steps:
                if step.screenshot_path:
                    src = FilePath(step.screenshot_path)
                    if src.exists():
                        dst = screenshots_dir / src.name
                        shutil.copy2(src, dst)
                        step.screenshot_path = str(dst)

        # Save to database
        db = get_database()
        return db.create_path(path)

    @classmethod
    def import_folder(cls, folder_path: str, copy_screenshots_to: Optional[str] = None) -> list[Path]:
        """Import all JSON paths from a folder.

        Args:
            folder_path: Directory containing JSON files.
            copy_screenshots_to: Directory to copy screenshots to.

        Returns:
            List of imported Path objects.
        """
        folder = FilePath(folder_path)
        imported_paths = []

        for json_file in folder.glob("*.json"):
            try:
                path = cls.import_path_to_database(
                    str(json_file),
                    base_dir=str(folder),
                    copy_screenshots_to=copy_screenshots_to
                )
                imported_paths.append(path)
            except (json.JSONDecodeError, KeyError) as e:
                # Log error but continue with other files
                print(f"Error importing {json_file}: {e}")

        return imported_paths

    @classmethod
    def sync_from_team_folder(cls, team_folder: str,
                               local_screenshots_dir: Optional[str] = None) -> dict:
        """Sync paths from a team folder.

        This imports new paths and can update existing ones based on timestamps.

        Args:
            team_folder: Path to team folder.
            local_screenshots_dir: Local directory for screenshots.

        Returns:
            Dictionary with 'imported', 'updated', 'skipped' counts.
        """
        folder = FilePath(team_folder)
        db = get_database()

        result = {"imported": 0, "updated": 0, "skipped": 0, "errors": 0}

        # Get existing paths by title for comparison
        existing_paths = {p.title: p for p in db.get_all_paths()}

        for json_file in folder.glob("*.json"):
            try:
                # Read the JSON to check if we need to import/update
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                path_data = data.get("path", {})
                title = path_data.get("title", "")
                remote_updated = path_data.get("updated_at")

                if title in existing_paths:
                    existing = existing_paths[title]
                    # Compare timestamps to decide if update is needed
                    if remote_updated:
                        remote_dt = datetime.fromisoformat(remote_updated)
                        if existing.updated_at and remote_dt > existing.updated_at:
                            # Remote is newer, update local
                            imported_path = cls.import_path(str(json_file), str(folder))
                            imported_path.id = existing.id
                            db.update_path(imported_path)
                            result["updated"] += 1
                        else:
                            result["skipped"] += 1
                    else:
                        result["skipped"] += 1
                else:
                    # New path, import it
                    cls.import_path_to_database(
                        str(json_file),
                        base_dir=str(folder),
                        copy_screenshots_to=local_screenshots_dir
                    )
                    result["imported"] += 1

            except (json.JSONDecodeError, KeyError, Exception) as e:
                print(f"Error processing {json_file}: {e}")
                result["errors"] += 1

        return result

    @staticmethod
    def _safe_filename(title: str) -> str:
        """Convert title to a safe filename."""
        # Remove or replace unsafe characters
        safe = title.replace(" ", "_")
        safe = "".join(c for c in safe if c.isalnum() or c in "_-")
        return safe[:100] or "untitled"  # Limit length
