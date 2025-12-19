from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox,
    QFrame, QScrollArea, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QFont, QPainterPath

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

        # Step instructions with formatting toolbar
        self.instructions_input = MarkdownTextEdit()
        self.instructions_input.setPlaceholderText(f"Step {step_number} instructions...")
        self.instructions_input.setMinimumHeight(100)
        self.instructions_input.setMaximumHeight(130)

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


class EmptyStateWidget(QWidget):
    """Attractive empty state shown when no steps exist yet"""

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(300)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        center_x = rect.width() // 2
        center_y = rect.height() // 2 - 40

        # Draw a stylized clipboard/path icon
        self._draw_icon(painter, center_x, center_y - 60)

        # Main message
        painter.setPen(QColor("#333"))
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        painter.setFont(font)

        text = "Start building your path"
        text_rect = painter.fontMetrics().boundingRect(text)
        painter.drawText(center_x - text_rect.width() // 2, center_y + 40, text)

        # Sub message
        painter.setPen(QColor("#666"))
        font.setPointSize(12)
        font.setBold(False)
        painter.setFont(font)

        sub_text = "Capture screenshots and add instructions step by step"
        sub_rect = painter.fontMetrics().boundingRect(sub_text)
        painter.drawText(center_x - sub_rect.width() // 2, center_y + 65, sub_text)

        # Tips
        tips = [
            "Tip: Keep instructions concise - one action per step",
            "Tip: Use callouts to highlight important UI elements",
            "Tip: Minimize distractions before capturing screenshots"
        ]

        font.setPointSize(11)
        font.setItalic(True)
        painter.setFont(font)
        painter.setPen(QColor("#888"))

        tip_y = center_y + 110
        for tip in tips:
            tip_rect = painter.fontMetrics().boundingRect(tip)
            painter.drawText(center_x - tip_rect.width() // 2, tip_y, tip)
            tip_y += 22

        painter.end()

    def _draw_icon(self, painter: QPainter, cx: int, cy: int):
        """Draw a stylized clipboard with steps icon"""
        # Clipboard background
        painter.setPen(QPen(QColor("#4CAF50"), 3))
        painter.setBrush(QColor("#f5f5f5"))

        clip_width, clip_height = 60, 80
        painter.drawRoundedRect(
            cx - clip_width // 2, cy - clip_height // 2,
            clip_width, clip_height, 8, 8
        )

        # Clipboard clip at top
        painter.setBrush(QColor("#4CAF50"))
        clip_top_width = 30
        painter.drawRoundedRect(
            cx - clip_top_width // 2, cy - clip_height // 2 - 5,
            clip_top_width, 14, 4, 4
        )

        # Step lines with checkmarks
        line_y = cy - clip_height // 2 + 20
        for i in range(3):
            # Checkbox
            box_x = cx - clip_width // 2 + 12
            painter.setPen(QPen(QColor("#4CAF50"), 2))
            painter.setBrush(QColor("#fff"))
            painter.drawRect(box_x, line_y, 10, 10)

            # Checkmark for first item
            if i == 0:
                painter.setPen(QPen(QColor("#4CAF50"), 2))
                path = QPainterPath()
                path.moveTo(box_x + 2, line_y + 5)
                path.lineTo(box_x + 4, line_y + 8)
                path.lineTo(box_x + 8, line_y + 2)
                painter.drawPath(path)

            # Line placeholder
            painter.setPen(QPen(QColor("#ccc"), 2))
            line_x = box_x + 16
            painter.drawLine(line_x, line_y + 5, cx + clip_width // 2 - 12, line_y + 5)

            line_y += 20


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

        # +Step button (prominent style for empty state)
        self.add_step_btn = QPushButton("+ Add First Step")
        self.add_step_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 14px 28px;
                font-size: 15px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.add_step_btn.clicked.connect(self._on_add_step)

        steps_header = QHBoxLayout()
        steps_header.addStretch()
        steps_header.addWidget(self.add_step_btn)
        steps_layout.addLayout(steps_header)

        # Empty state widget (shown when no steps exist)
        self.empty_state = EmptyStateWidget()

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

        # Stack empty state and scroll area
        steps_layout.addWidget(self.empty_state)
        steps_layout.addWidget(self.scroll_area)
        self.scroll_area.hide()  # Hidden initially for new paths

        # Add to content layout
        content_layout.addWidget(form_widget)
        content_layout.addLayout(steps_layout)

        main_layout.addLayout(content_layout)

        self.setLayout(main_layout)

    def _refresh_categories(self):
        """Refresh the category dropdown with managed categories."""
        current_text = self.category_combo.currentText()
        self.category_combo.clear()
        self.category_combo.addItem("Select Category...")

        # Load managed categories from database
        categories = self.data_service.get_managed_categories()
        for cat in categories:
            self.category_combo.addItem(cat['name'])

        # If no managed categories exist, show a hint
        if not categories:
            self.category_combo.addItem("(Add categories in Settings)")

        # Restore previous selection if it still exists
        if current_text:
            index = self.category_combo.findText(current_text)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

    def _update_empty_state_visibility(self):
        """Show/hide empty state based on whether steps exist"""
        has_steps = len(self.step_cards) > 0

        if has_steps:
            self.empty_state.hide()
            self.scroll_area.show()
            # Update button text
            self.add_step_btn.setText("+ Step")
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
        else:
            self.empty_state.show()
            self.scroll_area.hide()
            # Prominent button for empty state
            self.add_step_btn.setText("+ Add First Step")
            self.add_step_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 14px 28px;
                    font-size: 15px;
                    font-weight: bold;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            self.add_step_btn.setFixedWidth(180)

    def new_path(self):
        """Initialize for creating a new path"""
        self.current_path = None
        self.current_path_id = None
        self.pending_steps = []
        self.title_label.setText("New Path")
        self._refresh_categories()
        self._clear_form()
        self._clear_steps()
        self._update_empty_state_visibility()

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

        # Refresh categories dropdown
        self._refresh_categories()

        # Populate form
        self.title_input.setText(path.title)

        # Set category (add it if it doesn't exist in managed categories)
        index = self.category_combo.findText(path.category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
        elif path.category:
            # Category exists on path but not in managed list - add it temporarily
            self.category_combo.addItem(path.category)
            self.category_combo.setCurrentIndex(self.category_combo.count() - 1)
        else:
            self.category_combo.setCurrentIndex(0)

        self.tags_input.setText(path.tags)
        self.description_input.setText(path.description)

        # Load steps
        self._clear_steps()
        for step in steps:
            self._add_step_card(step)

        # Update empty state visibility
        self._update_empty_state_visibility()

    def add_pending_step(self, step: Step):
        """Add a step that was created in the step creator"""
        self.pending_steps.append(step)
        self._add_step_card(step)
        self._update_empty_state_visibility()

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

            # Update empty state visibility
            self._update_empty_state_visibility()

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
