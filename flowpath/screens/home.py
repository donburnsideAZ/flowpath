from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QListWidget, QGridLayout,
    QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal


class PathCard(QFrame):
    """A single path card in the grid"""
    def __init__(self, title, category, is_creator=False):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self.setStyleSheet("""
            PathCard {
                background-color: white;
                border: 2px solid #333;
                border-radius: 8px;
            }
        """)
        self.setFixedSize(200, 150)
        
        layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_label.setWordWrap(True)
        
        category_label = QLabel(category)
        category_label.setStyleSheet("color: #666; font-size: 11px;")
        
        layout.addWidget(title_label)
        layout.addWidget(category_label)
        layout.addStretch()
        
        if is_creator:
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
            layout.addWidget(edit_btn)
        
        self.setLayout(layout)
    
    def mousePressEvent(self, event):
        """Handle click on the card"""
        self.parent().parent().parent().path_clicked.emit()


class HomeScreen(QWidget):
    path_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        # Main horizontal layout: sidebar | content
        main_layout = QHBoxLayout()
        
        # === LEFT SIDEBAR ===
        sidebar = QVBoxLayout()
        
        # New Path button
        new_path_btn = QPushButton("+ New Path")
        new_path_btn.setStyleSheet("""
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
        self.new_path_btn = new_path_btn
        sidebar.addWidget(new_path_btn)
        
        # Category label
        cat_header = QLabel("Category")
        cat_header.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 20px;")
        sidebar.addWidget(cat_header)
        
        # Category list
        self.category_list = QListWidget()
        self.category_list.addItems(["LMS", "Content Creation", "Admin", "Troubleshooting"])
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
        sidebar.addWidget(self.category_list)
        
        # Tags label
        tags_header = QLabel("Tags")
        tags_header.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 20px;")
        sidebar.addWidget(tags_header)
        
        # Tag cloud (simplified as a list for now)
        self.tag_list = QListWidget()
        self.tag_list.addItems(["authentication", "video", "setup", "troubleshooting"])
        self.tag_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 6px;
                color: #1976D2;
            }
        """)
        self.tag_list.setMaximumHeight(120)
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
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("Search paths, tags or categories...")
        search_bar.setStyleSheet("""
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
        content.addWidget(search_bar)
        
        # Category indicator
        self.current_category = QLabel("Category: All")
        self.current_category.setStyleSheet("font-size: 14px; color: #666; padding: 10px 0;")
        content.addWidget(self.current_category)
        
        # Path cards grid
        cards_widget = QWidget()
        cards_layout = QGridLayout()
        cards_layout.setSpacing(20)
        
        # Sample cards (placeholders)
        sample_paths = [
            ("How to Reset Password", "LMS", True),
            ("Creating Video Content", "Content Creation", True),
            ("Admin Panel Overview", "Admin", False),
            ("Troubleshooting Login", "Troubleshooting", True),
            ("Upload Course Materials", "LMS", False),
            ("Export Reports", "Admin", True),
        ]
        
        row, col = 0, 0
        for title, category, is_creator in sample_paths:
            card = PathCard(title, category, is_creator)
            cards_layout.addWidget(card, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1
        
        cards_widget.setLayout(cards_layout)
        content.addWidget(cards_widget)
        content.addStretch()
        
        # Content container
        content_widget = QWidget()
        content_widget.setLayout(content)
        
        # === ASSEMBLE MAIN LAYOUT ===
        main_layout.addWidget(sidebar_widget)
        main_layout.addWidget(content_widget)
        
        self.setLayout(main_layout)
