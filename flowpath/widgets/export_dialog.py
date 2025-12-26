"""
Export Dialog for FlowPath application.

Provides a dialog for selecting export format and destination.
"""

import os
from typing import List, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QFileDialog, QMessageBox,
    QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from ..models import Path, Step
from ..services import ExportService


# Style constants
COLOR_PRIMARY_GREEN = "#4CAF50"
COLOR_PRIMARY_GREEN_HOVER = "#45a049"
COLOR_TEXT_SECONDARY = "#666666"
COLOR_BORDER = "#E0E0E0"


class ExportWorker(QThread):
    """Background worker for export operations."""
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(
        self,
        export_format: str,
        path: Path,
        steps: List[Step],
        output_path: str
    ):
        super().__init__()
        self.export_format = export_format
        self.path = path
        self.steps = steps
        self.output_path = output_path

    def run(self):
        try:
            if self.export_format == 'json':
                success = ExportService.export_json(
                    self.path, self.steps, self.output_path,
                    embed_images=True
                )
            elif self.export_format == 'html':
                success = ExportService.export_html(
                    self.path, self.steps, self.output_path
                )
            elif self.export_format == 'pdf':
                success = ExportService.export_pdf(
                    self.path, self.steps, self.output_path
                )
            else:
                success = False

            if success:
                self.finished.emit(True, f"Exported successfully to:\n{self.output_path}")
            else:
                self.finished.emit(False, "Export failed. Please try again.")
        except Exception as e:
            self.finished.emit(False, f"Export error: {str(e)}")


class ExportDialog(QDialog):
    """Dialog for exporting a path to various formats."""

    def __init__(self, path: Path, steps: List[Step], parent=None):
        super().__init__(parent)
        self.path = path
        self.steps = steps
        self.worker: Optional[ExportWorker] = None

        self.setWindowTitle("Export Path")
        self.setMinimumWidth(400)
        self.setModal(True)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QLabel(f"Export: {self.path.title}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {COLOR_BORDER};")
        layout.addWidget(sep)

        # Format selection
        format_label = QLabel("Select export format:")
        format_label.setStyleSheet("font-size: 14px; color: #333; font-weight: 600;")
        layout.addWidget(format_label)

        self.format_group = QButtonGroup(self)

        # JSON option
        self.json_radio = QRadioButton("JSON")
        self.json_radio.setStyleSheet("font-size: 14px;")
        json_desc = QLabel("Full data export with embedded images. Can be re-imported.")
        json_desc.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SECONDARY}; margin-left: 24px;")
        json_desc.setWordWrap(True)

        # HTML option
        self.html_radio = QRadioButton("HTML")
        self.html_radio.setStyleSheet("font-size: 14px;")
        self.html_radio.setChecked(True)
        html_desc = QLabel("Self-contained web page. Opens in any browser, easy to share.")
        html_desc.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SECONDARY}; margin-left: 24px;")
        html_desc.setWordWrap(True)

        # PDF option
        self.pdf_radio = QRadioButton("PDF")
        self.pdf_radio.setStyleSheet("font-size: 14px;")
        pdf_desc = QLabel("Print-ready document. Best for documentation and archiving.")
        pdf_desc.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SECONDARY}; margin-left: 24px;")
        pdf_desc.setWordWrap(True)

        self.format_group.addButton(self.json_radio)
        self.format_group.addButton(self.html_radio)
        self.format_group.addButton(self.pdf_radio)

        layout.addWidget(self.json_radio)
        layout.addWidget(json_desc)
        layout.addSpacing(8)
        layout.addWidget(self.html_radio)
        layout.addWidget(html_desc)
        layout.addSpacing(8)
        layout.addWidget(self.pdf_radio)
        layout.addWidget(pdf_desc)

        layout.addSpacing(8)

        # Progress bar (hidden initially)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate
        self.progress.setVisible(False)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                height: 8px;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_PRIMARY_GREEN};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.progress)

        # Status label (hidden initially)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"font-size: 13px; color: {COLOR_TEXT_SECONDARY};")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                color: #333;
                border: 1px solid {COLOR_BORDER};
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #f5f5f5;
            }}
        """)
        self.cancel_btn.clicked.connect(self.reject)

        self.export_btn = QPushButton("Export")
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_PRIMARY_GREEN};
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLOR_PRIMARY_GREEN_HOVER};
            }}
            QPushButton:disabled {{
                background-color: #ccc;
            }}
        """)
        self.export_btn.clicked.connect(self.do_export)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.export_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_selected_format(self) -> str:
        """Return the selected export format."""
        if self.json_radio.isChecked():
            return 'json'
        elif self.html_radio.isChecked():
            return 'html'
        elif self.pdf_radio.isChecked():
            return 'pdf'
        return 'html'

    def do_export(self):
        """Handle export button click."""
        export_format = self.get_selected_format()

        # Get file extension info
        format_info = {
            'json': ('JSON Files (*.json)', 'json'),
            'html': ('HTML Files (*.html)', 'html'),
            'pdf': ('PDF Files (*.pdf)', 'pdf'),
        }
        filter_str, ext = format_info[export_format]
        suggested_name = ExportService.get_suggested_filename(self.path, ext)

        # Show save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Path",
            suggested_name,
            filter_str
        )

        if not file_path:
            return  # User cancelled

        # Ensure correct extension
        if not file_path.lower().endswith(f'.{ext}'):
            file_path += f'.{ext}'

        # Show progress
        self.progress.setVisible(True)
        self.status_label.setText("Exporting...")
        self.status_label.setVisible(True)
        self.export_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)

        # Disable format selection
        self.json_radio.setEnabled(False)
        self.html_radio.setEnabled(False)
        self.pdf_radio.setEnabled(False)

        # Run export in background
        self.worker = ExportWorker(export_format, self.path, self.steps, file_path)
        self.worker.finished.connect(self._on_export_finished)
        self.worker.start()

    def _on_export_finished(self, success: bool, message: str):
        """Handle export completion."""
        self.progress.setVisible(False)
        self.status_label.setVisible(False)
        self.export_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.json_radio.setEnabled(True)
        self.html_radio.setEnabled(True)
        self.pdf_radio.setEnabled(True)

        if success:
            QMessageBox.information(self, "Export Complete", message)
            self.accept()
        else:
            QMessageBox.warning(self, "Export Failed", message)
