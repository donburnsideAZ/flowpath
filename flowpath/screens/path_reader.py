from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt


class ReaderStepCard(QFrame):
    """A step displayed in read-only mode"""
    def __init__(self, step_number, instructions="Sample instructions for this step."):
        super().__init__()
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
        screenshot = QLabel(f"Screenshot {step_number}")
        screenshot.setFixedSize(200, 140)
        screenshot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        screenshot.setStyleSheet("""
            background-color: #f0f0f0;
            border: 2px solid #ccc;
            border-radius: 4px;
            font-size: 14px;
            color: #666;
        """)
        
        # Step content
        content_layout = QVBoxLayout()
        
        step_label = QLabel(f"Step {step_number}")
        step_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #333;")
        
        instructions_label = QLabel(instructions)
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
    def __init__(self):
        super().__init__()
        self.is_creator = True  # For now, assume user is creator
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        
        # === TOP BAR ===
        top_bar = QHBoxLayout()
        
        # Path title
        self.title_label = QLabel("How to Reset Password")
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
        
        top_bar.addWidget(share_btn)
        top_bar.addWidget(export_btn)
        top_bar.addWidget(print_btn)
        top_bar.addWidget(self.exit_btn)
        
        if self.is_creator:
            top_bar.addWidget(self.edit_btn)
        
        main_layout.addLayout(top_bar)
        main_layout.addSpacing(10)
        
        # === PATH METADATA ===
        meta_layout = QHBoxLayout()
        
        category_label = QLabel("Category: LMS")
        category_label.setStyleSheet("color: #666; font-size: 13px;")
        
        tags_label = QLabel("Tags: authentication, troubleshooting")
        tags_label.setStyleSheet("color: #1976D2; font-size: 13px;")
        
        meta_layout.addWidget(category_label)
        meta_layout.addSpacing(30)
        meta_layout.addWidget(tags_label)
        meta_layout.addStretch()
        
        main_layout.addLayout(meta_layout)
        main_layout.addSpacing(20)
        
        # === STEPS AREA ===
        steps_container = QVBoxLayout()
        
        # Sample steps for demonstration
        sample_steps = [
            "Navigate to the login page and click on the 'Forgot Password' link below the password field.",
            "Enter your email address in the form and click 'Submit'. Check your inbox for the reset link.",
            "Click the reset link in your email. You'll be taken to a page where you can enter a new password.",
            "Enter your new password twice to confirm, then click 'Reset Password'. You can now log in.",
        ]
        
        for i, instructions in enumerate(sample_steps, 1):
            step_card = ReaderStepCard(i, instructions)
            steps_container.addWidget(step_card)
        
        steps_container.addStretch()
        
        steps_widget = QWidget()
        steps_widget.setLayout(steps_container)
        
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