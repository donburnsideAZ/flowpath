from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..database import get_database
from ..models import Path, Step
from ..export import PathExporter


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

        # Screenshot placeholder
        screenshot = QLabel(f"Screenshot {step.step_number}")
        screenshot.setFixedSize(200, 140)
        screenshot.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if step.screenshot_path:
            screenshot.setStyleSheet("""
                background-color: #e8f5e9;
                border: 2px solid #4CAF50;
                border-radius: 4px;
                font-size: 14px;
                color: #333;
            """)
            # Future: Load actual screenshot image
        else:
            screenshot.setStyleSheet("""
                background-color: #f0f0f0;
                border: 2px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
                color: #666;
            """)

        # Step content
        content_layout = QVBoxLayout()

        step_label = QLabel(f"Step {step.step_number}")
        step_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #333;")

        instructions_label = QLabel(step.instructions or "No instructions provided.")
        instructions_label.setWordWrap(True)
        instructions_label.setStyleSheet("font-size: 14px; color: #444; padding: 10px 0;")

        content_layout.addWidget(step_label)
        content_layout.addWidget(instructions_label)
        content_layout.addStretch()

        layout.addWidget(screenshot)
        layout.addLayout(content_layout)
        layout.addStretch()

        self.setLayout(layout)


class PathReaderScreen(QWidget):
    edit_requested = pyqtSignal(int)  # Emits path_id
    exit_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
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
        export_btn.clicked.connect(self._on_export)

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

        main_layout.addLayout(top_bar)
        main_layout.addSpacing(10)

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

        main_layout.addLayout(meta_layout)

        # Description
        self.description_label = QLabel("")
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("color: #444; font-size: 13px; padding: 10px 0;")
        main_layout.addWidget(self.description_label)

        main_layout.addSpacing(10)

        # === STEPS AREA ===
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
                background-color: #fafafa;
            }
        """)

        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)

    def load_path(self, path_id: int):
        """Load a path for viewing."""
        db = get_database()
        self.current_path = db.get_path(path_id)

        if not self.current_path:
            return

        # Update UI
        self.title_label.setText(self.current_path.title or "Untitled")
        self.category_label.setText(f"Category: {self.current_path.category or 'None'}")
        self.tags_label.setText(f"Tags: {self.current_path.tags or 'None'}")
        self.description_label.setText(self.current_path.description or "")

        # Clear and reload steps
        self._clear_steps()
        for step in self.current_path.steps:
            step_card = ReaderStepCard(step)
            self.steps_container.addWidget(step_card)

        # Show message if no steps
        if not self.current_path.steps:
            no_steps_label = QLabel("This path has no steps yet.")
            no_steps_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_steps_label.setStyleSheet("color: #666; font-size: 14px; padding: 40px;")
            self.steps_container.addWidget(no_steps_label)

    def _clear_steps(self):
        """Remove all step cards."""
        while self.steps_container.count():
            item = self.steps_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_edit(self):
        """Handle edit button click."""
        if self.current_path and self.current_path.id:
            self.edit_requested.emit(self.current_path.id)

    def _on_exit(self):
        """Handle exit button click."""
        self.exit_requested.emit()

    def _on_export(self):
        """Export the current path to JSON."""
        if not self.current_path:
            return

        # Ask user for export location
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Export Folder",
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if folder:
            try:
                file_path = PathExporter.export_path(self.current_path, folder)
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Path exported to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Export Failed",
                    f"Failed to export path:\n{str(e)}"
                )
