from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox,
    QFrame, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap

from ..services import DataService
from ..models import Path, Step
from ..widgets import MarkdownTextEdit


class StepCard(QFrame):
    """A single step in the path editor"""
    delete_clicked = pyqtSignal(int)  # Emits step index
    edit_clicked = pyqtSignal(int)  # Emits step index

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

        # Screenshot placeholder/display
        self.screenshot_label = QLabel("Screenshot")
        self.screenshot_label.setFixedSize(150, 100)
        self.screenshot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screenshot_label.setStyleSheet("""
            background-color: #f0f0f0;
            border: 2px dashed #ccc;
            border-radius: 4px;
        """)

        # Load screenshot if exists
        if step and step.screenshot_path:
            pixmap = QPixmap(step.screenshot_path)
            if not pixmap.isNull():
                self.screenshot_label.setPixmap(
                    pixmap.scaled(150, 100, Qt.AspectRatioMode.KeepAspectRatio)
                )

        # Step content
        content_layout = QVBoxLayout()

        # Step header with number and delete button
        header_layout = QHBoxLayout()
        step_label = QLabel(f"Step {step_number}")
        step_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(step_label)
        header_layout.addStretch()

        delete_btn = QPushButton("X")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 4px 8px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        delete_btn.setFixedSize(24, 24)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(step_number - 1))
        header_layout.addWidget(delete_btn)

        content_layout.addLayout(header_layout)

        # Step instructions (compact, no toolbar)
        self.instructions_input = MarkdownTextEdit(show_toolbar=False)
        self.instructions_input.setPlaceholderText(f"Step {step_number} instructions...")
        self.instructions_input.setMinimumHeight(80)
        self.instructions_input.setMaximumHeight(100)

        # Load existing instructions
        if step:
            self.instructions_input.setText(step.instructions)

        content_layout.addWidget(self.instructions_input)

        layout.addWidget(self.screenshot_label)
        layout.addLayout(content_layout)

        self.setLayout(layout)

    def get_instructions(self) -> str:
        """Get the current instructions text"""
        return self.instructions_input.toPlainText()

    def get_screenshot_path(self) -> str:
        """Get the screenshot path if any"""
        return self.step.screenshot_path if self.step else None


class PathEditorScreen(QWidget):
    path_saved = pyqtSignal(int)  # Emits path_id after save
    cancelled = pyqtSignal()
    add_step_requested = pyqtSignal()  # Request to open step creator

    def __init__(self):
        super().__init__()
        self.data_service = DataService.instance()
        self.current_path: Path = None
        self.current_path_id: int = None
        self.step_cards: list[StepCard] = []
        self.pending_steps: list[Step] = []  # Steps created in step creator
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # === TOP BAR ===
        top_bar = QHBoxLayout()

        self.title_label = QLabel("New Path")
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

        top_bar.addWidget(cancel_btn)
        top_bar.addWidget(self.save_done_btn)
        top_bar.addWidget(save_new_btn)

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
        self.category_combo.addItems(["Select Category...", "LMS", "Content Creation", "Admin", "Troubleshooting"])
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
        self.description_input = MarkdownTextEdit()
        self.description_input.setPlaceholderText("Description (supports **bold**, *italic*, [links](url))")
        self.description_input.setMaximumHeight(130)
        form_layout.addWidget(self.description_input)

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
        self.steps_container.addStretch()

        steps_widget = QWidget()
        steps_widget.setLayout(self.steps_container)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(steps_widget)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
            }
        """)

        steps_layout.addWidget(self.scroll_area)

        # Add to content layout
        content_layout.addWidget(form_widget)
        content_layout.addLayout(steps_layout)

        main_layout.addLayout(content_layout)

        self.setLayout(main_layout)

    def new_path(self):
        """Initialize for creating a new path"""
        self.current_path = None
        self.current_path_id = None
        self.pending_steps = []
        self.title_label.setText("New Path")
        self._clear_form()
        self._clear_steps()

    def load_path(self, path_id: int):
        """Load an existing path for editing"""
        result = self.data_service.get_path_with_steps(path_id)
        if result is None:
            QMessageBox.warning(self, "Error", "Path not found")
            return

        path, steps = result
        self.current_path = path
        self.current_path_id = path_id
        self.pending_steps = []
        self.title_label.setText(f"Edit: {path.title}")

        # Populate form
        self.title_input.setText(path.title)

        # Set category
        index = self.category_combo.findText(path.category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
        else:
            self.category_combo.setCurrentIndex(0)

        self.tags_input.setText(path.tags)
        self.description_input.setText(path.description)

        # Load steps
        self._clear_steps()
        for step in steps:
            self._add_step_card(step)

    def add_pending_step(self, step: Step):
        """Add a step that was created in the step creator"""
        self.pending_steps.append(step)
        self._add_step_card(step)

    def _clear_form(self):
        """Clear all form fields"""
        self.title_input.clear()
        self.category_combo.setCurrentIndex(0)
        self.tags_input.clear()
        self.description_input.clear()

    def _clear_steps(self):
        """Remove all step cards"""
        self.step_cards = []
        # Remove all widgets except the stretch
        while self.steps_container.count() > 1:
            item = self.steps_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _add_step_card(self, step: Step = None):
        """Add a new step card"""
        step_num = len(self.step_cards) + 1
        step_card = StepCard(step_num, step)
        step_card.delete_clicked.connect(self._on_delete_step)
        self.step_cards.append(step_card)

        # Insert before the stretch
        self.steps_container.insertWidget(self.steps_container.count() - 1, step_card)

    def _on_add_step(self):
        """Handle add step button click"""
        self.add_step_requested.emit()

    def _on_delete_step(self, index: int):
        """Handle step deletion"""
        if 0 <= index < len(self.step_cards):
            # Remove the card
            card = self.step_cards.pop(index)
            card.deleteLater()

            # Renumber remaining cards
            for i, card in enumerate(self.step_cards):
                card.step_number = i + 1
                # Update the step label
                for child in card.findChildren(QLabel):
                    if child.text().startswith("Step "):
                        child.setText(f"Step {i + 1}")
                        break

    def _collect_steps(self) -> list[Step]:
        """Collect step data from all cards"""
        steps = []
        for i, card in enumerate(self.step_cards):
            step = Step(
                path_id=self.current_path_id or 0,
                step_number=i + 1,
                instructions=card.get_instructions(),
                screenshot_path=card.get_screenshot_path(),
            )
            # Preserve existing step ID if editing
            if card.step and card.step.id:
                step.id = card.step.id
            steps.append(step)
        return steps

    def _validate(self) -> bool:
        """Validate form data"""
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a title for the path.")
            self.title_input.setFocus()
            return False
        return True

    def _save_path(self) -> int:
        """Save the current path and return its ID"""
        if not self._validate():
            return None

        # Get form data
        title = self.title_input.text().strip()
        category = self.category_combo.currentText()
        if category == "Select Category...":
            category = ""
        tags = self.tags_input.text().strip()
        description = self.description_input.toPlainText().strip()

        # Create or update path
        if self.current_path:
            # Update existing
            self.current_path.title = title
            self.current_path.category = category
            self.current_path.tags = tags
            self.current_path.description = description
            path = self.current_path
        else:
            # Create new
            path = Path(
                title=title,
                category=category,
                tags=tags,
                description=description,
            )

        # Collect steps
        steps = self._collect_steps()

        # Save to database
        path_id = self.data_service.save_path_with_steps(path, steps)
        self.current_path_id = path_id

        return path_id

    def _on_save_done(self):
        """Save and return to home"""
        path_id = self._save_path()
        if path_id:
            self.path_saved.emit(path_id)

    def _on_save_new(self):
        """Save current and start a new path"""
        path_id = self._save_path()
        if path_id:
            self.new_path()

    def _on_cancel(self):
        """Cancel editing"""
        self.cancelled.emit()
