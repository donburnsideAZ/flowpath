from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QListWidget, QGridLayout,
    QFrame, QScrollArea, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..services import DataService
from ..models import Path


class PathCard(QFrame):
    """A single path card in the grid"""
    clicked = pyqtSignal(int)  # Emits path_id when clicked
    edit_clicked = pyqtSignal(int)  # Emits path_id when edit clicked

    def __init__(self, path: Path, current_user: str = ""):
        super().__init__()
        self.path_id = path.id
        self.is_creator = (path.creator == current_user) if current_user else True

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

        title_label = QLabel(path.title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_label.setWordWrap(True)

        category_label = QLabel(path.category or "No category")
        category_label.setStyleSheet("color: #666; font-size: 11px;")

        layout.addWidget(title_label)
        layout.addWidget(category_label)

        # Show tags if present
        if path.tags:
            tags_label = QLabel(path.tags[:30] + "..." if len(path.tags) > 30 else path.tags)
            tags_label.setStyleSheet("color: #1976D2; font-size: 10px;")
            layout.addWidget(tags_label)

        layout.addStretch()

        if self.is_creator:
            edit_btn = QPushButton("EDIT")
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            edit_btn.setFixedWidth(50)
            edit_btn.clicked.connect(self._on_edit_clicked)
            layout.addWidget(edit_btn)

        self.setLayout(layout)

    def _on_edit_clicked(self):
        """Handle edit button click"""
        self.edit_clicked.emit(self.path_id)

    def mousePressEvent(self, event):
        """Handle click on the card"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.path_id)


class HomeScreen(QWidget):
    path_clicked = pyqtSignal(int)  # Emits path_id
    edit_path_clicked = pyqtSignal(int)  # Emits path_id for editing
    new_path_requested = pyqtSignal()  # Emitted when New Path clicked

    def __init__(self):
        super().__init__()
        self.data_service = DataService.instance()
        self.current_user = ""  # Will be set by main window if needed
        self.current_filter_category = None
        self.current_filter_tag = None
        self.current_search = ""
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
        self.category_list.itemClicked.connect(self._on_category_clicked)
        sidebar.addWidget(self.category_list)

        # Clear category filter button
        self.clear_category_btn = QPushButton("Clear Filter")
        self.clear_category_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                padding: 4px 8px;
                font-size: 11px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.clear_category_btn.clicked.connect(self._clear_filters)
        self.clear_category_btn.hide()
        sidebar.addWidget(self.clear_category_btn)

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
        self.tag_list.itemClicked.connect(self._on_tag_clicked)
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

        # Filter indicator
        self.filter_label = QLabel("Showing: All Paths")
        self.filter_label.setStyleSheet("font-size: 14px; color: #666; padding: 10px 0;")
        content.addWidget(self.filter_label)

        # Path cards scroll area
        self.cards_widget = QWidget()
        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(20)
        self.cards_widget.setLayout(self.cards_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.cards_widget)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #fafafa;
            }
        """)

        content.addWidget(scroll_area)

        # Content container
        content_widget = QWidget()
        content_widget.setLayout(content)

        # === ASSEMBLE MAIN LAYOUT ===
        main_layout.addWidget(sidebar_widget)
        main_layout.addWidget(content_widget)

        self.setLayout(main_layout)

        # Initial load
        self.refresh()

    def refresh(self):
        """Refresh the entire screen with current data"""
        self._load_categories()
        self._load_tags()
        self._load_paths()

    def _load_categories(self):
        """Load categories from database"""
        self.category_list.clear()
        categories = self.data_service.get_categories()
        if categories:
            for category in categories:
                self.category_list.addItem(category)
        else:
            # Show default categories if none exist
            self.category_list.addItems(["LMS", "Content Creation", "Admin", "Troubleshooting"])

    def _load_tags(self):
        """Load tags from database"""
        self.tag_list.clear()
        tags = self.data_service.get_all_tags()
        if tags:
            for tag in tags:
                self.tag_list.addItem(tag)
        else:
            # Show default tags if none exist
            self.tag_list.addItems(["authentication", "video", "setup", "troubleshooting"])

    def _load_paths(self):
        """Load and display paths based on current filters"""
        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get paths based on filters
        if self.current_search:
            paths = self.data_service.search_paths(self.current_search)
            self.filter_label.setText(f"Search: \"{self.current_search}\" ({len(paths)} results)")
        elif self.current_filter_category:
            paths = self.data_service.get_paths_by_category(self.current_filter_category)
            self.filter_label.setText(f"Category: {self.current_filter_category} ({len(paths)} paths)")
        elif self.current_filter_tag:
            paths = self.data_service.get_paths_by_tag(self.current_filter_tag)
            self.filter_label.setText(f"Tag: {self.current_filter_tag} ({len(paths)} paths)")
        else:
            paths = self.data_service.get_all_paths()
            self.filter_label.setText(f"Showing: All Paths ({len(paths)} total)")

        # Show/hide clear filter button
        if self.current_filter_category or self.current_filter_tag:
            self.clear_category_btn.show()
        else:
            self.clear_category_btn.hide()

        # Create cards for each path
        if paths:
            row, col = 0, 0
            for path in paths:
                card = PathCard(path, self.current_user)
                card.clicked.connect(self._on_path_clicked)
                card.edit_clicked.connect(self._on_edit_path_clicked)
                self.cards_layout.addWidget(card, row, col)
                col += 1
                if col >= 3:
                    col = 0
                    row += 1
        else:
            # Show empty state
            empty_label = QLabel("No paths found.\n\nClick '+ New Path' to create one!")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #666; font-size: 16px; padding: 40px;")
            self.cards_layout.addWidget(empty_label, 0, 0, 1, 3)

    def _on_category_clicked(self, item: QListWidgetItem):
        """Handle category selection"""
        self.current_filter_category = item.text()
        self.current_filter_tag = None
        self.tag_list.clearSelection()
        self._load_paths()

    def _on_tag_clicked(self, item: QListWidgetItem):
        """Handle tag selection"""
        self.current_filter_tag = item.text()
        self.current_filter_category = None
        self.category_list.clearSelection()
        self._load_paths()

    def _clear_filters(self):
        """Clear all filters"""
        self.current_filter_category = None
        self.current_filter_tag = None
        self.current_search = ""
        self.search_bar.clear()
        self.category_list.clearSelection()
        self.tag_list.clearSelection()
        self._load_paths()

    def _on_search_changed(self, text: str):
        """Handle search text changes"""
        self.current_search = text.strip()
        if self.current_search:
            self.current_filter_category = None
            self.current_filter_tag = None
            self.category_list.clearSelection()
            self.tag_list.clearSelection()
        self._load_paths()

    def _on_path_clicked(self, path_id: int):
        """Handle path card click"""
        self.path_clicked.emit(path_id)

    def _on_edit_path_clicked(self, path_id: int):
        """Handle edit button click on path card"""
        self.edit_path_clicked.emit(path_id)
