import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from flowpath.screens.home import HomeScreen
from flowpath.screens.path_editor import PathEditorScreen
from flowpath.screens.step_creator import StepCreatorScreen
from flowpath.screens.path_reader import PathReaderScreen
from flowpath.services import DataService


class FlowPathWindow(QMainWindow):
    """Main application window for FlowPath."""

    # Screen indices
    HOME = 0
    PATH_EDITOR = 1
    STEP_CREATOR = 2
    PATH_READER = 3

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FlowPath")
        self.setGeometry(100, 100, 1000, 700)

        # Initialize data service (singleton)
        self.data_service = DataService.instance()

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
        self._connect_home_screen()
        self._connect_path_editor_screen()
        self._connect_step_creator_screen()
        self._connect_path_reader_screen()

    def _connect_home_screen(self):
        """Connect Home screen signals."""
        # New Path button -> Path Editor (new mode)
        self.home_screen.new_path_btn.clicked.connect(self._on_new_path)

        # Path card clicked -> Path Reader
        self.home_screen.path_clicked.connect(self._on_view_path)

        # Edit button on path card -> Path Editor (edit mode)
        self.home_screen.edit_path_clicked.connect(self._on_edit_path)

    def _connect_path_editor_screen(self):
        """Connect Path Editor screen signals."""
        # Save & Done -> Home (after saving)
        self.path_editor_screen.path_saved.connect(self._on_path_saved)

        # Cancel -> Home
        self.path_editor_screen.cancelled.connect(self._show_home)

        # Add Step -> Step Creator
        self.path_editor_screen.add_step_requested.connect(self._on_add_step)

    def _connect_step_creator_screen(self):
        """Connect Step Creator screen signals."""
        # Step saved -> Add to Path Editor
        self.step_creator_screen.step_saved.connect(self._on_step_saved)

        # Done -> Back to Path Editor
        self.step_creator_screen.done_clicked.connect(self._show_path_editor)

        # Cancel -> Back to Path Editor
        self.step_creator_screen.cancelled.connect(self._show_path_editor)

    def _connect_path_reader_screen(self):
        """Connect Path Reader screen signals."""
        # Exit -> Home
        self.path_reader_screen.exit_clicked.connect(self._on_exit_reader)

        # Edit -> Path Editor (edit mode)
        self.path_reader_screen.edit_clicked.connect(self._on_edit_path)

    # ==================== Navigation Methods ====================

    def _show_home(self):
        """Show the Home screen."""
        self.home_screen.refresh()
        self.stack.setCurrentIndex(self.HOME)

    def _show_path_editor(self):
        """Show the Path Editor screen."""
        self.stack.setCurrentIndex(self.PATH_EDITOR)

    def _show_step_creator(self):
        """Show the Step Creator screen."""
        self.stack.setCurrentIndex(self.STEP_CREATOR)

    def _show_path_reader(self):
        """Show the Path Reader screen."""
        self.stack.setCurrentIndex(self.PATH_READER)

    # ==================== Event Handlers ====================

    def _on_new_path(self):
        """Handle New Path button click."""
        self.path_editor_screen.new_path()
        self._show_path_editor()

    def _on_view_path(self, path_id: int):
        """Handle path card click to view a path."""
        self.path_reader_screen.load_path(path_id)
        self._show_path_reader()

    def _on_edit_path(self, path_id: int):
        """Handle edit button click to edit a path."""
        self.path_editor_screen.load_path(path_id)
        self._show_path_editor()

    def _on_path_saved(self, path_id: int):
        """Handle path saved event."""
        self._show_home()

    def _on_add_step(self):
        """Handle Add Step button click in Path Editor."""
        # Calculate the next step number
        next_step_num = len(self.path_editor_screen.step_cards) + 1
        self.step_creator_screen.set_step_number(next_step_num)
        self.step_creator_screen.clear_step()
        self._show_step_creator()

    def _on_step_saved(self, step):
        """Handle step saved from Step Creator."""
        self.path_editor_screen.add_pending_step(step)

    def _on_exit_reader(self):
        """Handle Exit button click in Path Reader."""
        self._show_home()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FlowPathWindow()
    window.show()
    sys.exit(app.exec())
