"""Home screen - displays all paths with search and filter."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QListWidget, QGridLayout,
    QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..models import Path
from ..storage import DataStore
from .. import styles


class PathCard(QFrame):
    """A single path card in the grid."""
    clicked = pyqtSignal(str)  # Emits path_id when clicked

    def __init__(self, path: Path):
        super().__init__()
        self.path = path
        self.path_id = path.path_id

        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self.setStyleSheet(styles.CARD_FRAME)
        self.setFixedSize(200, 150)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout()

        title_label = QLabel(path.title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_label.setWordWrap(True)

        category_label = QLabel(path.category)
        category_label.setStyleSheet("color: #666; font-size: 11px;")

        layout.addWidget(title_label)
        layout.addWidget(category_label)
        layout.addStretch()

        if path.is_creator:
            edit_btn = QPushButton("EDIT")
            edit_btn.setStyleSheet(styles.BUTTON_PRIMARY_SMALL)
            edit_btn.setFixedWidth(50)
            edit_btn.clicked.connect(self._on_edit_clicked)
            layout.addWidget(edit_btn)

        self.setLayout(layout)

    def _on_edit_clicked(self):
        """Handle edit button click."""
        self.clicked.emit(self.path_id)

    def mousePressEvent(self, event):
        """Handle click on the card."""
        self.clicked.emit(self.path_id)

    def enterEvent(self, event):
        """Mouse enter - highlight card."""
        self.setStyleSheet(styles.CARD_FRAME_HOVER)

    def leaveEvent(self, event):
        """Mouse leave - remove highlight."""
        self.setStyleSheet(styles.CARD_FRAME)


class HomeScreen(QWidget):
    """Main home/dashboard screen."""
    path_selected = pyqtSignal(str)  # Emits path_id for viewing
    path_edit = pyqtSignal(str)  # Emits path_id for editing
    new_path_requested = pyqtSignal()  # Request to create new path

    def __init__(self):
        super().__init__()
        self.data_store = DataStore()
        self.current_category = None
        self.current_tag = None
        self.search_query = ""
        self.setup_ui()
        self.load_paths()

    def setup_ui(self):
        # Main horizontal layout: sidebar | content
        main_layout = QHBoxLayout()

        # === LEFT SIDEBAR ===
        sidebar = QVBoxLayout()

        # New Path button
        self.new_path_btn = QPushButton("+ New Path")
        self.new_path_btn.setStyleSheet(styles.BUTTON_PRIMARY)
        self.new_path_btn.clicked.connect(self._on_new_path)
        sidebar.addWidget(self.new_path_btn)

        # Category label
        cat_header = QLabel("Category")
        cat_header.setStyleSheet(styles.LABEL_HEADER)
        sidebar.addWidget(cat_header)

        # Category list
        self.category_list = QListWidget()
        self.category_list.addItem("All Categories")
        self.category_list.addItems(["LMS", "Content Creation", "Admin", "Troubleshooting"])
        self.category_list.setStyleSheet(styles.LIST_WIDGET)
        self.category_list.setMaximumHeight(150)
        self.category_list.currentRowChanged.connect(self._on_category_changed)
        sidebar.addWidget(self.category_list)

        # Tags label
        tags_header = QLabel("Tags")
        tags_header.setStyleSheet(styles.LABEL_HEADER)
        sidebar.addWidget(tags_header)

        # Tag list
        self.tag_list = QListWidget()
        self.tag_list.addItem("All Tags")
        self.tag_list.setStyleSheet(styles.LIST_WIDGET_TAGS)
        self.tag_list.setMaximumHeight(120)
        self.tag_list.currentRowChanged.connect(self._on_tag_changed)
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
        self.search_bar.setStyleSheet(styles.INPUT_TEXT)
        self.search_bar.textChanged.connect(self._on_search_changed)
        content.addWidget(self.search_bar)

        # Category indicator
        self.filter_label = QLabel("Showing: All Paths")
        self.filter_label.setStyleSheet(styles.LABEL_MUTED)
        content.addWidget(self.filter_label)

        # Scrollable cards area
        self.cards_widget = QWidget()
        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(20)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.cards_widget.setLayout(self.cards_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.cards_widget)
        scroll_area.setStyleSheet(styles.SCROLL_AREA)

        content.addWidget(scroll_area)

        # Content container
        content_widget = QWidget()
        content_widget.setLayout(content)

        # === ASSEMBLE MAIN LAYOUT ===
        main_layout.addWidget(sidebar_widget)
        main_layout.addWidget(content_widget)

        self.setLayout(main_layout)

    def load_paths(self):
        """Load and display paths from storage."""
        # Get paths based on current filters
        paths = self.data_store.search_paths(
            self.search_query,
            category=self.current_category,
            tag=self.current_tag
        )

        # Update tag list with available tags
        self._update_tag_list()

        # Clear existing cards
        self._clear_cards()

        # Add path cards
        row, col = 0, 0
        for path in paths:
            card = PathCard(path)
            card.clicked.connect(self._on_path_clicked)
            self.cards_layout.addWidget(card, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

        # Update filter label
        self._update_filter_label(len(paths))

    def _clear_cards(self):
        """Remove all cards from the grid."""
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _update_tag_list(self):
        """Update the tag list with available tags."""
        current_selection = self.tag_list.currentRow()
        self.tag_list.clear()
        self.tag_list.addItem("All Tags")
        tags = self.data_store.get_all_tags()
        self.tag_list.addItems(tags)
        if current_selection >= 0 and current_selection < self.tag_list.count():
            self.tag_list.setCurrentRow(current_selection)

    def _update_filter_label(self, count: int):
        """Update the filter status label."""
        parts = []
        if self.current_category:
            parts.append(f"Category: {self.current_category}")
        if self.current_tag:
            parts.append(f"Tag: {self.current_tag}")
        if self.search_query:
            parts.append(f"Search: '{self.search_query}'")

        if parts:
            self.filter_label.setText(f"Showing: {count} paths ({', '.join(parts)})")
        else:
            self.filter_label.setText(f"Showing: {count} paths")

    def _on_new_path(self):
        """Handle new path button click."""
        self.new_path_requested.emit()

    def _on_path_clicked(self, path_id: str):
        """Handle path card click."""
        self.path_selected.emit(path_id)

    def _on_category_changed(self, row: int):
        """Handle category selection change."""
        if row == 0:  # "All Categories"
            self.current_category = None
        else:
            self.current_category = self.category_list.item(row).text()
        self.load_paths()

    def _on_tag_changed(self, row: int):
        """Handle tag selection change."""
        if row == 0:  # "All Tags"
            self.current_tag = None
        else:
            self.current_tag = self.tag_list.item(row).text()
        self.load_paths()

    def _on_search_changed(self, text: str):
        """Handle search text change."""
        self.search_query = text
        self.load_paths()

    def refresh(self):
        """Refresh the path list."""
        self.load_paths()
