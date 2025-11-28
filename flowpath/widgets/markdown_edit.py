"""
MarkdownTextEdit widget for FlowPath.

A text editor with a toolbar for inserting Markdown formatting.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QInputDialog, QLineEdit
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QTextCursor


class MarkdownTextEdit(QWidget):
    """
    A text editor widget with a Markdown formatting toolbar.

    Provides buttons for:
    - Bold (**text**)
    - Italic (*text*)
    - Link ([text](url))

    Usage:
        editor = MarkdownTextEdit()
        editor.setPlaceholderText("Enter instructions...")
        text = editor.toPlainText()
        editor.setText("Some **bold** text")
    """

    textChanged = pyqtSignal()

    def __init__(self, parent=None, show_toolbar: bool = True):
        super().__init__(parent)
        self.show_toolbar = show_toolbar
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Toolbar
        if self.show_toolbar:
            toolbar = QHBoxLayout()
            toolbar.setSpacing(4)

            # Bold button
            self.bold_btn = QPushButton("B")
            self.bold_btn.setToolTip("Bold (Ctrl+B)")
            self.bold_btn.setFixedSize(28, 28)
            self.bold_btn.setStyleSheet("""
                QPushButton {
                    font-weight: bold;
                    font-size: 14px;
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
            """)
            self.bold_btn.clicked.connect(self._insert_bold)
            toolbar.addWidget(self.bold_btn)

            # Italic button
            self.italic_btn = QPushButton("I")
            self.italic_btn.setToolTip("Italic (Ctrl+I)")
            self.italic_btn.setFixedSize(28, 28)
            self.italic_btn.setStyleSheet("""
                QPushButton {
                    font-style: italic;
                    font-size: 14px;
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
            """)
            self.italic_btn.clicked.connect(self._insert_italic)
            toolbar.addWidget(self.italic_btn)

            # Link button
            self.link_btn = QPushButton("🔗")
            self.link_btn.setToolTip("Insert Link (Ctrl+K)")
            self.link_btn.setFixedSize(28, 28)
            self.link_btn.setStyleSheet("""
                QPushButton {
                    font-size: 14px;
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
            """)
            self.link_btn.clicked.connect(self._insert_link)
            toolbar.addWidget(self.link_btn)

            toolbar.addStretch()
            layout.addLayout(toolbar)

        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("""
            QTextEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #ccc;
                border-radius: 4px;
            }
            QTextEdit:focus {
                border-color: #4CAF50;
            }
        """)
        self.text_edit.textChanged.connect(self.textChanged.emit)
        layout.addWidget(self.text_edit)

        self.setLayout(layout)

    def _insert_bold(self):
        """Insert bold markdown syntax around selected text."""
        self._wrap_selection("**", "**")

    def _insert_italic(self):
        """Insert italic markdown syntax around selected text."""
        self._wrap_selection("*", "*")

    def _insert_link(self):
        """Insert a markdown link."""
        cursor = self.text_edit.textCursor()
        selected_text = cursor.selectedText()

        # Get link URL from user
        url, ok = QInputDialog.getText(
            self,
            "Insert Link",
            "Enter URL:",
            QLineEdit.EchoMode.Normal,
            "https://"
        )

        if ok and url:
            link_text = selected_text if selected_text else "link text"
            markdown_link = f"[{link_text}]({url})"

            if selected_text:
                cursor.removeSelectedText()
            cursor.insertText(markdown_link)
            self.text_edit.setTextCursor(cursor)

    def _wrap_selection(self, prefix: str, suffix: str):
        """Wrap the selected text with prefix and suffix."""
        cursor = self.text_edit.textCursor()
        selected_text = cursor.selectedText()

        if selected_text:
            # Wrap selected text
            new_text = f"{prefix}{selected_text}{suffix}"
            cursor.removeSelectedText()
            cursor.insertText(new_text)
        else:
            # Insert placeholder and position cursor
            cursor.insertText(f"{prefix}text{suffix}")
            # Move cursor to select "text"
            cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, len(suffix))
            cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, 4)

        self.text_edit.setTextCursor(cursor)
        self.text_edit.setFocus()

    # ==================== Public API ====================

    def toPlainText(self) -> str:
        """Get the plain text content."""
        return self.text_edit.toPlainText()

    def setText(self, text: str):
        """Set the text content."""
        self.text_edit.setPlainText(text)

    def setPlainText(self, text: str):
        """Set the text content (alias for setText)."""
        self.text_edit.setPlainText(text)

    def setPlaceholderText(self, text: str):
        """Set the placeholder text."""
        self.text_edit.setPlaceholderText(text)

    def clear(self):
        """Clear the text content."""
        self.text_edit.clear()

    def setMinimumHeight(self, height: int):
        """Set minimum height of the text editor."""
        self.text_edit.setMinimumHeight(height)

    def setMaximumHeight(self, height: int):
        """Set maximum height of the text editor."""
        self.text_edit.setMaximumHeight(height)

    def setFocus(self):
        """Set focus to the text editor."""
        self.text_edit.setFocus()

    def setReadOnly(self, readonly: bool):
        """Set the editor to read-only mode."""
        self.text_edit.setReadOnly(readonly)
