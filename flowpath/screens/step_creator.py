from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap


class StepCreatorScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.screenshot_path = None
        self.original_pixmap = None  # Store original for rescaling
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        
        # === TOP BAR ===
        top_bar = QHBoxLayout()
        
        title_label = QLabel("Step Creator")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        top_bar.addWidget(title_label)
        
        top_bar.addStretch()
        
        # Save buttons
        self.save_add_btn = QPushButton("Save && +Step")
        self.save_add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.save_done_btn = QPushButton("Save && Done")
        self.save_done_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        
        top_bar.addWidget(self.save_add_btn)
        top_bar.addWidget(self.save_done_btn)
        
        main_layout.addLayout(top_bar)
        main_layout.addSpacing(20)
        
        # === SCREENSHOT BUTTON ===
        screenshot_btn_layout = QHBoxLayout()
        screenshot_btn_layout.addStretch()
        
        self.screenshot_btn = QPushButton("+ Screen Shot")
        self.screenshot_btn.setStyleSheet("""
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
        self.screenshot_btn.clicked.connect(self.capture_screenshot)
        
        screenshot_btn_layout.addWidget(self.screenshot_btn)
        screenshot_btn_layout.addStretch()
        
        main_layout.addLayout(screenshot_btn_layout)
        main_layout.addSpacing(20)
        
        # === SCREENSHOT AREA ===
        self.screenshot_frame = QFrame()
        self.screenshot_frame.setFrameStyle(QFrame.Shape.Box)
        self.screenshot_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 3px dashed #ccc;
                border-radius: 8px;
            }
        """)
        self.screenshot_frame.setMinimumHeight(350)
        
        screenshot_layout = QVBoxLayout()
        self.screenshot_label = QLabel("Screenshot will appear here")
        self.screenshot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screenshot_label.setStyleSheet("color: #999; font-size: 16px; border: none;")
        screenshot_layout.addWidget(self.screenshot_label)
        self.screenshot_frame.setLayout(screenshot_layout)
        
        main_layout.addWidget(self.screenshot_frame)
        main_layout.addSpacing(20)
        
        # === STEP INSTRUCTIONS ===
        self.instructions_input = QTextEdit()
        self.instructions_input.setPlaceholderText("Step instructions...")
        self.instructions_input.setStyleSheet("""
            QTextEdit {
                padding: 15px;
                font-size: 14px;
                border: 2px solid #ccc;
                border-radius: 8px;
            }
            QTextEdit:focus {
                border-color: #4CAF50;
            }
        """)
        self.instructions_input.setMinimumHeight(120)
        self.instructions_input.setMaximumHeight(150)
        
        main_layout.addWidget(self.instructions_input)
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def capture_screenshot(self):
        """Placeholder for screenshot capture - we'll implement this next

        Once you have a QPixmap from your capture, call:
            self.display_screenshot(pixmap)
        """
        self.screenshot_label.setText("Screenshot captured!\n(Capture functionality coming soon)")
        self.screenshot_label.setStyleSheet("color: #4CAF50; font-size: 16px; border: none;")
    
    def clear_step(self):
        """Clear the form for a new step"""
        self.screenshot_label.setText("Screenshot will appear here")
        self.screenshot_label.setStyleSheet("color: #999; font-size: 16px; border: none;")
        self.instructions_input.clear()
        self.screenshot_path = None
        self.original_pixmap = None

    def display_screenshot(self, pixmap):
        """Display a screenshot scaled to fit within the container"""
        self.original_pixmap = pixmap
        self._update_scaled_pixmap()

    def _update_scaled_pixmap(self):
        """Scale the pixmap to fit within the screenshot frame"""
        if self.original_pixmap is None:
            return

        # Get available size from the frame (with some padding)
        available_width = self.screenshot_frame.width() - 20
        available_height = self.screenshot_frame.height() - 20

        # Ensure minimum dimensions
        if available_width < 100 or available_height < 100:
            available_width = max(available_width, 100)
            available_height = max(available_height, 100)

        # Scale pixmap to fit while maintaining aspect ratio
        scaled_pixmap = self.original_pixmap.scaled(
            available_width,
            available_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.screenshot_label.setPixmap(scaled_pixmap)
        self.screenshot_label.setStyleSheet("border: none;")

    def resizeEvent(self, event):
        """Handle window resize to rescale screenshot"""
        super().resizeEvent(event)
        if self.original_pixmap is not None:
            self._update_scaled_pixmap()