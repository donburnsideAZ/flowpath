from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QComboBox,
    QFrame, QScrollArea
)
from PyQt6.QtCore import Qt


class StepCard(QFrame):
    """A single step in the path"""
    def __init__(self, step_number):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            StepCard {
                background-color: white;
                border: 2px solid #333;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        layout = QHBoxLayout()
        
        # Screenshot placeholder
        screenshot = QLabel("Screenshot")
        screenshot.setFixedSize(150, 100)
        screenshot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        screenshot.setStyleSheet("""
            background-color: #f0f0f0;
            border: 2px dashed #ccc;
            border-radius: 4px;
        """)
        
        # Step instructions
        instructions = QTextEdit()
        instructions.setPlaceholderText(f"Step {step_number} instructions...")
        instructions.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        instructions.setMinimumHeight(100)
        
        layout.addWidget(screenshot)
        layout.addWidget(instructions)
        
        self.setLayout(layout)


class PathEditorScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.steps = []
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        
        # === TOP BAR ===
        top_bar = QHBoxLayout()
        
        title_label = QLabel("New Path")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        top_bar.addWidget(title_label)
        
        top_bar.addStretch()
        
        # Save buttons
        save_done_btn = QPushButton("Save && Done")
        save_done_btn.setStyleSheet("""
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
        
        save_new_btn = QPushButton("Save && New")
        save_new_btn.setStyleSheet("""
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
        
        save_sync_btn = QPushButton("Save && Sync")
        save_sync_btn.setStyleSheet("""
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
        
        top_bar.addWidget(save_done_btn)
        top_bar.addWidget(save_new_btn)
        top_bar.addWidget(save_sync_btn)
        
        main_layout.addLayout(top_bar)
        
        # === FORM AND STEPS AREA ===
        content_layout = QHBoxLayout()
        
        # Left side: metadata form
        form_layout = QVBoxLayout()
        
        # Title
        title_input = QLineEdit()
        title_input.setPlaceholderText("Title")
        title_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #ccc;
                border-radius: 4px;
            }
        """)
        form_layout.addWidget(title_input)
        
        # Category dropdown
        category_combo = QComboBox()
        category_combo.addItems(["Select Category...", "LMS", "Content Creation", "Admin", "Troubleshooting"])
        category_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #ccc;
                border-radius: 4px;
            }
        """)
        form_layout.addWidget(category_combo)
        
        # Tags
        tags_input = QLineEdit()
        tags_input.setPlaceholderText("Tags (comma separated)")
        tags_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #ccc;
                border-radius: 4px;
            }
        """)
        form_layout.addWidget(tags_input)
        
        # Description
        description_input = QTextEdit()
        description_input.setPlaceholderText("Description")
        description_input.setStyleSheet("""
            QTextEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #ccc;
                border-radius: 4px;
            }
        """)
        description_input.setMaximumHeight(100)
        form_layout.addWidget(description_input)
        
        form_layout.addStretch()
        
        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        form_widget.setFixedWidth(250)
        
        # Right side: steps area
        steps_layout = QVBoxLayout()
        
        # +Step button
        add_step_btn = QPushButton("+ Step")
        add_step_btn.setStyleSheet("""
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
        add_step_btn.setFixedWidth(120)
        self.add_step_btn = add_step_btn  # Store reference for navigation
        
        steps_header = QHBoxLayout()
        steps_header.addStretch()
        steps_header.addWidget(add_step_btn)
        steps_layout.addLayout(steps_header)
        
        # Scrollable steps area
        self.steps_container = QVBoxLayout()
        self.steps_container.addStretch()
        
        steps_widget = QWidget()
        steps_widget.setLayout(self.steps_container)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(steps_widget)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
            }
        """)
        
        steps_layout.addWidget(scroll_area)
        
        # Add to content layout
        content_layout.addWidget(form_widget)
        content_layout.addLayout(steps_layout)
        
        main_layout.addLayout(content_layout)
        
        self.setLayout(main_layout)
        
        # Store reference to save_done for navigation later
        self.save_done_btn = save_done_btn
    
    def add_step(self):
        """Add a new step card"""
        step_num = len(self.steps) + 1
        step_card = StepCard(step_num)
        self.steps.append(step_card)
        
        # Insert before the stretch
        self.steps_container.insertWidget(self.steps_container.count() - 1, step_card)