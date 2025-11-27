from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QListWidget, QGridLayout,
    QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..database import get_database
from ..models import Path


class PathCard(QFrame):
    """A single path card in the grid"""
    clicked = pyqtSignal(int)  # Emits path_id when clicked

    def __init__(self, path: Path):
        super().__init__()
        self.path_id = path.id
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self.setStyleSheet("""
            PathCard {
                background-color: white;
                border: 2px solid #333;
                border-radius: 8px;
            }
            PathCard:hover {
                border-color: #4CAF50;
            }
        """)
        self.setFixedSize(200, 150)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout()

        title_label = QLabel(path.title or "Untitled")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_label.setWordWrap(True)

        category_label = QLabel(path.category or "No category")
        category_label.setStyleSheet("color: #666; font-size: 11px;")

        layout.addWidget(title_label)
        layout.addWidget(category_label)

        # Show tags if present
        if path.tags:
            tags_label = QLabel(path.tags)
            tags_label.setStyleSheet("color: #1976D2; font-size: 10px;")
            tags_label.setWordWrap(True)
            layout.addWidget(tags_label)

        layout.addStretch()
        self.setLayout(layout)

    def mousePressEvent(self, event):
        """Handle click on the card"""
        if self.path_id is not None:
            self.clicked.emit(self.path_id)


class HomeScreen(QWidget):
    path_clicked = pyqtSignal(int)  # Emits path_id
    new_path_requested = pyqtSignal()

    # Default categories (used when database is empty)
    DEFAULT_CATEGORIES = ["LMS", "Content Creation", "Admin", "Troubleshooting"]

    def __init__(self):
        super().__init__()
        self.current_filter_category = None
        self.current_search_query = ""
        self.setup_ui()

    def setup_ui(self):
        # Main horizontal layout: sidebar | content
        main_layout = QHBoxLayout()

        # === LEFT SIDEBAR ===
        sidebar = QVBoxLayout()

        # New Path button
        self.new_path_btn = QPushButton("+ New Path")
        self.new_path_btn.setStyleSheet("""
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
        sidebar.addWidget(self.new_path_btn)

        # Category label
        cat_header = QLabel("Category")
        cat_header.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 20px;")
        sidebar.addWidget(cat_header)

        # Category list
        self.category_list = QListWidget()
        self.category_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #e8f5e9;
                color: black;
            }
        """)
        self.category_list.setMaximumHeight(150)
        self.category_list.itemClicked.connect(self._on_category_selected)
        sidebar.addWidget(self.category_list)

        # Clear filter button
        self.clear_filter_btn = QPushButton("Show All")
        self.clear_filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                padding: 6px 12px;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.clear_filter_btn.clicked.connect(self._clear_filters)
        sidebar.addWidget(self.clear_filter_btn)

        # Tags label
        tags_header = QLabel("Tags")
        tags_header.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 20px;")
        sidebar.addWidget(tags_header)

        # Tag list
        self.tag_list = QListWidget()
        self.tag_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 6px;
                color: #1976D2;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)
        self.tag_list.setMaximumHeight(120)
        self.tag_list.itemClicked.connect(self._on_tag_selected)
        sidebar.addWidget(self.tag_list)

        sidebar.addStretch()

        # Sidebar container
        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar)
        sidebar_widget.setFixedWidth(200)

        # === MAIN CONTENT ===
        content = QVBoxLayout()

        # Team name header
        team_label = QLabel("Axway Documentation Team")
        team_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        team_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        content.addWidget(team_label)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search paths, tags or categories...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #ccc;
                border-radius: 6px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)
        self.search_bar.textChanged.connect(self._on_search_changed)
        content.addWidget(self.search_bar)

        # Category indicator
        self.current_category_label = QLabel("Category: All")
        self.current_category_label.setStyleSheet("font-size: 14px; color: #666; padding: 10px 0;")
        content.addWidget(self.current_category_label)

        # Scrollable area for path cards
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")

        # Container for path cards grid
        self.cards_container = QWidget()
        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(20)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.cards_container.setLayout(self.cards_layout)

        scroll_area.setWidget(self.cards_container)
        content.addWidget(scroll_area)

        # Content container
        content_widget = QWidget()
        content_widget.setLayout(content)

        # === ASSEMBLE MAIN LAYOUT ===
        main_layout.addWidget(sidebar_widget)
        main_layout.addWidget(content_widget)

        self.setLayout(main_layout)

    def refresh(self):
        """Refresh all data from the database."""
        self._load_categories()
        self._load_tags()
        self._load_paths()

    def _load_categories(self):
        """Load categories from database."""
        self.category_list.clear()

        db = get_database()
        categories = db.get_all_categories()

        # Use default categories if none exist
        if not categories:
            categories = self.DEFAULT_CATEGORIES

        self.category_list.addItems(categories)

    def _load_tags(self):
        """Load tags from database."""
        self.tag_list.clear()

        db = get_database()
        tags = db.get_all_tags()

        if tags:
            self.tag_list.addItems(tags)

    def _load_paths(self):
        """Load paths from database based on current filters."""
        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        db = get_database()

        # Get paths based on filters
        if self.current_search_query:
            paths = db.search_paths(self.current_search_query)
        elif self.current_filter_category:
            paths = db.get_paths_by_category(self.current_filter_category)
        else:
            paths = db.get_all_paths()

        # Create cards
        row, col = 0, 0
        for path in paths:
            card = PathCard(path)
            card.clicked.connect(self._on_path_clicked)
            self.cards_layout.addWidget(card, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

        # Show message if no paths
        if not paths:
            no_paths_label = QLabel("No paths found.\nClick '+ New Path' to create one.")
            no_paths_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_paths_label.setStyleSheet("color: #666; font-size: 14px; padding: 40px;")
            self.cards_layout.addWidget(no_paths_label, 0, 0)

    def _on_category_selected(self, item):
        """Handle category selection."""
        self.current_filter_category = item.text()
        self.current_search_query = ""
        self.search_bar.clear()
        self.current_category_label.setText(f"Category: {self.current_filter_category}")
        self._load_paths()

    def _on_tag_selected(self, item):
        """Handle tag selection - search for the tag."""
        tag = item.text()
        self.search_bar.setText(tag)

    def _on_search_changed(self, text):
        """Handle search text change."""
        self.current_search_query = text
        self.current_filter_category = None
        self.category_list.clearSelection()

        if text:
            self.current_category_label.setText(f"Search: {text}")
        else:
            self.current_category_label.setText("Category: All")

        self._load_paths()

    def _clear_filters(self):
        """Clear all filters and show all paths."""
        self.current_filter_category = None
        self.current_search_query = ""
        self.search_bar.clear()
        self.category_list.clearSelection()
        self.tag_list.clearSelection()
        self.current_category_label.setText("Category: All")
        self._load_paths()

    def _on_path_clicked(self, path_id: int):
        """Handle path card click."""
        self.path_clicked.emit(path_id)
