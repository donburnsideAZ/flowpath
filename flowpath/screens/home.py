"""
Home Screen for FlowPath application.

Displays the library of FlowPath paths and legacy documents with filtering options.
"""

import subprocess
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QListWidget, QGridLayout,
    QFrame, QScrollArea, QListWidgetItem,
    QMessageBox, QProgressDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ..services import DataService, LegacyConverter
from ..models import Path, LegacyDocument


# Color constants
COLOR_PRIMARY_GREEN = "#4CAF50"
COLOR_PRIMARY_GREEN_HOVER = "#45a049"
COLOR_EDIT_ORANGE = "#E67E22"
COLOR_EDIT_ORANGE_HOVER = "#D35400"
COLOR_LEGACY_BORDER = "#9E9E9E"
COLOR_LEGACY_BADGE = "#757575"
COLOR_TEXT_SECONDARY = "#666666"
COLOR_TEXT_MUTED = "#999999"
COLOR_TAG_BLUE = "#1976D2"
COLOR_BORDER = "#E0E0E0"
COLOR_CARD_BG = "#FFFFFF"
COLOR_HOVER_BG = "#F5F5F5"
COLOR_MAIN_BG = "#FFFFFF"  # Clean white background


class PathListRow(QFrame):
    """A list row displaying a FlowPath path."""
    clicked = pyqtSignal(int)  # Emits path_id when clicked

    def __init__(self, path: Path, step_count: int = 0, current_user: str = ""):
        super().__init__()
        self.path_id = path.id
        self.step_count = step_count

        self.setObjectName("PathListRow")
        self.setStyleSheet(f"""
            #PathListRow {{
                background-color: transparent;
                border: none;
                border-bottom: 1px solid #F0F0F0;
                margin: 0px;
                padding: 0px;
            }}
            #PathListRow:hover {{
                background-color: {COLOR_HOVER_BG};
            }}
        """)
        self.setFixedHeight(48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Title (main content - takes most space, with elide for long text)
        title_label = QLabel(path.title)
        title_label.setStyleSheet("""
            font-size: 14px;
            color: #333333;
            background: transparent;
        """)
        title_label.setMinimumWidth(100)
        layout.addWidget(title_label, 1)  # stretch factor 1

        # Category (simple text, no background)
        if path.category:
            category_label = QLabel(path.category)
            category_label.setStyleSheet(f"""
                color: {COLOR_TEXT_SECONDARY};
                font-size: 14px;
                background: transparent;
            """)
            layout.addWidget(category_label)

        # Step count (simple text, no background shape)
        if step_count > 0:
            step_label = QLabel(f"{step_count} step{'s' if step_count != 1 else ''}")
            step_label.setStyleSheet(f"""
                color: {COLOR_PRIMARY_GREEN};
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            """)
            layout.addWidget(step_label)

        self.setLayout(layout)

    def mousePressEvent(self, event):
        """Handle click on the row."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.path_id)


class LegacyDocListRow(QFrame):
    """A list row displaying a legacy document."""
    clicked = pyqtSignal(str)  # Emits filepath when clicked
    convert_clicked = pyqtSignal(str)  # Emits filepath when convert clicked

    # File type colors (MS Office style)
    TYPE_COLORS = {
        'word': '#2B579A',       # Word blue
        'pdf': '#D32F2F',        # PDF red
        'powerpoint': '#D24726', # PowerPoint orange
        'excel': '#217346',      # Excel green
        'text': '#757575',       # Text gray
        'html': '#E44D26',       # HTML orange
        'pages': '#FF9500',      # Pages orange
        'numbers': '#00A650',    # Numbers green
        'keynote': '#007AFF',    # Keynote blue
    }
    
    # Types that can be converted to FlowPath
    CONVERTIBLE_TYPES = {'word', 'powerpoint', 'text'}

    def __init__(self, doc: LegacyDocument):
        super().__init__()
        self.filepath = doc.filepath
        self.doc = doc
        self.is_convertible = doc.file_type in self.CONVERTIBLE_TYPES

        self.setObjectName("LegacyDocListRow")
        self.setStyleSheet(f"""
            #LegacyDocListRow {{
                background-color: transparent;
                border: none;
                border-bottom: 1px solid #F0F0F0;
                margin: 0px;
                padding: 0px;
            }}
            #LegacyDocListRow:hover {{
                background-color: {COLOR_HOVER_BG};
            }}
        """)
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Filename (main content - takes most space)
        filename_label = QLabel(doc.filename)
        filename_label.setStyleSheet("""
            font-size: 14px;
            color: #333333;
            background: transparent;
        """)
        filename_label.setMinimumWidth(100)
        filename_label.setMaximumWidth(400)
        layout.addWidget(filename_label, 1)  # stretch factor 1

        # File type label
        type_label = QLabel(doc.type_label)
        type_label.setStyleSheet(f"""
            color: {COLOR_TEXT_SECONDARY};
            font-size: 14px;
            background-color: #F0F0F0;
            padding: 2px 8px;
            border-radius: 7px;
        """)
        layout.addWidget(type_label)

        # Legacy badge
        legacy_badge = QLabel("LEGACY")
        legacy_badge.setStyleSheet(f"""
            background-color: {COLOR_LEGACY_BADGE};
            color: white;
            padding: 2px 8px;
            border-radius: 7px;
            font-size: 14px;
            font-weight: bold;
        """)
        layout.addWidget(legacy_badge)

        # Modified date
        modified_label = QLabel(doc.modified_display)
        modified_label.setStyleSheet(f"""
            color: {COLOR_TEXT_MUTED};
            font-size: 14px;
            background: transparent;
        """)
        modified_label.setFixedWidth(80)
        layout.addWidget(modified_label)

        # Convert button for convertible types
        if self.is_convertible:
            convert_btn = QPushButton("CONVERT")
            convert_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_PRIMARY_GREEN};
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 7px;
                }}
                QPushButton:hover {{
                    background-color: {COLOR_PRIMARY_GREEN_HOVER};
                }}
            """)
            convert_btn.setFixedWidth(65)
            convert_btn.clicked.connect(self._on_convert_clicked)
            layout.addWidget(convert_btn)

        self.setLayout(layout)

    def _on_convert_clicked(self):
        """Handle convert button click."""
        self.convert_clicked.emit(self.filepath)

    def mousePressEvent(self, event):
        """Handle click on the row."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.filepath)


# Keep the old card classes for potential future use but they won't be used
class PathCard(QFrame):
    """A polished card displaying a FlowPath path."""
    clicked = pyqtSignal(int)  # Emits path_id when clicked
    edit_clicked = pyqtSignal(int)  # Emits path_id when edit clicked

    def __init__(self, path: Path, step_count: int = 0, current_user: str = ""):
        super().__init__()
        self.path_id = path.id
        self.is_creator = (path.creator == current_user) if current_user else True
        self.step_count = step_count

        self.setObjectName("PathCard")
        self.setStyleSheet(f"""
            #PathCard {{
                background-color: {COLOR_CARD_BG};
                border: 2px solid {COLOR_BORDER};
                border-radius: 10px;
            }}
            #PathCard:hover {{
                border-color: {COLOR_PRIMARY_GREEN};
                background-color: {COLOR_HOVER_BG};
            }}
        """)
        self.setFixedSize(220, 180)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        # Preview area / icon placeholder (top section)
        preview_area = QFrame()
        preview_area.setFixedHeight(50)
        preview_area.setStyleSheet(f"""
            background-color: #E8F5E9;
            border-radius: 6px;
            border: 1px solid {COLOR_BORDER};
        """)
        preview_layout = QHBoxLayout(preview_area)
        preview_layout.setContentsMargins(8, 8, 8, 8)
        
        # FlowPath icon/indicator
        icon_label = QLabel("📋")
        icon_label.setStyleSheet("font-size: 24px; background: transparent; border: none;")
        preview_layout.addWidget(icon_label)
        preview_layout.addStretch()
        
        # Step count badge
        if step_count > 0:
            step_badge = QLabel(f"{step_count} step{'s' if step_count != 1 else ''}")
            step_badge.setStyleSheet(f"""
                background-color: {COLOR_PRIMARY_GREEN};
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            """)
            preview_layout.addWidget(step_badge)
        
        layout.addWidget(preview_area)

        # Title
        title_label = QLabel(path.title)
        title_label.setStyleSheet(f"""
            font-weight: bold;
            font-size: 14px;
            color: #333333;
            background: transparent;
        """)
        title_label.setWordWrap(True)
        title_label.setMaximumHeight(36)
        layout.addWidget(title_label)

        # Category
        if path.category:
            category_label = QLabel(path.category)
            category_label.setStyleSheet(f"""
                color: {COLOR_TEXT_SECONDARY};
                font-size: 14px;
                background: transparent;
            """)
            layout.addWidget(category_label)

        # Tags (truncated)
        if path.tags:
            tags_display = path.tags[:35] + "..." if len(path.tags) > 35 else path.tags
            tags_label = QLabel(tags_display)
            tags_label.setStyleSheet(f"""
                color: {COLOR_TAG_BLUE};
                font-size: 14px;
                background: transparent;
            """)
            layout.addWidget(tags_label)

        layout.addStretch()

        # Bottom row with edit button
        if self.is_creator:
            bottom_row = QHBoxLayout()
            bottom_row.addStretch()
            
            edit_btn = QPushButton("EDIT")
            edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_EDIT_ORANGE};
                    color: white;
                    border: none;
                    padding: 4px 12px;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: {COLOR_EDIT_ORANGE_HOVER};
                }}
            """)
            edit_btn.setFixedWidth(50)
            edit_btn.clicked.connect(self._on_edit_clicked)
            bottom_row.addWidget(edit_btn)
            
            layout.addLayout(bottom_row)

        self.setLayout(layout)

    def _on_edit_clicked(self):
        """Handle edit button click."""
        self.edit_clicked.emit(self.path_id)

    def mousePressEvent(self, event):
        """Handle click on the card."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.path_id)


class LegacyDocCard(QFrame):
    """A card displaying a legacy document."""
    clicked = pyqtSignal(str)  # Emits filepath when clicked
    convert_clicked = pyqtSignal(str)  # Emits filepath when convert clicked

    # File type icons
    TYPE_ICONS = {
        'word': '📄',
        'pdf': '📕',
        'powerpoint': '📊',
        'excel': '📗',
        'text': '📝',
        'html': '🌐',
        'pages': '📄',
        'numbers': '📗',
        'keynote': '📊',
    }
    
    # Types that can be converted to FlowPath
    CONVERTIBLE_TYPES = {'word', 'powerpoint', 'text'}

    def __init__(self, doc: LegacyDocument):
        super().__init__()
        self.filepath = doc.filepath
        self.doc = doc
        self.is_convertible = doc.file_type in self.CONVERTIBLE_TYPES

        self.setObjectName("LegacyDocCard")
        self.setStyleSheet(f"""
            #LegacyDocCard {{
                background-color: {COLOR_CARD_BG};
                border: 2px solid {COLOR_LEGACY_BORDER};
                border-radius: 10px;
            }}
            #LegacyDocCard:hover {{
                border-color: {COLOR_TAG_BLUE};
                background-color: {COLOR_HOVER_BG};
            }}
        """)
        self.setFixedSize(220, 180)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        # Preview area with file type icon
        preview_area = QFrame()
        preview_area.setFixedHeight(50)
        preview_area.setStyleSheet(f"""
            background-color: #F5F5F5;
            border-radius: 6px;
            border: 1px solid {COLOR_BORDER};
        """)
        preview_layout = QHBoxLayout(preview_area)
        preview_layout.setContentsMargins(8, 8, 8, 8)
        
        # File type icon
        icon = self.TYPE_ICONS.get(doc.file_type, '📄')
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px; background: transparent; border: none;")
        preview_layout.addWidget(icon_label)
        preview_layout.addStretch()
        
        # Legacy badge
        legacy_badge = QLabel("LEGACY")
        legacy_badge.setStyleSheet(f"""
            background-color: {COLOR_LEGACY_BADGE};
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: bold;
        """)
        preview_layout.addWidget(legacy_badge)
        
        layout.addWidget(preview_area)

        # Filename
        filename_label = QLabel(doc.filename)
        filename_label.setStyleSheet(f"""
            font-weight: bold;
            font-size: 14px;
            color: #333333;
            background: transparent;
        """)
        filename_label.setWordWrap(True)
        filename_label.setMaximumHeight(36)
        layout.addWidget(filename_label)

        # File type label
        type_label = QLabel(doc.type_label)
        type_label.setStyleSheet(f"""
            color: {COLOR_TEXT_SECONDARY};
            font-size: 14px;
            background: transparent;
        """)
        layout.addWidget(type_label)

        layout.addStretch()

        # Bottom row with info and convert button
        bottom_row = QHBoxLayout()
        
        modified_label = QLabel(doc.modified_display)
        modified_label.setStyleSheet(f"""
            color: {COLOR_TEXT_MUTED};
            font-size: 14px;
            background: transparent;
        """)
        bottom_row.addWidget(modified_label)
        
        bottom_row.addStretch()
        
        # Convert button for convertible types
        if self.is_convertible:
            convert_btn = QPushButton("CONVERT")
            convert_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_PRIMARY_GREEN};
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: {COLOR_PRIMARY_GREEN_HOVER};
                }}
            """)
            convert_btn.setFixedWidth(60)
            convert_btn.clicked.connect(self._on_convert_clicked)
            bottom_row.addWidget(convert_btn)
        else:
            # Just show size for non-convertible types
            size_label = QLabel(doc.size_display)
            size_label.setStyleSheet(f"""
                color: {COLOR_TEXT_MUTED};
                font-size: 14px;
                background: transparent;
            """)
            bottom_row.addWidget(size_label)
        
        layout.addLayout(bottom_row)

        self.setLayout(layout)

    def _on_convert_clicked(self):
        """Handle convert button click."""
        self.convert_clicked.emit(self.filepath)

    def mousePressEvent(self, event):
        """Handle click on the card - opens in default app."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.filepath)


class CollapsibleSection(QFrame):
    """A collapsible section with a header and content area."""

    def __init__(self, title: str, count: int = 0):
        super().__init__()
        self.is_collapsed = True  # Start collapsed
        self.count = count

        self.setObjectName("CollapsibleSection")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header (clickable)
        self.header = QFrame()
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header.setStyleSheet(f"""
            QFrame {{
                background-color: #F5F5F5;
                border: 1px solid {COLOR_BORDER};
                border-radius: 0px;
                padding: 8px 12px;
            }}
            QFrame:hover {{
                background-color: #EEEEEE;
            }}
        """)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(12, 8, 12, 8)

        # Arrow indicator
        self.arrow_label = QLabel(">")
        self.arrow_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-weight: bold; font-size: 14px;")
        self.arrow_label.setFixedWidth(16)
        header_layout.addWidget(self.arrow_label)

        # Title
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"font-size: 14px; color: {COLOR_TEXT_SECONDARY};")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # Count badge
        self.count_label = QLabel(f"{count}")
        self.count_label.setStyleSheet(f"""
            background-color: {COLOR_LEGACY_BADGE};
            color: white;
            padding: 2px 8px;
            border-radius: 7px;
            font-size: 14px;
            font-weight: bold;
        """)
        header_layout.addWidget(self.count_label)

        self.header.setLayout(header_layout)
        self.header.mousePressEvent = self._on_header_clicked

        main_layout.addWidget(self.header)

        # Content container (hidden by default)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 4, 0, 0)
        self.content_layout.setSpacing(4)
        self.content_widget.setLayout(self.content_layout)
        self.content_widget.hide()

        main_layout.addWidget(self.content_widget)

        self.setLayout(main_layout)

    def _on_header_clicked(self, event):
        """Toggle collapse state."""
        self.is_collapsed = not self.is_collapsed
        self.content_widget.setVisible(not self.is_collapsed)
        self.arrow_label.setText("v" if not self.is_collapsed else ">")

    def add_widget(self, widget):
        """Add a widget to the content area."""
        self.content_layout.addWidget(widget)

    def clear(self):
        """Clear all widgets from content area."""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def update_count(self, count: int):
        """Update the count badge."""
        self.count = count
        self.count_label.setText(f"{count}")


class HomeScreen(QWidget):
    """Main home screen showing library of paths and files."""
    path_clicked = pyqtSignal(int)  # Emits path_id
    new_path_requested = pyqtSignal()  # Emitted when New Path clicked

    def __init__(self):
        super().__init__()
        self.data_service = DataService.instance()
        self.current_user = ""  # Will be set by main window if needed
        self.current_filter_category = None
        self.current_filter_tag = None
        self.current_search = ""
        self.current_tab = "paths"  # "paths" or "files"
        self.setup_ui()

    def setup_ui(self):
        """Set up the home screen UI."""
        # Main horizontal layout: sidebar | content
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === LEFT SIDEBAR ===
        sidebar = QVBoxLayout()
        sidebar.setContentsMargins(16, 16, 16, 16)
        sidebar.setSpacing(12)

        # New Path button
        self.new_path_btn = QPushButton("+ New Path")
        self.new_path_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_PRIMARY_GREEN};
                color: white;
                border: none;
                padding: 14px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 7px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_PRIMARY_GREEN_HOVER};
            }}
        """)
        self.new_path_btn.clicked.connect(lambda: self.new_path_requested.emit())
        sidebar.addWidget(self.new_path_btn)

        # Spacer
        sidebar.addSpacing(20)

        # Category header
        cat_header = QLabel("Category")
        cat_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        sidebar.addWidget(cat_header)

        # Category list
        self.category_list = QListWidget()
        self.category_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 7px;
                background-color: white;
                font-size: 14px;
            }}
            QListWidget::item {{
                padding: 10px 12px;
                border-bottom: 1px solid #F0F0F0;
                font-size: 14px;
            }}
            QListWidget::item:last-child {{
                border-bottom: none;
            }}
            QListWidget::item:selected {{
                background-color: #E8F5E9;
                color: #333;
            }}
            QListWidget::item:hover {{
                background-color: #F5F5F5;
            }}
        """)
        self.category_list.setMaximumHeight(160)
        self.category_list.itemClicked.connect(self._on_category_clicked)
        sidebar.addWidget(self.category_list)

        # Clear filter button
        self.clear_category_btn = QPushButton("Clear Filter")
        self.clear_category_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #F5F5F5;
                border: 1px solid {COLOR_BORDER};
                padding: 6px 12px;
                font-size: 14px;
                border-radius: 7px;
                color: {COLOR_TEXT_SECONDARY};
            }}
            QPushButton:hover {{
                background-color: #EEEEEE;
            }}
        """)
        self.clear_category_btn.clicked.connect(self._clear_filters)
        self.clear_category_btn.hide()
        sidebar.addWidget(self.clear_category_btn)

        # Spacer
        sidebar.addSpacing(16)

        # Tags header
        tags_header = QLabel("Tags")
        tags_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        sidebar.addWidget(tags_header)

        # Tag list
        self.tag_list = QListWidget()
        self.tag_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 7px;
                background-color: white;
                font-size: 14px;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                color: {COLOR_TAG_BLUE};
                border-bottom: 1px solid #F0F0F0;
                font-size: 14px;
            }}
            QListWidget::item:last-child {{
                border-bottom: none;
            }}
            QListWidget::item:selected {{
                background-color: #E3F2FD;
            }}
            QListWidget::item:hover {{
                background-color: #F5F5F5;
            }}
        """)
        self.tag_list.setMaximumHeight(130)
        self.tag_list.itemClicked.connect(self._on_tag_clicked)
        sidebar.addWidget(self.tag_list)

        sidebar.addStretch()

        # Sidebar container
        sidebar_widget = QFrame()
        sidebar_widget.setLayout(sidebar)
        sidebar_widget.setFixedWidth(220)
        sidebar_widget.setStyleSheet(f"""
            QFrame {{
                background-color: #FAFAFA;
                border-right: 1px solid {COLOR_BORDER};
            }}
        """)

        # === MAIN CONTENT ===
        content = QVBoxLayout()
        content.setContentsMargins(24, 20, 24, 20)
        content.setSpacing(16)

        # Header row with team name
        header_row = QHBoxLayout()
        
        self.team_label = QLabel(self.data_service.get_team_name())
        self.team_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        header_row.addWidget(self.team_label)
        
        header_row.addStretch()
        content.addLayout(header_row)

        # Search and filter row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.setStyleSheet(f"""
            QLineEdit {{
                padding: 10px 16px;
                font-size: 14px;
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                background-color: white;
            }}
            QLineEdit:focus {{
                border-color: {COLOR_PRIMARY_GREEN};
            }}
        """)
        self.search_bar.textChanged.connect(self._on_search_changed)
        filter_row.addWidget(self.search_bar, stretch=1)

        content.addLayout(filter_row)

        # Tab bar for Paths / Files
        tab_row = QHBoxLayout()
        tab_row.setSpacing(0)
        
        self.paths_tab = QPushButton("Paths")
        self.paths_tab.setCheckable(True)
        self.paths_tab.setChecked(True)
        self.paths_tab.setStyleSheet(self._get_tab_style(True))
        self.paths_tab.clicked.connect(lambda: self._switch_tab("paths"))
        tab_row.addWidget(self.paths_tab)
        
        self.files_tab = QPushButton("Files")
        self.files_tab.setCheckable(True)
        self.files_tab.setChecked(False)
        self.files_tab.setStyleSheet(self._get_tab_style(False))
        self.files_tab.clicked.connect(lambda: self._switch_tab("files"))
        tab_row.addWidget(self.files_tab)
        
        tab_row.addStretch()
        
        # Count labels next to tabs
        self.paths_count_label = QLabel("")
        self.paths_count_label.setStyleSheet(f"font-size: 14px; color: {COLOR_TEXT_SECONDARY}; margin-left: 8px;")
        tab_row.addWidget(self.paths_count_label)
        
        content.addLayout(tab_row)

        # Filter indicator (shows active category/tag filter)
        self.filter_label = QLabel("")
        self.filter_label.setStyleSheet(f"font-size: 14px; color: {COLOR_TEXT_SECONDARY};")
        self.filter_label.hide()  # Only show when filtering
        content.addWidget(self.filter_label)

        # List scroll area (changed from grid to vertical list)
        self.cards_widget = QWidget()
        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(4)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_widget.setLayout(self.cards_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.cards_widget)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)

        content.addWidget(scroll_area)

        # Content container
        content_widget = QWidget()
        content_widget.setLayout(content)
        content_widget.setStyleSheet(f"background-color: {COLOR_MAIN_BG};")

        # === ASSEMBLE MAIN LAYOUT ===
        main_layout.addWidget(sidebar_widget)
        main_layout.addWidget(content_widget)

        self.setLayout(main_layout)

        # Initial load
        self.refresh()

    def refresh(self):
        """Refresh the entire screen with current data."""
        self.team_label.setText(self.data_service.get_team_name())
        self._load_categories()
        self._load_tags()
        self._load_content()

    def _get_tab_style(self, is_active: bool) -> str:
        """Get stylesheet for tab button based on active state."""
        if is_active:
            return f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLOR_PRIMARY_GREEN};
                    border: none;
                    border-bottom: 2px solid {COLOR_PRIMARY_GREEN};
                    padding: 8px 16px;
                    font-size: 14px;
                    font-weight: bold;
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLOR_TEXT_SECONDARY};
                    border: none;
                    border-bottom: 2px solid transparent;
                    padding: 8px 16px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    color: #333;
                }}
            """

    def _switch_tab(self, tab: str):
        """Switch between Paths and Files tabs."""
        self.current_tab = tab
        self.paths_tab.setChecked(tab == "paths")
        self.files_tab.setChecked(tab == "files")
        self.paths_tab.setStyleSheet(self._get_tab_style(tab == "paths"))
        self.files_tab.setStyleSheet(self._get_tab_style(tab == "files"))
        
        # Clear search and filters when switching tabs
        self.current_search = ""
        self.search_bar.clear()
        self._clear_filters()
        
        self._load_content()

    def _load_categories(self):
        """Load categories from database."""
        self.category_list.clear()
        categories = self.data_service.get_categories()
        if categories:
            for category in categories:
                self.category_list.addItem(category)
        else:
            # Show default categories if none exist
            self.category_list.addItems(["LMS", "Content Creation", "Admin", "Troubleshooting"])

    def _load_tags(self):
        """Load tags from database."""
        self.tag_list.clear()
        tags = self.data_service.get_all_tags()
        if tags:
            for tag in tags:
                self.tag_list.addItem(tag)
        else:
            # Show default tags if none exist
            self.tag_list.addItems(["authentication", "video", "setup", "troubleshooting"])

    def _load_content(self):
        """Load and display paths or files based on current tab and filters."""
        # Clear existing items
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Count both for the tab labels
        all_paths = self.data_service.get_all_paths()
        all_files = self.data_service.get_legacy_documents()
        self.paths_count_label.setText(f"{len(all_paths)} paths · {len(all_files)} files")

        # Show/hide clear filter button
        if self.current_filter_category or self.current_filter_tag or self.current_search:
            self.clear_category_btn.show()
            self.filter_label.show()
        else:
            self.clear_category_btn.hide()
            self.filter_label.hide()

        if self.current_tab == "paths":
            # Load paths
            if self.current_search:
                paths = self.data_service.search_paths(self.current_search)
                self.filter_label.setText(f'Search: "{self.current_search}" ({len(paths)} results)')
            elif self.current_filter_category:
                paths = self.data_service.get_paths_by_category(self.current_filter_category)
                self.filter_label.setText(f"Category: {self.current_filter_category}")
            elif self.current_filter_tag:
                paths = self.data_service.get_paths_by_tag(self.current_filter_tag)
                self.filter_label.setText(f"Tag: {self.current_filter_tag}")
            else:
                paths = all_paths

            # Add path rows
            for path in paths:
                step_count = self.data_service.count_steps(path.id) if path.id else 0
                row = PathListRow(path, step_count, self.current_user)
                row.clicked.connect(self._on_path_clicked)
                self.cards_layout.addWidget(row)

            # Empty state
            if not paths:
                self._show_empty_state("No paths found.\n\nClick '+ New Path' to create one!")

        else:
            # Load files
            if self.current_search:
                files = self.data_service.search_legacy_documents(self.current_search)
                self.filter_label.setText(f'Search: "{self.current_search}" ({len(files)} results)')
            else:
                files = all_files

            # Add file rows
            for doc in files:
                row = LegacyDocListRow(doc)
                row.clicked.connect(self._on_legacy_doc_clicked)
                row.convert_clicked.connect(self._on_convert_doc_clicked)
                self.cards_layout.addWidget(row)

            # Empty state
            if not files:
                self._show_empty_state("No files found.\n\nAdd documents to your team folder to see them here.")

        # Add stretch at the end to push items to top
        self.cards_layout.addStretch()

    def _show_empty_state(self, message: str):
        """Show an empty state message."""
        empty_label = QLabel(message)
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 14px; padding: 60px;")
        self.cards_layout.addWidget(empty_label)

    def _on_category_clicked(self, item: QListWidgetItem):
        """Handle category selection."""
        self.current_filter_category = item.text()
        self.current_filter_tag = None
        self.tag_list.clearSelection()
        self._load_content()

    def _on_tag_clicked(self, item: QListWidgetItem):
        """Handle tag selection."""
        self.current_filter_tag = item.text()
        self.current_filter_category = None
        self.category_list.clearSelection()
        self._load_content()

    def _clear_filters(self):
        """Clear all filters."""
        self.current_filter_category = None
        self.current_filter_tag = None
        self.current_search = ""
        self.search_bar.clear()
        self.category_list.clearSelection()
        self.tag_list.clearSelection()
        self._load_content()

    def _on_search_changed(self, text: str):
        """Handle search text changes."""
        self.current_search = text.strip()
        if self.current_search:
            self.current_filter_category = None
            self.current_filter_tag = None
            self.category_list.clearSelection()
            self.tag_list.clearSelection()
        self._load_content()

    def _on_path_clicked(self, path_id: int):
        """Handle path card click."""
        self.path_clicked.emit(path_id)

    def _on_legacy_doc_clicked(self, filepath: str):
        """Handle legacy document click - open in default app."""
        try:
            if sys.platform == 'darwin':
                subprocess.run(['open', filepath], check=True)
            elif sys.platform == 'win32':
                subprocess.run(['start', '', filepath], shell=True, check=True)
            else:
                subprocess.run(['xdg-open', filepath], check=True)
        except Exception as e:
            print(f"Error opening file: {e}")

    def _on_convert_doc_clicked(self, filepath: str):
        """Handle convert button click - convert legacy doc to FlowPath."""
        import os
        
        # Get output directory (same as team folder, in a 'converted' subfolder)
        team_folder = self.data_service.team_folder
        if not team_folder:
            QMessageBox.warning(
                self,
                "No Team Folder",
                "Please set a team folder before converting documents."
            )
            return
        
        output_dir = os.path.join(team_folder, "converted")
        
        # Show progress
        filename = os.path.basename(filepath)
        progress = QProgressDialog(
            f"Converting {filename}...",
            None,  # No cancel button
            0, 0,  # Indeterminate progress
            self
        )
        progress.setWindowTitle("Converting Document")
        progress.setModal(True)
        progress.show()
        
        # Force UI update
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        
        try:
            # Run conversion
            converter = LegacyConverter(output_dir)
            result = converter.convert(filepath)
            
            progress.close()
            
            if result.success:
                # Create a new FlowPath path from the conversion
                from ..models import Path as FlowPathModel
                
                new_path = FlowPathModel(
                    title=result.title,
                    category="Imported",
                    tags="imported, converted",
                    description=f"Converted from {filename}",
                    creator="converter"
                )
                
                # Save to database
                path_id = self.data_service.create_path(new_path)
                
                # Import steps from the generated markdown
                steps_created = 0
                if result.markdown_path:
                    steps_created = self._import_steps_from_markdown(path_id, result.markdown_path)
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Conversion Complete",
                    f"Successfully converted '{filename}' to FlowPath!\n\n"
                    f"Title: {result.title}\n"
                    f"Steps imported: {steps_created}\n\n"
                    f"The new path has been added to your library."
                )
                
                # Refresh to show the new path
                self.refresh()
            else:
                QMessageBox.critical(
                    self,
                    "Conversion Failed",
                    f"Failed to convert '{filename}':\n\n{result.error}"
                )
                
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                "Conversion Error",
                f"An error occurred during conversion:\n\n{str(e)}"
            )

    def _import_steps_from_markdown(self, path_id: int, markdown_path: str) -> int:
        """
        Parse a FlowPath markdown file and create Step records.
        
        Args:
            path_id: ID of the parent Path
            markdown_path: Path to the markdown file
            
        Returns:
            Number of steps created
        """
        import re
        import os
        from pathlib import Path
        from ..models import Step
        
        md_path = Path(markdown_path)
        
        try:
            content = md_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Error reading markdown file: {e}")
            return 0
        
        # The markdown file is at: /output_dir/slug/slug.md
        # Images are referenced as: slug/images/slide-01.jpg
        # Actual image location: /output_dir/slug/images/slide-01.jpg
        # So we need the parent of the markdown's parent (output_dir) to resolve paths
        output_dir = md_path.parent.parent
        
        # Pattern to match step headers: ## Step N: Title
        step_pattern = r'^## Step (\d+):\s*(.+?)$'
        
        # Split content on step headers while keeping the headers
        parts = re.split(r'(^## Step \d+:.*$)', content, flags=re.MULTILINE)
        
        steps_created = 0
        current_step_num = None
        
        for part in parts:
            header_match = re.match(step_pattern, part.strip())
            if header_match:
                # This is a step header - capture the step number
                current_step_num = int(header_match.group(1))
            elif current_step_num is not None:
                # This is content for the previous step header
                content_text = part.strip()
                
                # Extract screenshot path if present
                screenshot_path = None
                img_match = re.search(r'!\[.*?\]\((.+?)\)', content_text)
                if img_match:
                    relative_path = img_match.group(1)
                    # Convert to absolute path
                    absolute_path = output_dir / relative_path
                    if absolute_path.exists():
                        screenshot_path = str(absolute_path)
                    else:
                        # Try relative to markdown file's directory as fallback
                        alt_path = md_path.parent / relative_path
                        if alt_path.exists():
                            screenshot_path = str(alt_path)
                        else:
                            print(f"Warning: Image not found: {relative_path}")
                
                # Remove image markdown from instructions, keep the text
                instructions = re.sub(r'!\[.*?\]\(.+?\)\s*', '', content_text).strip()
                
                # Create the step record
                step = Step(
                    path_id=path_id,
                    step_number=current_step_num,
                    instructions=instructions,
                    screenshot_path=screenshot_path
                )
                
                self.data_service.create_step(step)
                steps_created += 1
                
                # Reset for next step
                current_step_num = None
        
        return steps_created

    def set_team_folder(self, folder_path: str):
        """Set the team folder path for legacy document scanning."""
        self.data_service.team_folder = folder_path
        self.refresh()
