import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, 
    QMenuBar, QMenu, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QPalette, QColor, QAction
from PyQt6.QtCore import Qt, QSettings

from flowpath.screens.home import HomeScreen
from flowpath.screens.path_editor import PathEditorScreen
from flowpath.screens.step_creator import StepCreatorScreen
from flowpath.screens.path_reader import PathReaderScreen
from flowpath.screens.admin import AdminScreen
from flowpath.services import DataService

__version__ = "0.5"


class FlowPathWindow(QMainWindow):
    """Main application window for FlowPath."""

    # Screen indices
    HOME = 0
    PATH_EDITOR = 1
    STEP_CREATOR = 2
    PATH_READER = 3
    ADMIN = 4

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"FlowPath v{__version__}")
        self.setGeometry(100, 100, 1000, 700)

        # Initialize data service (singleton)
        self.data_service = DataService.instance()
        
        # Load settings
        self.settings = QSettings("FlowPath", "FlowPath")

        # Stack to hold all screens
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Create menu bar
        self._create_menu_bar()

        # Create screens
        self.home_screen = HomeScreen()
        self.path_editor_screen = PathEditorScreen()
        self.step_creator_screen = StepCreatorScreen()
        self.path_reader_screen = PathReaderScreen()
        self.admin_screen = AdminScreen()

        # Add screens to stack
        self.stack.addWidget(self.home_screen)          # index 0
        self.stack.addWidget(self.path_editor_screen)   # index 1
        self.stack.addWidget(self.step_creator_screen)  # index 2
        self.stack.addWidget(self.path_reader_screen)   # index 3
        self.stack.addWidget(self.admin_screen)         # index 4

        # Connect navigation signals
        self._connect_home_screen()
        self._connect_path_editor_screen()
        self._connect_step_creator_screen()
        self._connect_path_reader_screen()
        self._connect_admin_screen()

        # Load saved team folder
        self._load_team_folder()

    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # FlowPath menu (or File menu on Windows/Linux)
        file_menu = menubar.addMenu("FlowPath")
        
        # Team Folder action
        team_folder_action = QAction("Set Team Folder...", self)
        team_folder_action.setShortcut("Ctrl+,")
        team_folder_action.triggered.connect(self._on_set_team_folder)
        file_menu.addAction(team_folder_action)
        
        # Show current team folder
        self.show_folder_action = QAction("Show Team Folder", self)
        self.show_folder_action.triggered.connect(self._on_show_team_folder)
        file_menu.addAction(self.show_folder_action)
        
        file_menu.addSeparator()

        # Settings/Admin action
        settings_action = QAction("Manage Categories && Tags...", self)
        settings_action.triggered.connect(self._on_show_admin)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        # About action
        about_action = QAction("About FlowPath", self)
        about_action.triggered.connect(self._on_about)
        file_menu.addAction(about_action)

    def _load_team_folder(self):
        """Load the saved team folder setting."""
        team_folder = self.settings.value("team_folder", "")
        if team_folder:
            self.home_screen.set_team_folder(team_folder)
            self._update_window_title(team_folder)

    def _on_set_team_folder(self):
        """Handle Set Team Folder menu action."""
        current_folder = self.settings.value("team_folder", "")
        
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Team Folder",
            current_folder,
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            self.settings.setValue("team_folder", folder)
            self.home_screen.set_team_folder(folder)
            self._update_window_title(folder)

    def _on_show_team_folder(self):
        """Show the current team folder location."""
        team_folder = self.settings.value("team_folder", "")
        if team_folder:
            QMessageBox.information(
                self,
                "Team Folder",
                f"Current team folder:\n\n{team_folder}"
            )
        else:
            QMessageBox.information(
                self,
                "Team Folder",
                "No team folder set.\n\nUse FlowPath → Set Team Folder to configure."
            )

    def _on_about(self):
        """Show About dialog."""
        QMessageBox.about(
            self,
            "About FlowPath",
            f"FlowPath v{__version__}\n\n"
            "A cross-platform tool for creating step-by-step\n"
            "documentation and SOPs."
        )

    def _update_window_title(self, team_folder: str):
        """Update window title to show team folder."""
        import os
        folder_name = os.path.basename(team_folder)
        self.setWindowTitle(f"FlowPath v{__version__} - {folder_name}")

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

    def _connect_admin_screen(self):
        """Connect Admin screen signals."""
        # Back -> Home
        self.admin_screen.back_clicked.connect(self._on_exit_admin)

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

    def _show_admin(self):
        """Show the Admin screen."""
        self.admin_screen.refresh()
        self.stack.setCurrentIndex(self.ADMIN)

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

    def _on_show_admin(self):
        """Handle Manage Categories & Tags menu action."""
        self._show_admin()

    def _on_exit_admin(self):
        """Handle Back button click in Admin screen."""
        self._show_home()


def create_light_palette() -> QPalette:
    """Create a light mode palette for consistent styling."""
    palette = QPalette()
    
    # Window and widget backgrounds
    palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
    
    # Text colors
    palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(128, 128, 128))
    
    # Button colors
    palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
    
    # Highlight colors
    palette.setColor(QPalette.ColorRole.Highlight, QColor(76, 175, 80))  # FlowPath green
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    
    # Tooltip colors
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
    
    # Link colors
    palette.setColor(QPalette.ColorRole.Link, QColor(0, 102, 204))
    palette.setColor(QPalette.ColorRole.LinkVisited, QColor(102, 51, 153))
    
    # Disabled state colors
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(128, 128, 128))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(128, 128, 128))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(128, 128, 128))
    
    return palette


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Force Fusion style for consistent cross-platform appearance
    app.setStyle('Fusion')
    
    # Apply light mode palette to override system dark mode
    app.setPalette(create_light_palette())
    
    window = FlowPathWindow()
    window.show()
    sys.exit(app.exec())
