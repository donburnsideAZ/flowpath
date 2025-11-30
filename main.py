import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt6.QtGui import QScreen
from flowpath.screens.home import HomeScreen
from flowpath.screens.path_editor import PathEditorScreen
from flowpath.screens.step_creator import StepCreatorScreen
from flowpath.screens.path_reader import PathReaderScreen


class FlowPathWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FlowPath")

        # Set window size to 50% of available screen
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        width = int(screen_geometry.width() * 0.5)
        height = int(screen_geometry.height() * 0.5)

        # Center the window on screen
        x = (screen_geometry.width() - width) // 2
        y = (screen_geometry.height() - height) // 2
        self.setGeometry(x, y, width, height)
        
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
        
        # Connect navigation
        self.home_screen.new_path_btn.clicked.connect(self.show_path_editor)
        self.home_screen.path_clicked.connect(self.show_path_reader)
        self.path_editor_screen.save_done_btn.clicked.connect(self.show_home)
        self.path_editor_screen.add_step_btn.clicked.connect(self.show_step_creator)
        self.step_creator_screen.save_done_btn.clicked.connect(self.show_path_editor)
        self.step_creator_screen.save_add_btn.clicked.connect(self.save_and_new_step)
        self.path_reader_screen.exit_btn.clicked.connect(self.show_home)
        self.path_reader_screen.edit_btn.clicked.connect(self.show_path_editor)
    
    def show_home(self):
        self.stack.setCurrentIndex(0)
    
    def show_path_editor(self):
        self.stack.setCurrentIndex(1)
    
    def show_step_creator(self):
        self.stack.setCurrentIndex(2)
    
    def show_path_reader(self):
        self.stack.setCurrentIndex(3)
    
    def save_and_new_step(self):
        """Save current step and clear for a new one"""
        self.step_creator_screen.clear_step()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FlowPathWindow()
    window.show()
    sys.exit(app.exec())
