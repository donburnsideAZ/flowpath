"""Step creator screen - create individual workflow steps with screenshots."""

import os
import uuid
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QFrame, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QScreen, QPixmap

from ..models import Step
from ..storage import DataStore
from .. import styles


class StepCreatorScreen(QWidget):
    """Screen for creating individual steps with screenshots."""
    step_created = pyqtSignal(object)  # Emits Step object
    save_and_continue = pyqtSignal(object)  # Save and add another step
    save_and_done = pyqtSignal(object)  # Save and return to editor

    def __init__(self):
        super().__init__()
        self.data_store = DataStore()
        self.screenshot_path = None
        self.screenshot_pixmap = None
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # === TOP BAR ===
        top_bar = QHBoxLayout()

        title_label = QLabel("Step Creator")
        title_label.setStyleSheet(styles.LABEL_TITLE)
        top_bar.addWidget(title_label)

        top_bar.addStretch()

        # Save buttons
        self.save_add_btn = QPushButton("Save && +Step")
        self.save_add_btn.setStyleSheet(styles.BUTTON_PRIMARY)
        self.save_add_btn.clicked.connect(self._on_save_and_add)

        self.save_done_btn = QPushButton("Save && Done")
        self.save_done_btn.setStyleSheet(styles.BUTTON_NEUTRAL)
        self.save_done_btn.clicked.connect(self._on_save_and_done)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(styles.BUTTON_NEUTRAL)
        self.cancel_btn.clicked.connect(self._on_cancel)

        top_bar.addWidget(self.save_add_btn)
        top_bar.addWidget(self.save_done_btn)
        top_bar.addWidget(self.cancel_btn)

        main_layout.addLayout(top_bar)
        main_layout.addSpacing(20)

        # === SCREENSHOT BUTTON ===
        screenshot_btn_layout = QHBoxLayout()
        screenshot_btn_layout.addStretch()

        self.screenshot_btn = QPushButton("+ Screen Shot")
        self.screenshot_btn.setStyleSheet(styles.BUTTON_PRIMARY)
        self.screenshot_btn.clicked.connect(self._capture_screenshot)

        self.clear_screenshot_btn = QPushButton("Clear")
        self.clear_screenshot_btn.setStyleSheet(styles.BUTTON_NEUTRAL)
        self.clear_screenshot_btn.clicked.connect(self._clear_screenshot)
        self.clear_screenshot_btn.setVisible(False)

        screenshot_btn_layout.addWidget(self.screenshot_btn)
        screenshot_btn_layout.addWidget(self.clear_screenshot_btn)
        screenshot_btn_layout.addStretch()

        main_layout.addLayout(screenshot_btn_layout)
        main_layout.addSpacing(20)

        # === SCREENSHOT AREA ===
        self.screenshot_frame = QFrame()
        self.screenshot_frame.setFrameStyle(QFrame.Shape.Box)
        self.screenshot_frame.setStyleSheet(styles.SCREENSHOT_FRAME)
        self.screenshot_frame.setMinimumHeight(350)

        screenshot_layout = QVBoxLayout()
        self.screenshot_label = QLabel("Screenshot will appear here\n\nClick '+ Screen Shot' to capture your screen")
        self.screenshot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screenshot_label.setStyleSheet("color: #999; font-size: 16px; border: none;")
        screenshot_layout.addWidget(self.screenshot_label)
        self.screenshot_frame.setLayout(screenshot_layout)

        main_layout.addWidget(self.screenshot_frame)
        main_layout.addSpacing(20)

        # === STEP INSTRUCTIONS ===
        instructions_label = QLabel("Instructions")
        instructions_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(instructions_label)

        self.instructions_input = QTextEdit()
        self.instructions_input.setPlaceholderText(
            "Describe what the user should do in this step...\n\n"
            "Example: Click the 'Settings' button in the top-right corner of the screen."
        )
        self.instructions_input.setStyleSheet(styles.INPUT_TEXTAREA)
        self.instructions_input.setMinimumHeight(120)
        self.instructions_input.setMaximumHeight(150)

        main_layout.addWidget(self.instructions_input)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def _capture_screenshot(self):
        """Capture a screenshot of the entire screen."""
        # Hide the window briefly to capture clean screenshot
        main_window = self.window()
        main_window.hide()

        # Small delay to ensure window is hidden
        QTimer.singleShot(300, self._do_capture)

    def _do_capture(self):
        """Actually perform the screenshot capture."""
        try:
            # Get the primary screen
            screen = QApplication.primaryScreen()
            if screen:
                # Capture the entire screen
                self.screenshot_pixmap = screen.grabWindow(0)

                # Generate unique filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}_{uuid.uuid4().hex[:8]}.png"
                self.screenshot_path = self.data_store.get_screenshot_path(filename)

                # Save the screenshot
                self.screenshot_pixmap.save(self.screenshot_path, "PNG")

                # Display scaled preview
                scaled = self.screenshot_pixmap.scaled(
                    600, 400,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.screenshot_label.setPixmap(scaled)
                self.screenshot_label.setStyleSheet("border: none;")

                # Show clear button
                self.clear_screenshot_btn.setVisible(True)
            else:
                self.screenshot_label.setText("Failed to capture screenshot\n(No screen available)")
                self.screenshot_label.setStyleSheet("color: #f44336; font-size: 16px; border: none;")
        except Exception as e:
            self.screenshot_label.setText(f"Screenshot error:\n{str(e)}")
            self.screenshot_label.setStyleSheet("color: #f44336; font-size: 16px; border: none;")
        finally:
            # Show the window again
            main_window = self.window()
            main_window.show()
            main_window.raise_()
            main_window.activateWindow()

    def _clear_screenshot(self):
        """Clear the current screenshot."""
        # Delete the screenshot file if it exists
        if self.screenshot_path and os.path.exists(self.screenshot_path):
            try:
                os.remove(self.screenshot_path)
            except:
                pass

        self.screenshot_path = None
        self.screenshot_pixmap = None
        self.screenshot_label.setPixmap(QPixmap())
        self.screenshot_label.setText("Screenshot will appear here\n\nClick '+ Screen Shot' to capture your screen")
        self.screenshot_label.setStyleSheet("color: #999; font-size: 16px; border: none;")
        self.clear_screenshot_btn.setVisible(False)

    def _create_step(self) -> Step:
        """Create a Step object from current form data."""
        return Step(
            instructions=self.instructions_input.toPlainText().strip(),
            screenshot_path=self.screenshot_path
        )

    def _validate(self) -> bool:
        """Validate the form."""
        instructions = self.instructions_input.toPlainText().strip()
        if not instructions:
            QMessageBox.warning(
                self, "Validation Error",
                "Please enter instructions for this step."
            )
            return False
        return True

    def _on_save_and_add(self):
        """Save step and prepare for another."""
        if self._validate():
            step = self._create_step()
            self.save_and_continue.emit(step)
            self.clear_step()

    def _on_save_and_done(self):
        """Save step and return to editor."""
        if self._validate():
            step = self._create_step()
            self.save_and_done.emit(step)

    def _on_cancel(self):
        """Cancel step creation."""
        self._clear_screenshot()
        self.save_and_done.emit(None)

    def clear_step(self):
        """Clear the form for a new step."""
        self._clear_screenshot()
        self.instructions_input.clear()
