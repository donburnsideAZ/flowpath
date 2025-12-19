from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QCursor, QPainter, QColor, QFont

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
COLOR_MAIN_BG = "#FFFFFF"  # Clean white background


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

        self.setStyleSheet("""
            ReaderStepCard {
                background-color: white;
                border: none;
                margin: 0px;
                padding: 0px;
            }
        """)

        # Horizontal layout - image left, content right
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(24)

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
                image_label.setStyleSheet("""
                    background-color: white;
                    border: none;
                    padding: 0px;
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
        content_layout.setSpacing(10)

        # Step header (H2 equivalent)
        step_label = QLabel(f"Step {step.step_number}")
        step_label.setStyleSheet("""
            color: #333;
            background: transparent;
            padding: 0px;
            margin: 0px;
        """)
        step_header_font = QFont()
        step_header_font.setPixelSize(18)
        step_header_font.setBold(True)
        step_label.setFont(step_header_font)
        content_layout.addWidget(step_label)

        # Instructions (body text - 14px)
        if step.instructions:
            instructions_label = MarkdownLabel()
            instructions_label.setMarkdown(step.instructions)
            instructions_label.setStyleSheet("""
                color: #444; 
                background: transparent;
            """)
            body_font = QFont()
            body_font.setPixelSize(14)
            instructions_label.setFont(body_font)
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
            border: none;
            color: {COLOR_TEXT_SECONDARY};
        """)
        placeholder_font = QFont()
        placeholder_font.setPixelSize(14)
        placeholder.setFont(placeholder_font)
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

        # === HEADER BAR ===
        header_widget = QWidget()
        header_widget.setStyleSheet(f"background-color: {COLOR_CARD_BG};")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(24, 16, 24, 16)
        header_layout.setSpacing(8)

        # Row 1: Back button and Title
        title_row = QHBoxLayout()
        
        self.exit_btn = QPushButton("← Back")
        self.exit_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: none;
                padding: 6px 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #333;
            }
        """)
        self.exit_btn.clicked.connect(self._on_exit)
        title_row.addWidget(self.exit_btn)
        
        title_row.addSpacing(8)
        
        self.title_label = QLabel("Path Title")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        self.title_label.setTextFormat(Qt.TextFormat.PlainText)
        title_row.addWidget(self.title_label)
        
        title_row.addStretch()
        header_layout.addLayout(title_row)

        # Row 2: Description
        self.description_label = MarkdownLabel()
        self.description_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY};")
        desc_font = QFont()
        desc_font.setPixelSize(14)
        self.description_label.setFont(desc_font)
        header_layout.addWidget(self.description_label)

        # Row 3: Category and Tags
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(4)
        
        body_font = QFont()
        body_font.setPixelSize(14)
        
        body_font_bold = QFont()
        body_font_bold.setPixelSize(14)
        body_font_bold.setBold(True)

        cat_prefix = QLabel("Category:")
        cat_prefix.setStyleSheet("color: #333;")
        cat_prefix.setFont(body_font_bold)
        meta_layout.addWidget(cat_prefix)
        
        self.category_label = QPushButton("")
        self.category_label.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLOR_TEXT_SECONDARY};
                border: none;
                text-align: left;
                padding: 0px 4px;
            }}
            QPushButton:hover {{
                color: {COLOR_PRIMARY_GREEN};
            }}
        """)
        self.category_label.setFont(body_font)
        self.category_label.setCursor(Qt.CursorShape.PointingHandCursor)
        meta_layout.addWidget(self.category_label)

        meta_layout.addSpacing(20)

        tags_prefix = QLabel("Tags:")
        tags_prefix.setStyleSheet("color: #333;")
        tags_prefix.setFont(body_font_bold)
        meta_layout.addWidget(tags_prefix)
        
        self.tags_label = QPushButton("")
        self.tags_label.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLOR_TAG_BLUE};
                border: none;
                text-align: left;
                padding: 0px 4px;
            }}
            QPushButton:hover {{
                color: {COLOR_PRIMARY_GREEN};
            }}
        """)
        self.tags_label.setFont(body_font)
        self.tags_label.setCursor(Qt.CursorShape.PointingHandCursor)
        meta_layout.addWidget(self.tags_label)

        meta_layout.addStretch()
        header_layout.addLayout(meta_layout)

        # Row 4: Action buttons
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(8)
        
        share_btn = QPushButton("Share")
        share_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLOR_TEXT_SECONDARY};
                border: 1px solid {COLOR_BORDER};
                padding: 6px 14px;
                border-radius: 4px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #f5f5f5;
            }}
        """)

        export_btn = QPushButton("Export")
        export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLOR_TEXT_SECONDARY};
                border: 1px solid {COLOR_BORDER};
                padding: 6px 14px;
                border-radius: 4px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #f5f5f5;
            }}
        """)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_EDIT_ORANGE};
                color: white;
                border: none;
                padding: 6px 18px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLOR_EDIT_ORANGE_HOVER};
            }}
        """)
        self.edit_btn.clicked.connect(self._on_edit)

        buttons_row.addWidget(share_btn)
        buttons_row.addWidget(export_btn)
        buttons_row.addWidget(self.edit_btn)
        buttons_row.addStretch()
        header_layout.addLayout(buttons_row)

        self.main_layout.addWidget(header_widget)

        # Separator line (90% width, centered, light gray)
        separator_layout = QHBoxLayout()
        separator_layout.setContentsMargins(0, 4, 0, 4)
        separator_layout.addStretch(1)  # 5% left
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #E8E8E8; max-height: 1px;")
        separator_layout.addWidget(separator, 18)  # 90% center
        separator_layout.addStretch(1)  # 5% right
        
        separator_container = QWidget()
        separator_container.setLayout(separator_layout)
        self.main_layout.addWidget(separator_container)

        # === STEPS AREA ===
        self.steps_container = QVBoxLayout()
        self.steps_container.setContentsMargins(24, 16, 24, 16)
        self.steps_container.setSpacing(0)
        self.steps_container.addStretch()

        steps_widget = QWidget()
        steps_widget.setLayout(self.steps_container)
        steps_widget.setStyleSheet("background-color: white;")

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(steps_widget)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
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
        self.category_label.setText(path.category or "None")
        self.tags_label.setText(path.tags or "None")
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
            empty_label.setStyleSheet("color: #666; padding: 40px;")
            empty_font = QFont()
            empty_font.setPixelSize(14)
            empty_label.setFont(empty_font)
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
