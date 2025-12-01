#!/usr/bin/env python3
"""FlowPath - Workflow documentation tool."""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from flowpath import __version__
from flowpath.screens.home import HomeScreen
from flowpath.screens.path_editor import PathEditorScreen
from flowpath.screens.step_creator import StepCreatorScreen
from flowpath.screens.path_reader import PathReaderScreen


class FlowPathWindow(QMainWindow):
    """Main application window."""

    # Screen indices
    HOME = 0
    EDITOR = 1
    STEP_CREATOR = 2
    READER = 3

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"FlowPath v{__version__}")
        self.setGeometry(100, 100, 1000, 700)

        # Stack to hold all screens
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Create screens
        self.home_screen = HomeScreen()
        self.path_editor_screen = PathEditorScreen()
        self.step_creator_screen = StepCreatorScreen()
        self.path_reader_screen = PathReaderScreen()

        # Add screens to stack
        self.stack.addWidget(self.home_screen)          # index 0
        self.stack.addWidget(self.path_editor_screen)   # index 1
        self.stack.addWidget(self.step_creator_screen)  # index 2
        self.stack.addWidget(self.path_reader_screen)   # index 3

        # Connect navigation signals
        self._connect_signals()

    def _connect_signals(self):
        """Connect all screen navigation signals."""

        # Home screen signals
        self.home_screen.new_path_requested.connect(self._on_new_path)
        self.home_screen.path_selected.connect(self._on_view_path)

        # Path editor signals
        self.path_editor_screen.save_completed.connect(self._on_editor_done)
        self.path_editor_screen.add_step_requested.connect(self._on_add_step)

        # Step creator signals
        self.step_creator_screen.save_and_continue.connect(self._on_step_saved_continue)
        self.step_creator_screen.save_and_done.connect(self._on_step_saved_done)

        # Path reader signals
        self.path_reader_screen.exit_requested.connect(self._on_reader_exit)
        self.path_reader_screen.edit_requested.connect(self._on_edit_path)

    # === Navigation handlers ===

    def _on_new_path(self):
        """Create a new path."""
        self.path_editor_screen.load_path(None)  # New path
        self.stack.setCurrentIndex(self.EDITOR)

    def _on_view_path(self, path_id: str):
        """View a path in the reader."""
        self.path_reader_screen.load_path(path_id)
        self.stack.setCurrentIndex(self.READER)

    def _on_edit_path(self, path_id: str):
        """Edit an existing path."""
        self.path_editor_screen.load_path(path_id)
        self.stack.setCurrentIndex(self.EDITOR)

    def _on_editor_done(self):
        """Return to home after editing."""
        self.home_screen.refresh()
        self.stack.setCurrentIndex(self.HOME)

    def _on_add_step(self):
        """Open step creator from editor."""
        self.step_creator_screen.clear_step()
        self.stack.setCurrentIndex(self.STEP_CREATOR)

    def _on_step_saved_continue(self, step):
        """Step saved, create another."""
        if step:
            self.path_editor_screen.add_step(step)
        # Stay on step creator (already cleared)

    def _on_step_saved_done(self, step):
        """Step saved (or cancelled), return to editor."""
        if step:
            self.path_editor_screen.add_step(step)
        self.stack.setCurrentIndex(self.EDITOR)

    def _on_reader_exit(self):
        """Return to home from reader."""
        self.home_screen.refresh()
        self.stack.setCurrentIndex(self.HOME)


def main():
    """Application entry point."""
    # Handle --version flag before creating QApplication
    if "--version" in sys.argv or "-v" in sys.argv:
        print(f"FlowPath v{__version__}")
        sys.exit(0)

    app = QApplication(sys.argv)

    # Set application-wide styling
    app.setStyle("Fusion")

    window = FlowPathWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
