from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..models import Step


class StepCreatorScreen(QWidget):
    step_saved = pyqtSignal(Step)  # Emits the created step
    step_saved_add_another = pyqtSignal(Step)  # Save and add another
    cancelled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_step = None
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # === TOP BAR ===
        top_bar = QHBoxLayout()

        title_label = QLabel("Step Creator")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        top_bar.addWidget(title_label)

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

        # === SCREENSHOT BUTTON ===
        screenshot_btn_layout = QHBoxLayout()
        screenshot_btn_layout.addStretch()

        self.screenshot_btn = QPushButton("+ Screen Shot")
        self.screenshot_btn.setStyleSheet("""
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
        self.screenshot_btn.clicked.connect(self.capture_screenshot)

        screenshot_btn_layout.addWidget(self.screenshot_btn)
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
        self.instructions_input = QTextEdit()
        self.instructions_input.setPlaceholderText("Step instructions...")
        self.instructions_input.setStyleSheet("""
            QTextEdit {
                padding: 15px;
                font-size: 14px;
                border: 2px solid #ccc;
                border-radius: 8px;
            }
            QTextEdit:focus {
                border-color: #4CAF50;
            }
        """)
        self.instructions_input.setMinimumHeight(120)
        self.instructions_input.setMaximumHeight(150)

        main_layout.addWidget(self.instructions_input)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def new_step(self):
        """Prepare for creating a new step."""
        self.current_step = Step()
        self.clear_step()

    def capture_screenshot(self):
        """Placeholder for screenshot capture - we'll implement this next"""
        self.screenshot_label.setText("Screenshot captured!\n(Capture functionality coming soon)")
        self.screenshot_label.setStyleSheet("color: #4CAF50; font-size: 16px; border: none;")
        # Future: Actually capture screenshot and store path
        # self.current_step.screenshot_path = captured_path

    def clear_step(self):
        """Clear the form for a new step"""
        self.screenshot_label.setText("Screenshot will appear here")
        self.screenshot_label.setStyleSheet("color: #999; font-size: 16px; border: none;")
        self.instructions_input.clear()
        if self.current_step:
            self.current_step.screenshot_path = None

    def _collect_step_data(self) -> Step:
        """Collect data from the form into a Step object."""
        if not self.current_step:
            self.current_step = Step()

        self.current_step.instructions = self.instructions_input.toPlainText().strip()
        return self.current_step

    def _on_save_done(self):
        """Save step and return to path editor."""
        step = self._collect_step_data()
        self.step_saved.emit(step)

    def _on_save_add(self):
        """Save step and prepare for another."""
        step = self._collect_step_data()
        self.step_saved_add_another.emit(step)
        self.new_step()

    def _on_cancel(self):
        """Cancel step creation."""
        self.cancelled.emit()
