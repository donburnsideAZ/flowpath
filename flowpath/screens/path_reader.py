from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap

from ..services import DataService
from ..models import Path, Step
from ..widgets import MarkdownLabel


class ReaderStepCard(QFrame):
    """A step displayed in read-only mode"""

    def __init__(self, step: Step):
        super().__init__()
        self.step = step

        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            ReaderStepCard {
                background-color: white;
                border: 2px solid #333;
                border-radius: 8px;
                margin: 10px;
            }
        """)

        layout = QHBoxLayout()

        # Screenshot placeholder/display
        self.screenshot_label = QLabel(f"Screenshot {step.step_number}")
        self.screenshot_label.setFixedSize(200, 140)
        self.screenshot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screenshot_label.setStyleSheet("""
            background-color: #f0f0f0;
            border: 2px solid #ccc;
            border-radius: 4px;
            font-size: 14px;
            color: #666;
        """)

        # Load screenshot if exists
        if step.screenshot_path:
            pixmap = QPixmap(step.screenshot_path)
            if not pixmap.isNull():
                self.screenshot_label.setPixmap(
                    pixmap.scaled(200, 140, Qt.AspectRatioMode.KeepAspectRatio)
                )
                self.screenshot_label.setStyleSheet("""
                    background-color: #f0f0f0;
                    border: 2px solid #ccc;
                    border-radius: 4px;
                """)

        # Step content
        content_layout = QVBoxLayout()

        step_label = QLabel(f"Step {step.step_number}")
        step_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #333;")

        # Use MarkdownLabel to render formatted instructions
        instructions_label = MarkdownLabel()
        instructions_label.setMarkdown(step.instructions or "No instructions provided.")
        instructions_label.setStyleSheet("font-size: 14px; color: #444; padding: 10px 0;")

        content_layout.addWidget(step_label)
        content_layout.addWidget(instructions_label)
        content_layout.addStretch()

        layout.addWidget(self.screenshot_label)
        layout.addLayout(content_layout)
        layout.addStretch()

        self.setLayout(layout)


class PathReaderScreen(QWidget):
    exit_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)  # Emits path_id

    def __init__(self):
        super().__init__()
        self.data_service = DataService.instance()
        self.current_path: Path = None
        self.current_path_id: int = None
        self.current_user = ""  # Will be set by main window if needed
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout()

        # === TOP BAR ===
        top_bar = QHBoxLayout()

        # Path title
        self.title_label = QLabel("Path Title")
        self.title_label.setStyleSheet("font-size: 22px; font-weight: bold;")
        top_bar.addWidget(self.title_label)

        top_bar.addStretch()

        # Action buttons
        share_btn = QPushButton("Share")
        share_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

        export_btn = QPushButton("Export")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

        print_btn = QPushButton("Print")
        print_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

        self.exit_btn = QPushButton("Exit")
        self.exit_btn.setStyleSheet("""
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
        self.exit_btn.clicked.connect(self._on_exit)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setStyleSheet("""
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
        self.edit_btn.clicked.connect(self._on_edit)

        top_bar.addWidget(share_btn)
        top_bar.addWidget(export_btn)
        top_bar.addWidget(print_btn)
        top_bar.addWidget(self.exit_btn)
        top_bar.addWidget(self.edit_btn)

        self.main_layout.addLayout(top_bar)
        self.main_layout.addSpacing(10)

        # === PATH METADATA ===
        meta_layout = QHBoxLayout()

        self.category_label = QLabel("Category: ")
        self.category_label.setStyleSheet("color: #666; font-size: 13px;")

        self.tags_label = QLabel("Tags: ")
        self.tags_label.setStyleSheet("color: #1976D2; font-size: 13px;")

        meta_layout.addWidget(self.category_label)
        meta_layout.addSpacing(30)
        meta_layout.addWidget(self.tags_label)
        meta_layout.addStretch()

        self.main_layout.addLayout(meta_layout)

        # Description (renders Markdown)
        self.description_label = MarkdownLabel()
        self.description_label.setStyleSheet("color: #555; font-size: 13px; padding: 10px 0;")
        self.main_layout.addWidget(self.description_label)

        self.main_layout.addSpacing(10)

        # === STEPS AREA ===
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
                background-color: #fafafa;
            }
        """)

        self.main_layout.addWidget(self.scroll_area)

        self.setLayout(self.main_layout)

    def load_path(self, path_id: int):
        """Load and display a path"""
        result = self.data_service.get_path_with_steps(path_id)
        if result is None:
            self.title_label.setText("Path not found")
            return

        path, steps = result
        self.current_path = path
        self.current_path_id = path_id

        # Update header
        self.title_label.setText(path.title)
        self.category_label.setText(f"Category: {path.category or 'None'}")
        self.tags_label.setText(f"Tags: {path.tags or 'None'}")
        self.description_label.setMarkdown(path.description or "")
        self.description_label.setVisible(bool(path.description))

        # Show/hide edit button based on creator
        is_creator = (path.creator == self.current_user) if self.current_user else True
        self.edit_btn.setVisible(is_creator)

        # Clear existing steps
        self._clear_steps()

        # Add step cards
        if steps:
            for step in steps:
                step_card = ReaderStepCard(step)
                self.steps_container.insertWidget(self.steps_container.count() - 1, step_card)
        else:
            empty_label = QLabel("This path has no steps yet.")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #666; font-size: 14px; padding: 40px;")
            self.steps_container.insertWidget(0, empty_label)

    def _clear_steps(self):
        """Remove all step cards"""
        while self.steps_container.count() > 1:
            item = self.steps_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_exit(self):
        """Handle exit button"""
        self.exit_clicked.emit()

    def _on_edit(self):
        """Handle edit button"""
        if self.current_path_id:
            self.edit_clicked.emit(self.current_path_id)
