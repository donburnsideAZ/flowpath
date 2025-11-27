import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from flowpath.database import init_database
from flowpath.screens.home import HomeScreen
from flowpath.screens.path_editor import PathEditorScreen
from flowpath.screens.step_creator import StepCreatorScreen
from flowpath.screens.path_reader import PathReaderScreen


class FlowPathWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FlowPath")
        self.setGeometry(100, 100, 1000, 700)

        # Initialize database
        init_database()

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

        # Home screen
        self.home_screen.new_path_btn.clicked.connect(self.new_path)
        self.home_screen.path_clicked.connect(self.view_path)

        # Path editor screen
        self.path_editor_screen.path_saved.connect(self.on_path_saved)
        self.path_editor_screen.cancelled.connect(self.show_home)
        self.path_editor_screen.add_step_requested.connect(self.show_step_creator)

        # Step creator screen
        self.step_creator_screen.step_saved.connect(self.on_step_saved)
        self.step_creator_screen.step_saved_add_another.connect(self.on_step_saved_add_another)
        self.step_creator_screen.cancelled.connect(self.show_path_editor)

        # Path reader screen
        self.path_reader_screen.edit_requested.connect(self.edit_path)
        self.path_reader_screen.exit_requested.connect(self.show_home)

        # Load initial data
        self.home_screen.refresh()

    def show_home(self):
        """Show home screen and refresh data."""
        self.home_screen.refresh()
        self.stack.setCurrentIndex(0)

    def new_path(self):
        """Create a new path."""
        self.path_editor_screen.new_path()
        self.stack.setCurrentIndex(1)

    def edit_path(self, path_id: int):
        """Edit an existing path."""
        self.path_editor_screen.load_path(path_id)
        self.stack.setCurrentIndex(1)

    def view_path(self, path_id: int):
        """View a path in read-only mode."""
        self.path_reader_screen.load_path(path_id)
        self.stack.setCurrentIndex(3)

    def show_path_editor(self):
        """Return to path editor."""
        self.stack.setCurrentIndex(1)

    def show_step_creator(self):
        """Show step creator for adding a new step."""
        self.step_creator_screen.new_step()
        self.stack.setCurrentIndex(2)

    def on_path_saved(self, path_id: int):
        """Handle path saved - return to home."""
        self.show_home()

    def on_step_saved(self, step):
        """Handle step saved - add to path editor and return."""
        self.path_editor_screen.add_step_from_creator(step)
        self.show_path_editor()

    def on_step_saved_add_another(self, step):
        """Handle step saved with add another - add to path editor, stay on creator."""
        self.path_editor_screen.add_step_from_creator(step)
        # Stay on step creator - it already called new_step()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FlowPathWindow()
    window.show()
    sys.exit(app.exec())
