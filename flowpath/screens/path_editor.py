from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QComboBox,
    QFrame, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..database import get_database
from ..models import Path, Step


class StepCard(QFrame):
    """A single step in the path editor"""
    delete_requested = pyqtSignal(int)  # Emits step index

    def __init__(self, step_number: int, step: Step = None):
        super().__init__()
        self.step_number = step_number
        self.step = step or Step(step_number=step_number)

        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            StepCard {
                background-color: white;
                border: 2px solid #333;
                border-radius: 8px;
                margin: 5px;
            }
        """)

        layout = QHBoxLayout()

        # Step number label
        step_num_label = QLabel(f"Step {step_number}")
        step_num_label.setStyleSheet("font-weight: bold; font-size: 14px; min-width: 60px;")

        # Screenshot placeholder
        self.screenshot_label = QLabel("No screenshot")
        self.screenshot_label.setFixedSize(150, 100)
        self.screenshot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screenshot_label.setStyleSheet("""
            background-color: #f0f0f0;
            border: 2px dashed #ccc;
            border-radius: 4px;
        """)

        if self.step.screenshot_path:
            self.screenshot_label.setText("Screenshot")
            self.screenshot_label.setStyleSheet("""
                background-color: #e8f5e9;
                border: 2px solid #4CAF50;
                border-radius: 4px;
            """)

        # Step instructions
        self.instructions_input = QTextEdit()
        self.instructions_input.setPlaceholderText(f"Step {step_number} instructions...")
        self.instructions_input.setPlainText(self.step.instructions)
        self.instructions_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        self.instructions_input.setMinimumHeight(80)
        self.instructions_input.setMaximumHeight(100)

        # Delete button
        delete_btn = QPushButton("×")
        delete_btn.setFixedSize(30, 30)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.step_number - 1))

        layout.addWidget(step_num_label)
        layout.addWidget(self.screenshot_label)
        layout.addWidget(self.instructions_input, 1)
        layout.addWidget(delete_btn)

        self.setLayout(layout)

    def get_step_data(self) -> Step:
        """Get the current step data from the UI."""
        self.step.instructions = self.instructions_input.toPlainText()
        self.step.step_number = self.step_number
        return self.step

    def set_screenshot(self, path: str):
        """Update screenshot display."""
        self.step.screenshot_path = path
        if path:
            self.screenshot_label.setText("Screenshot")
            self.screenshot_label.setStyleSheet("""
                background-color: #e8f5e9;
                border: 2px solid #4CAF50;
                border-radius: 4px;
            """)


class PathEditorScreen(QWidget):
    path_saved = pyqtSignal(int)  # Emits path_id after save
    cancelled = pyqtSignal()
    add_step_requested = pyqtSignal()

    # Default categories
    CATEGORIES = ["", "LMS", "Content Creation", "Admin", "Troubleshooting"]

    def __init__(self):
        super().__init__()
        self.current_path = None  # Path being edited
        self.step_cards = []
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # === TOP BAR ===
        top_bar = QHBoxLayout()

        self.title_header = QLabel("New Path")
        self.title_header.setStyleSheet("font-size: 20px; font-weight: bold;")
        top_bar.addWidget(self.title_header)

        top_bar.addStretch()

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333;
                border: 1px solid #ccc;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        cancel_btn.clicked.connect(self._on_cancel)

        # Save buttons
        self.save_done_btn = QPushButton("Save && Done")
        self.save_done_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        self.save_done_btn.clicked.connect(self._on_save_done)

        save_new_btn = QPushButton("Save && New")
        save_new_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        save_new_btn.clicked.connect(self._on_save_new)

        save_sync_btn = QPushButton("Save && Sync")
        save_sync_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        top_bar.addWidget(cancel_btn)
        top_bar.addWidget(self.save_done_btn)
        top_bar.addWidget(save_new_btn)
        top_bar.addWidget(save_sync_btn)

        main_layout.addLayout(top_bar)

        # === FORM AND STEPS AREA ===
        content_layout = QHBoxLayout()

        # Left side: metadata form
        form_layout = QVBoxLayout()

        # Title
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Title")
        self.title_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #ccc;
                border-radius: 4px;
            }
        """)
        form_layout.addWidget(self.title_input)

        # Category dropdown
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Select Category..."] + self.CATEGORIES[1:])
        self.category_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #ccc;
                border-radius: 4px;
            }
        """)
        form_layout.addWidget(self.category_combo)

        # Tags
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Tags (comma separated)")
        self.tags_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #ccc;
                border-radius: 4px;
            }
        """)
        form_layout.addWidget(self.tags_input)

        # Description
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Description")
        self.description_input.setStyleSheet("""
            QTextEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #ccc;
                border-radius: 4px;
            }
        """)
        self.description_input.setMaximumHeight(100)
        form_layout.addWidget(self.description_input)

        # Delete path button (only visible when editing)
        self.delete_btn = QPushButton("Delete Path")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self.delete_btn.clicked.connect(self._on_delete)
        self.delete_btn.hide()
        form_layout.addWidget(self.delete_btn)

        form_layout.addStretch()

        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        form_widget.setFixedWidth(250)

        # Right side: steps area
        steps_layout = QVBoxLayout()

        # +Step button
        self.add_step_btn = QPushButton("+ Step")
        self.add_step_btn.setStyleSheet("""
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
        self.add_step_btn.setFixedWidth(120)
        self.add_step_btn.clicked.connect(self._on_add_step)

        steps_header = QHBoxLayout()
        steps_header.addStretch()
        steps_header.addWidget(self.add_step_btn)
        steps_layout.addLayout(steps_header)

        # Scrollable steps area
        self.steps_container = QVBoxLayout()
        self.steps_container.setAlignment(Qt.AlignmentFlag.AlignTop)

        steps_widget = QWidget()
        steps_widget.setLayout(self.steps_container)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(steps_widget)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
            }
        """)

        steps_layout.addWidget(scroll_area)

        # Add to content layout
        content_layout.addWidget(form_widget)
        content_layout.addLayout(steps_layout)

        main_layout.addLayout(content_layout)

        self.setLayout(main_layout)

    def new_path(self):
        """Set up for creating a new path."""
        self.current_path = Path()
        self.title_header.setText("New Path")
        self.delete_btn.hide()
        self._clear_form()

    def load_path(self, path_id: int):
        """Load a path for editing."""
        db = get_database()
        self.current_path = db.get_path(path_id)

        if not self.current_path:
            return

        self.title_header.setText("Edit Path")
        self.delete_btn.show()

        # Populate form
        self.title_input.setText(self.current_path.title)
        self.tags_input.setText(self.current_path.tags)
        self.description_input.setPlainText(self.current_path.description)

        # Set category
        category = self.current_path.category
        index = self.category_combo.findText(category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
        else:
            self.category_combo.setCurrentIndex(0)

        # Clear and reload steps
        self._clear_steps()
        for step in self.current_path.steps:
            self._add_step_card(step)

    def _clear_form(self):
        """Clear all form inputs."""
        self.title_input.clear()
        self.category_combo.setCurrentIndex(0)
        self.tags_input.clear()
        self.description_input.clear()
        self._clear_steps()

    def _clear_steps(self):
        """Remove all step cards."""
        for card in self.step_cards:
            self.steps_container.removeWidget(card)
            card.deleteLater()
        self.step_cards.clear()

    def _add_step_card(self, step: Step = None):
        """Add a step card to the editor."""
        step_number = len(self.step_cards) + 1
        card = StepCard(step_number, step)
        card.delete_requested.connect(self._on_delete_step)
        self.step_cards.append(card)
        self.steps_container.addWidget(card)

    def _on_add_step(self):
        """Handle adding a new step."""
        # Emit signal so main window can navigate to step creator
        self.add_step_requested.emit()

    def add_step_inline(self):
        """Add a new empty step directly in the editor."""
        self._add_step_card()

    def add_step_from_creator(self, step: Step):
        """Add a step created by the step creator."""
        step.step_number = len(self.step_cards) + 1
        self._add_step_card(step)

    def _on_delete_step(self, index: int):
        """Handle step deletion."""
        if 0 <= index < len(self.step_cards):
            card = self.step_cards.pop(index)
            self.steps_container.removeWidget(card)
            card.deleteLater()

            # Renumber remaining steps
            for i, card in enumerate(self.step_cards):
                card.step_number = i + 1

    def _collect_path_data(self) -> Path:
        """Collect all data from the form into the path object."""
        if not self.current_path:
            self.current_path = Path()

        self.current_path.title = self.title_input.text().strip()

        category_index = self.category_combo.currentIndex()
        if category_index > 0:
            self.current_path.category = self.category_combo.currentText()
        else:
            self.current_path.category = ""

        self.current_path.tags = self.tags_input.text().strip()
        self.current_path.description = self.description_input.toPlainText().strip()

        # Collect steps
        self.current_path.steps = []
        for i, card in enumerate(self.step_cards):
            step = card.get_step_data()
            step.step_number = i + 1
            self.current_path.steps.append(step)

        return self.current_path

    def _validate(self) -> bool:
        """Validate the form data."""
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a title.")
            self.title_input.setFocus()
            return False
        return True

    def _save_path(self) -> int:
        """Save the path to the database. Returns path_id."""
        if not self._validate():
            return None

        path = self._collect_path_data()
        db = get_database()

        if path.id:
            # Update existing
            db.update_path(path)
        else:
            # Create new
            path = db.create_path(path)

        return path.id

    def _on_save_done(self):
        """Save and return to home."""
        path_id = self._save_path()
        if path_id:
            self.path_saved.emit(path_id)

    def _on_save_new(self):
        """Save current path and start a new one."""
        path_id = self._save_path()
        if path_id:
            self.new_path()

    def _on_cancel(self):
        """Cancel editing."""
        self.cancelled.emit()

    def _on_delete(self):
        """Delete the current path."""
        if not self.current_path or not self.current_path.id:
            return

        reply = QMessageBox.question(
            self, "Delete Path",
            f"Are you sure you want to delete '{self.current_path.title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            db = get_database()
            db.delete_path(self.current_path.id)
            self.cancelled.emit()
