"""Path editor screen - create and edit workflow paths."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QComboBox,
    QFrame, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..models import Path, Step
from ..storage import DataStore
from .. import styles


class StepCard(QFrame):
    """A single step card in the editor."""
    delete_requested = pyqtSignal(int)  # Emits step index

    def __init__(self, step_number: int, step: Step = None):
        super().__init__()
        self.step_number = step_number
        self.step = step

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

        # Screenshot placeholder
        self.screenshot_label = QLabel("Screenshot")
        self.screenshot_label.setFixedSize(150, 100)
        self.screenshot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screenshot_label.setStyleSheet(styles.SCREENSHOT_PLACEHOLDER)

        if step and step.screenshot_path:
            self.screenshot_label.setText("Has Screenshot")
            self.screenshot_label.setStyleSheet(
                styles.SCREENSHOT_PLACEHOLDER + "color: #4CAF50;"
            )

        # Step content area
        content_layout = QVBoxLayout()

        # Step header with number and delete button
        header_layout = QHBoxLayout()
        step_label = QLabel(f"Step {step_number}")
        step_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(step_label)
        header_layout.addStretch()

        delete_btn = QPushButton("×")
        delete_btn.setFixedSize(24, 24)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.step_number - 1))
        header_layout.addWidget(delete_btn)

        content_layout.addLayout(header_layout)

        # Step instructions
        self.instructions = QTextEdit()
        self.instructions.setPlaceholderText(f"Step {step_number} instructions...")
        self.instructions.setStyleSheet(styles.INPUT_TEXTAREA)
        self.instructions.setMinimumHeight(80)
        self.instructions.setMaximumHeight(100)

        if step:
            self.instructions.setText(step.instructions)

        content_layout.addWidget(self.instructions)

        layout.addWidget(self.screenshot_label)
        layout.addLayout(content_layout)

        self.setLayout(layout)

    def get_step_data(self) -> Step:
        """Get the step data from this card."""
        if self.step:
            self.step.instructions = self.instructions.toPlainText()
            return self.step
        else:
            return Step(instructions=self.instructions.toPlainText())


class PathEditorScreen(QWidget):
    """Screen for creating and editing paths."""
    save_completed = pyqtSignal()  # Emitted when save is done
    add_step_requested = pyqtSignal()  # Request to open step creator
    path_saved = pyqtSignal(str)  # Emits path_id after save

    def __init__(self):
        super().__init__()
        self.data_store = DataStore()
        self.current_path = None  # Path being edited
        self.step_cards = []  # List of StepCard widgets
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # === TOP BAR ===
        top_bar = QHBoxLayout()

        self.title_label = QLabel("New Path")
        self.title_label.setStyleSheet(styles.LABEL_TITLE)
        top_bar.addWidget(self.title_label)

        top_bar.addStretch()

        # Save buttons
        self.save_done_btn = QPushButton("Save && Done")
        self.save_done_btn.setStyleSheet(styles.BUTTON_NEUTRAL)
        self.save_done_btn.clicked.connect(self._on_save_done)

        self.save_new_btn = QPushButton("Save && New")
        self.save_new_btn.setStyleSheet(styles.BUTTON_NEUTRAL)
        self.save_new_btn.clicked.connect(self._on_save_new)

        self.save_sync_btn = QPushButton("Save && Sync")
        self.save_sync_btn.setStyleSheet(styles.BUTTON_PRIMARY)
        self.save_sync_btn.clicked.connect(self._on_save_sync)

        top_bar.addWidget(self.save_done_btn)
        top_bar.addWidget(self.save_new_btn)
        top_bar.addWidget(self.save_sync_btn)

        main_layout.addLayout(top_bar)

        # === FORM AND STEPS AREA ===
        content_layout = QHBoxLayout()

        # Left side: metadata form
        form_layout = QVBoxLayout()

        # Title
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Title")
        self.title_input.setStyleSheet(styles.INPUT_TEXT)
        form_layout.addWidget(self.title_input)

        # Category dropdown
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Select Category...", "LMS", "Content Creation",
            "Admin", "Troubleshooting"
        ])
        self.category_combo.setStyleSheet(styles.INPUT_COMBO)
        form_layout.addWidget(self.category_combo)

        # Tags
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Tags (comma separated)")
        self.tags_input.setStyleSheet(styles.INPUT_TEXT)
        form_layout.addWidget(self.tags_input)

        # Description
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Description")
        self.description_input.setStyleSheet(styles.INPUT_TEXTAREA)
        self.description_input.setMaximumHeight(100)
        form_layout.addWidget(self.description_input)

        form_layout.addStretch()

        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        form_widget.setFixedWidth(250)

        # Right side: steps area
        steps_layout = QVBoxLayout()

        # +Step button
        self.add_step_btn = QPushButton("+ Step")
        self.add_step_btn.setStyleSheet(styles.BUTTON_PRIMARY)
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

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(steps_widget)
        self.scroll_area.setStyleSheet(styles.SCROLL_AREA)

        steps_layout.addWidget(self.scroll_area)

        # Add to content layout
        content_layout.addWidget(form_widget)
        content_layout.addLayout(steps_layout)

        main_layout.addLayout(content_layout)

        self.setLayout(main_layout)

    def load_path(self, path_id: str = None):
        """Load a path for editing, or create a new one."""
        if path_id:
            self.current_path = self.data_store.get_path(path_id)
            if self.current_path:
                self._populate_form()
                self.title_label.setText("Edit Path")
            else:
                self._create_new_path()
        else:
            self._create_new_path()

    def _create_new_path(self):
        """Initialize form for a new path."""
        self.current_path = Path(title="")
        self.title_label.setText("New Path")
        self._clear_form()

    def _populate_form(self):
        """Populate form with current path data."""
        if not self.current_path:
            return

        self.title_input.setText(self.current_path.title)

        # Set category
        category_index = self.category_combo.findText(self.current_path.category)
        if category_index >= 0:
            self.category_combo.setCurrentIndex(category_index)
        else:
            self.category_combo.setCurrentIndex(0)

        self.tags_input.setText(self.current_path.get_tags_string())
        self.description_input.setText(self.current_path.description)

        # Load steps
        self._clear_steps()
        for i, step in enumerate(self.current_path.steps):
            self._add_step_card(step)

    def _clear_form(self):
        """Clear all form fields."""
        self.title_input.clear()
        self.category_combo.setCurrentIndex(0)
        self.tags_input.clear()
        self.description_input.clear()
        self._clear_steps()

    def _clear_steps(self):
        """Remove all step cards."""
        for card in self.step_cards:
            card.deleteLater()
        self.step_cards = []

    def _add_step_card(self, step: Step = None):
        """Add a step card to the editor."""
        step_num = len(self.step_cards) + 1
        card = StepCard(step_num, step)
        card.delete_requested.connect(self._on_delete_step)
        self.step_cards.append(card)
        self.steps_container.addWidget(card)

    def _on_delete_step(self, index: int):
        """Handle step deletion."""
        if 0 <= index < len(self.step_cards):
            card = self.step_cards.pop(index)
            card.deleteLater()
            # Renumber remaining cards
            self._renumber_steps()

    def _renumber_steps(self):
        """Update step numbers after deletion."""
        for i, card in enumerate(self.step_cards):
            card.step_number = i + 1
            # Update the step label in the card
            for child in card.findChildren(QLabel):
                if child.text().startswith("Step"):
                    child.setText(f"Step {i + 1}")
                    break

    def _collect_form_data(self) -> bool:
        """Collect form data into current_path. Returns True if valid."""
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Validation Error", "Please enter a title.")
            return False

        self.current_path.title = title

        category_index = self.category_combo.currentIndex()
        if category_index > 0:
            self.current_path.category = self.category_combo.currentText()
        else:
            self.current_path.category = ""

        self.current_path.set_tags_from_string(self.tags_input.text())
        self.current_path.description = self.description_input.toPlainText()

        # Collect steps
        self.current_path.steps = []
        for card in self.step_cards:
            step = card.get_step_data()
            if step.instructions.strip():  # Only add non-empty steps
                self.current_path.steps.append(step)

        return True

    def _save_path(self) -> bool:
        """Save the current path to storage."""
        if not self._collect_form_data():
            return False

        success = self.data_store.save_path(self.current_path)
        if success:
            self.path_saved.emit(self.current_path.path_id)
        else:
            QMessageBox.critical(self, "Save Error", "Failed to save path.")
        return success

    def _on_save_done(self):
        """Save and return to home."""
        if self._save_path():
            self.save_completed.emit()

    def _on_save_new(self):
        """Save and start a new path."""
        if self._save_path():
            self._create_new_path()

    def _on_save_sync(self):
        """Save and sync (placeholder for future remote sync)."""
        if self._save_path():
            QMessageBox.information(
                self, "Sync",
                "Path saved locally. Remote sync coming soon!"
            )

    def _on_add_step(self):
        """Request to add a new step via step creator."""
        self.add_step_requested.emit()

    def add_step(self, step: Step):
        """Add a step from the step creator."""
        self._add_step_card(step)

    def add_step_inline(self):
        """Add an empty step card directly in the editor."""
        self._add_step_card()
