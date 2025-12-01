"""Path reader screen - view workflow paths in read-only mode."""

import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap

from ..models import Path, Step
from ..storage import DataStore
from .. import styles


class ReaderStepCard(QFrame):
    """A step displayed in read-only mode."""

    def __init__(self, step_number: int, step: Step):
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

        # Screenshot area
        screenshot_label = QLabel()
        screenshot_label.setFixedSize(200, 140)
        screenshot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if step.screenshot_path and os.path.exists(step.screenshot_path):
            # Load and display the actual screenshot
            pixmap = QPixmap(step.screenshot_path)
            scaled = pixmap.scaled(
                200, 140,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            screenshot_label.setPixmap(scaled)
            screenshot_label.setStyleSheet("border: 2px solid #ccc; border-radius: 4px;")
        else:
            # Show placeholder
            screenshot_label.setText(f"Step {step_number}")
            screenshot_label.setStyleSheet("""
                background-color: #f0f0f0;
                border: 2px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
                color: #666;
            """)

        # Step content
        content_layout = QVBoxLayout()

        step_label = QLabel(f"Step {step_number}")
        step_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #333;")

        instructions_label = QLabel(step.instructions)
        instructions_label.setWordWrap(True)
        instructions_label.setStyleSheet("font-size: 14px; color: #444; padding: 10px 0;")

        content_layout.addWidget(step_label)
        content_layout.addWidget(instructions_label)
        content_layout.addStretch()

        layout.addWidget(screenshot_label)
        layout.addLayout(content_layout)
        layout.addStretch()

        self.setLayout(layout)


class PathReaderScreen(QWidget):
    """Screen for viewing paths in read-only mode."""
    exit_requested = pyqtSignal()  # Return to home
    edit_requested = pyqtSignal(str)  # Edit path (emits path_id)

    def __init__(self):
        super().__init__()
        self.data_store = DataStore()
        self.current_path = None
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # === TOP BAR ===
        top_bar = QHBoxLayout()

        # Path title
        self.title_label = QLabel("Path Title")
        self.title_label.setStyleSheet("font-size: 22px; font-weight: bold;")
        top_bar.addWidget(self.title_label)

        top_bar.addStretch()

        # Action buttons
        share_btn = QPushButton("Share")
        share_btn.setStyleSheet(styles.BUTTON_SECONDARY)
        share_btn.clicked.connect(self._on_share)

        export_btn = QPushButton("Export")
        export_btn.setStyleSheet(styles.BUTTON_SECONDARY)
        export_btn.clicked.connect(self._on_export)

        print_btn = QPushButton("Print")
        print_btn.setStyleSheet(styles.BUTTON_SECONDARY)
        print_btn.clicked.connect(self._on_print)

        self.exit_btn = QPushButton("Exit")
        self.exit_btn.setStyleSheet(styles.BUTTON_NEUTRAL)
        self.exit_btn.clicked.connect(self._on_exit)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setStyleSheet(styles.BUTTON_PRIMARY)
        self.edit_btn.clicked.connect(self._on_edit)

        top_bar.addWidget(share_btn)
        top_bar.addWidget(export_btn)
        top_bar.addWidget(print_btn)
        top_bar.addWidget(self.exit_btn)
        top_bar.addWidget(self.edit_btn)

        main_layout.addLayout(top_bar)
        main_layout.addSpacing(10)

        # === PATH METADATA ===
        meta_layout = QHBoxLayout()

        self.category_label = QLabel("Category: ")
        self.category_label.setStyleSheet(styles.LABEL_MUTED)

        self.tags_label = QLabel("Tags: ")
        self.tags_label.setStyleSheet(styles.LABEL_LINK)

        meta_layout.addWidget(self.category_label)
        meta_layout.addSpacing(30)
        meta_layout.addWidget(self.tags_label)
        meta_layout.addStretch()

        main_layout.addLayout(meta_layout)

        # === DESCRIPTION ===
        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("color: #555; font-size: 13px; padding: 10px 0;")
        main_layout.addWidget(self.description_label)

        main_layout.addSpacing(10)

        # === STEPS AREA ===
        self.steps_container = QVBoxLayout()
        self.steps_container.setAlignment(Qt.AlignmentFlag.AlignTop)

        steps_widget = QWidget()
        steps_widget.setLayout(self.steps_container)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(steps_widget)
        self.scroll_area.setStyleSheet(styles.SCROLL_AREA)

        main_layout.addWidget(self.scroll_area)

        self.setLayout(main_layout)

    def load_path(self, path_id: str):
        """Load a path for viewing."""
        self.current_path = self.data_store.get_path(path_id)
        if self.current_path:
            self._populate_view()
        else:
            QMessageBox.warning(self, "Error", "Path not found.")

    def _populate_view(self):
        """Populate the view with path data."""
        if not self.current_path:
            return

        self.title_label.setText(self.current_path.title)
        self.category_label.setText(f"Category: {self.current_path.category or 'None'}")
        self.tags_label.setText(f"Tags: {self.current_path.get_tags_string() or 'None'}")
        self.description_label.setText(self.current_path.description)

        # Show/hide edit button based on creator status
        self.edit_btn.setVisible(self.current_path.is_creator)

        # Clear existing step cards
        self._clear_steps()

        # Add step cards
        for i, step in enumerate(self.current_path.steps, 1):
            card = ReaderStepCard(i, step)
            self.steps_container.addWidget(card)

    def _clear_steps(self):
        """Remove all step cards."""
        while self.steps_container.count():
            item = self.steps_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_share(self):
        """Handle share button click."""
        QMessageBox.information(
            self, "Share",
            "Share functionality coming soon!\n\n"
            "This will allow you to share paths with teammates."
        )

    def _on_export(self):
        """Handle export button click."""
        QMessageBox.information(
            self, "Export",
            "Export functionality coming soon!\n\n"
            "This will allow you to export paths as PDF or HTML."
        )

    def _on_print(self):
        """Handle print button click."""
        QMessageBox.information(
            self, "Print",
            "Print functionality coming soon!\n\n"
            "This will allow you to print paths."
        )

    def _on_exit(self):
        """Return to home screen."""
        self.exit_requested.emit()

    def _on_edit(self):
        """Edit the current path."""
        if self.current_path:
            self.edit_requested.emit(self.current_path.path_id)
