"""Reusable styles for FlowPath application."""

# Color palette
COLORS = {
    "primary": "#4CAF50",
    "primary_hover": "#45a049",
    "secondary": "#2196F3",
    "secondary_hover": "#1976D2",
    "neutral": "#666",
    "neutral_hover": "#555",
    "border": "#ccc",
    "border_dark": "#333",
    "background": "#f5f5f5",
    "background_light": "#fafafa",
    "text": "#333",
    "text_muted": "#666",
    "text_link": "#1976D2",
    "white": "#ffffff",
    "success_bg": "#e8f5e9",
}

# Button styles
BUTTON_PRIMARY = """
    QPushButton {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        font-size: 14px;
        font-weight: bold;
        border-radius: 6px;
    }
    QPushButton:hover {
        background-color: #45a049;
    }
    QPushButton:disabled {
        background-color: #a5d6a7;
    }
"""

BUTTON_PRIMARY_SMALL = """
    QPushButton {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 8px 16px;
        font-size: 12px;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #45a049;
    }
"""

BUTTON_SECONDARY = """
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
"""

BUTTON_NEUTRAL = """
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
"""

BUTTON_DANGER = """
    QPushButton {
        background-color: #f44336;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #d32f2f;
    }
"""

# Input styles
INPUT_TEXT = """
    QLineEdit {
        padding: 10px;
        font-size: 14px;
        border: 2px solid #ccc;
        border-radius: 4px;
    }
    QLineEdit:focus {
        border-color: #4CAF50;
    }
"""

INPUT_TEXTAREA = """
    QTextEdit {
        padding: 10px;
        font-size: 14px;
        border: 2px solid #ccc;
        border-radius: 4px;
    }
    QTextEdit:focus {
        border-color: #4CAF50;
    }
"""

INPUT_COMBO = """
    QComboBox {
        padding: 10px;
        font-size: 14px;
        border: 2px solid #ccc;
        border-radius: 4px;
    }
    QComboBox:focus {
        border-color: #4CAF50;
    }
"""

# List widget styles
LIST_WIDGET = """
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
"""

LIST_WIDGET_TAGS = """
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
"""

# Card styles
CARD_FRAME = """
    background-color: white;
    border: 2px solid #333;
    border-radius: 8px;
"""

CARD_FRAME_HOVER = """
    background-color: #f5f5f5;
    border: 2px solid #4CAF50;
    border-radius: 8px;
"""

# Screenshot placeholder
SCREENSHOT_PLACEHOLDER = """
    background-color: #f0f0f0;
    border: 2px dashed #ccc;
    border-radius: 4px;
"""

SCREENSHOT_FRAME = """
    QFrame {
        background-color: #f5f5f5;
        border: 3px dashed #ccc;
        border-radius: 8px;
    }
"""

# Scroll area
SCROLL_AREA = """
    QScrollArea {
        border: none;
        background-color: #fafafa;
    }
"""

# Label styles
LABEL_TITLE = "font-size: 20px; font-weight: bold;"
LABEL_HEADER = "font-weight: bold; font-size: 14px; margin-top: 20px;"
LABEL_MUTED = "color: #666; font-size: 13px;"
LABEL_LINK = "color: #1976D2; font-size: 13px;"
