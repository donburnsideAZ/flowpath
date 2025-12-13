from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QCursor, QPainter, QColor

from ..services import DataService
from ..models import Path, Step
from ..widgets import MarkdownLabel

# Color constants (matching home screen)
COLOR_PRIMARY_GREEN = "#4CAF50"
COLOR_PRIMARY_GREEN_HOVER = "#45a049"
COLOR_EDIT_ORANGE = "#E67E22"
COLOR_EDIT_ORANGE_HOVER = "#D35400"
COLOR_TEXT_SECONDARY = "#666666"
COLOR_TAG_BLUE = "#1976D2"
COLOR_BORDER = "#E0E0E0"
COLOR_CARD_BG = "#FFFFFF"
COLOR_MAIN_BG = "#EAEFF2"


class ImageLightbox(QWidget):
    """In-window overlay to display an image. Click anywhere to close."""
    
    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        
        # Fill the parent widget
        if parent:
            self.setGeometry(parent.rect())
        
        # Image to display
        self.pixmap = pixmap
        
        # Make clickable
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Calculate scaled image size (max 800px wide, keep aspect ratio)
        max_width = 800
        max_height = 600
        self.scaled_pixmap = pixmap.scaled(
            max_width, max_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    
    def paintEvent(self, event):
        """Custom paint to draw overlay and image"""
        painter = QPainter(self)
        
        # Dark semi-transparent overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 180))
        
        # Calculate centered position for image
        img_width = self.scaled_pixmap.width()
        img_height = self.scaled_pixmap.height()
        x = (self.width() - img_width) // 2
        y = (self.height() - img_height) // 2
        
        # White background/border for image
        padding = 12
        painter.fillRect(
            x - padding, y - padding,
            img_width + padding * 2, img_height + padding * 2,
            QColor(255, 255, 255)
        )
        
        # Draw the image
        painter.drawPixmap(x, y, self.scaled_pixmap)
        
        # Hint text at bottom
        painter.setPen(QColor(255, 255, 255))
        hint_rect = self.rect()
        hint_rect.setTop(y + img_height + padding + 20)
        painter.drawText(hint_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, 
                        "Click anywhere to close")
    
    def mousePressEvent(self, event):
        """Close on any click"""
        self.close()
        self.deleteLater()
    
    def keyPressEvent(self, event):
        """Close on Escape key"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            self.deleteLater()


class ClickableImageLabel(QLabel):
    """A QLabel that emits clicked signal and shows pointer cursor"""
    clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    
    def mousePressEvent(self, event):
        self.clicked.emit()


class ReaderStepCard(QFrame):
    """A step displayed in read-only mode with image left, text right"""

    def __init__(self, step: Step):
        super().__init__()
        self.step = step
        self.full_pixmap = None  # Store full-size image for lightbox

        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet(f"""
            ReaderStepCard {{
                background-color: {COLOR_CARD_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                margin: 4px 0px;
            }}
        """)

        # Horizontal layout - image left, content right
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # Screenshot - moderate size on left
        if step.screenshot_path:
            self.full_pixmap = QPixmap(step.screenshot_path)
            if not self.full_pixmap.isNull():
                image_label = ClickableImageLabel()
                image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Scale to comfortable size - bigger than thumbnail, smaller than full
                max_width = 340
                max_height = 240
                scaled_pixmap = self.full_pixmap.scaled(
                    max_width, max_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                image_label.setPixmap(scaled_pixmap)
                # Fixed width container for consistent alignment
                image_label.setFixedWidth(360)
                image_label.setStyleSheet(f"""
                    background-color: white;
                    border: 1px solid {COLOR_BORDER};
                    border-radius: 4px;
                    padding: 8px;
                """)
                image_label.setToolTip("Click to enlarge")
                image_label.clicked.connect(self._show_lightbox)
                layout.addWidget(image_label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            else:
                self._add_placeholder(layout)
        else:
            self._add_placeholder(layout)

        # Content on right
        content_layout = QVBoxLayout()
        content_layout.setSpacing(8)

        # Step header
        step_label = QLabel(f"Step {step.step_number}")
        step_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 16px; 
            color: #333;
            background: transparent;
        """)
        content_layout.addWidget(step_label)

        # Instructions
        if step.instructions:
            instructions_label = MarkdownLabel()
            instructions_label.setMarkdown(step.instructions)
            instructions_label.setStyleSheet("""
                font-size: 14px; 
                color: #444; 
                background: transparent;
            """)
            instructions_label.setWordWrap(True)
            content_layout.addWidget(instructions_label)

        content_layout.addStretch()
        layout.addLayout(content_layout, 1)  # Give text area stretch priority

        self.setLayout(layout)

    def _add_placeholder(self, layout):
        """Add a placeholder for steps without screenshots"""
        placeholder = QLabel("No screenshot")
        placeholder.setFixedSize(360, 120)
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet(f"""
            background-color: #f5f5f5;
            border: 2px dashed {COLOR_BORDER};
            border-radius: 4px;
            font-size: 12px;
            color: {COLOR_TEXT_SECONDARY};
        """)
        layout.addWidget(placeholder, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

    def _show_lightbox(self):
        """Show the full-size image in a lightbox overlay"""
        if self.full_pixmap and not self.full_pixmap.isNull():
            # Find the top-level window to overlay on
            main_window = self.window()
            lightbox = ImageLightbox(self.full_pixmap, main_window)
            lightbox.setGeometry(main_window.rect())
            lightbox.show()
            lightbox.raise_()
            lightbox.setFocus()


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
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # === HEADER BAR (white background) ===
        header_widget = QWidget()
        header_widget.setStyleSheet(f"background-color: {COLOR_CARD_BG}; border-bottom: 1px solid {COLOR_BORDER};")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(24, 16, 24, 16)
        header_layout.setSpacing(8)

        # Top row with title and buttons
        top_bar = QHBoxLayout()

        # Path title
        self.title_label = QLabel("Path Title")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        top_bar.addWidget(self.title_label)

        top_bar.addStretch()

        # Action buttons
        share_btn = QPushButton("Share")
        share_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_PRIMARY_GREEN};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLOR_PRIMARY_GREEN_HOVER};
            }}
        """)

        export_btn = QPushButton("Export")
        export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_PRIMARY_GREEN};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLOR_PRIMARY_GREEN_HOVER};
            }}
        """)

        print_btn = QPushButton("Print")
        print_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_PRIMARY_GREEN};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLOR_PRIMARY_GREEN_HOVER};
            }}
        """)

        self.exit_btn = QPushButton("Exit")
        self.exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        self.exit_btn.clicked.connect(self._on_exit)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_EDIT_ORANGE};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLOR_EDIT_ORANGE_HOVER};
            }}
        """)
        self.edit_btn.clicked.connect(self._on_edit)

        top_bar.addWidget(share_btn)
        top_bar.addWidget(export_btn)
        top_bar.addWidget(print_btn)
        top_bar.addWidget(self.exit_btn)
        top_bar.addWidget(self.edit_btn)

        header_layout.addLayout(top_bar)

        # === PATH METADATA ===
        meta_layout = QHBoxLayout()

        self.category_label = QLabel("Category: ")
        self.category_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 13px;")

        self.tags_label = QLabel("Tags: ")
        self.tags_label.setStyleSheet(f"color: {COLOR_TAG_BLUE}; font-size: 13px;")

        meta_layout.addWidget(self.category_label)
        meta_layout.addSpacing(20)
        meta_layout.addWidget(self.tags_label)
        meta_layout.addStretch()

        header_layout.addLayout(meta_layout)

        # Description (renders Markdown)
        self.description_label = MarkdownLabel()
        self.description_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 13px;")
        header_layout.addWidget(self.description_label)

        self.main_layout.addWidget(header_widget)

        # === STEPS AREA (blue-gray background) ===
        self.steps_container = QVBoxLayout()
        self.steps_container.setContentsMargins(24, 16, 24, 16)
        self.steps_container.setSpacing(8)
        self.steps_container.addStretch()

        steps_widget = QWidget()
        steps_widget.setLayout(self.steps_container)
        steps_widget.setStyleSheet(f"background-color: {COLOR_MAIN_BG};")

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(steps_widget)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {COLOR_MAIN_BG};
            }}
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
