from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QAction

from ..models import Step
from ..widgets import MarkdownTextEdit, ScreenCapture


class StepCreatorScreen(QWidget):
    step_saved = pyqtSignal(Step)  # Emits the created step
    done_clicked = pyqtSignal()  # Emitted when Save & Done is clicked
    cancelled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.screenshot_path = None
        self.step_number = 1  # Will be set by the caller
        self.screen_capture = ScreenCapture()
        self.screen_capture.captured.connect(self._on_screenshot_captured)
        self.screen_capture.cancelled.connect(self._on_screenshot_cancelled)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # === TOP BAR ===
        top_bar = QHBoxLayout()

        self.title_label = QLabel("Step Creator")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        top_bar.addWidget(self.title_label)

        top_bar.addStretch()

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333;
                border: 1px solid #ccc;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        cancel_btn.clicked.connect(self._on_cancel)

        # Save buttons
        self.save_add_btn = QPushButton("Save && +Step")
        self.save_add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.save_add_btn.clicked.connect(self._on_save_add)

        self.save_done_btn = QPushButton("Save && Done")
        self.save_done_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        self.save_done_btn.clicked.connect(self._on_save_done)

        top_bar.addWidget(cancel_btn)
        top_bar.addWidget(self.save_add_btn)
        top_bar.addWidget(self.save_done_btn)

        main_layout.addLayout(top_bar)
        main_layout.addSpacing(20)

        # === SCREENSHOT BUTTONS ===
        screenshot_btn_layout = QHBoxLayout()
        screenshot_btn_layout.addStretch()

        # Full screen capture button
        self.fullscreen_btn = QPushButton("Full Screen")
        self.fullscreen_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.fullscreen_btn.clicked.connect(self._capture_full_screen)

        # Region select button
        self.region_btn = QPushButton("Select Region")
        self.region_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.region_btn.clicked.connect(self._capture_region)

        screenshot_btn_layout.addWidget(self.fullscreen_btn)
        screenshot_btn_layout.addWidget(self.region_btn)
        screenshot_btn_layout.addStretch()

        main_layout.addLayout(screenshot_btn_layout)
        main_layout.addSpacing(20)

        # === SCREENSHOT AREA ===
        self.screenshot_frame = QFrame()
        self.screenshot_frame.setFrameStyle(QFrame.Shape.Box)
        self.screenshot_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 3px dashed #ccc;
                border-radius: 8px;
            }
        """)
        self.screenshot_frame.setMinimumHeight(350)

        screenshot_layout = QVBoxLayout()
        self.screenshot_label = QLabel("Screenshot will appear here")
        self.screenshot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screenshot_label.setStyleSheet("color: #999; font-size: 16px; border: none;")
        screenshot_layout.addWidget(self.screenshot_label)
        self.screenshot_frame.setLayout(screenshot_layout)

        main_layout.addWidget(self.screenshot_frame)
        main_layout.addSpacing(20)

        # === STEP INSTRUCTIONS ===
        self.instructions_input = MarkdownTextEdit()
        self.instructions_input.setPlaceholderText("Step instructions... (use **bold**, *italic*, [link](url))")
        self.instructions_input.setMinimumHeight(120)
        self.instructions_input.setMaximumHeight(180)

        main_layout.addWidget(self.instructions_input)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def set_step_number(self, number: int):
        """Set the step number for display"""
        self.step_number = number
        self.title_label.setText(f"Step {number} Creator")

    def _capture_full_screen(self):
        """Capture the full screen."""
        # Get the main window to minimize
        main_window = self.window()
        self.screen_capture.capture_full_screen(main_window)

    def _capture_region(self):
        """Capture a selected region of the screen."""
        main_window = self.window()
        self.screen_capture.capture_region(main_window)

    def _on_screenshot_captured(self, filepath: str):
        """Handle successful screenshot capture."""
        self.screenshot_path = filepath

        # Load and display the screenshot
        pixmap = QPixmap(filepath)
        if not pixmap.isNull():
            # Scale to fit the frame while maintaining aspect ratio
            scaled = pixmap.scaled(
                self.screenshot_frame.width() - 20,
                self.screenshot_frame.height() - 20,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.screenshot_label.setPixmap(scaled)
            self.screenshot_label.setStyleSheet("border: none;")
        else:
            self.screenshot_label.setText("Screenshot saved!")
            self.screenshot_label.setStyleSheet("color: #4CAF50; font-size: 16px; border: none;")

    def _on_screenshot_cancelled(self):
        """Handle cancelled screenshot capture."""
        # Don't change anything if cancelled
        pass

    def capture_screenshot(self):
        """Legacy method - triggers full screen capture."""
        self._capture_full_screen()

    def clear_step(self):
        """Clear the form for a new step"""
        self.screenshot_label.setText("Screenshot will appear here")
        self.screenshot_label.setStyleSheet("color: #999; font-size: 16px; border: none;")
        self.instructions_input.clear()
        self.screenshot_path = None

    def _create_step(self) -> Step:
        """Create a Step object from the current form data"""
        return Step(
            path_id=0,  # Will be set when saving the path
            step_number=self.step_number,
            instructions=self.instructions_input.toPlainText().strip(),
            screenshot_path=self.screenshot_path,
        )

    def _validate(self) -> bool:
        """Validate the step data"""
        instructions = self.instructions_input.toPlainText().strip()
        if not instructions:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter instructions for this step."
            )
            self.instructions_input.setFocus()
            return False
        return True

    def _on_save_add(self):
        """Save current step and prepare for another"""
        if not self._validate():
            return

        step = self._create_step()
        self.step_saved.emit(step)

        # Prepare for next step
        self.step_number += 1
        self.set_step_number(self.step_number)
        self.clear_step()

    def _on_save_done(self):
        """Save current step and return to path editor"""
        if not self._validate():
            return

        step = self._create_step()
        self.step_saved.emit(step)
        self.done_clicked.emit()

    def _on_cancel(self):
        """Cancel and return to path editor"""
        self.cancelled.emit()
