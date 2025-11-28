"""
MarkdownLabel widget for FlowPath.

A label that renders Markdown text as HTML.
"""

import re
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt


class MarkdownLabel(QLabel):
    """
    A QLabel that renders Markdown text as HTML.

    Supports:
    - Bold: **text** or __text__
    - Italic: *text* or _text_
    - Links: [text](url)
    - Line breaks

    Usage:
        label = MarkdownLabel()
        label.setMarkdown("This is **bold** and *italic*")
    """

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self.setWordWrap(True)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setOpenExternalLinks(True)
        self._markdown_text = ""

        if text:
            self.setMarkdown(text)

    def setMarkdown(self, text: str):
        """Set the text as Markdown and render as HTML."""
        self._markdown_text = text
        html = self._markdown_to_html(text)
        self.setText(html)

    def markdown(self) -> str:
        """Get the original Markdown text."""
        return self._markdown_text

    def _markdown_to_html(self, text: str) -> str:
        """Convert Markdown text to HTML."""
        if not text:
            return ""

        html = text

        # Escape HTML special characters first (but preserve our markdown)
        html = html.replace("&", "&amp;")
        html = html.replace("<", "&lt;")
        html = html.replace(">", "&gt;")

        # Links: [text](url) -> <a href="url">text</a>
        html = re.sub(
            r'\[([^\]]+)\]\(([^)]+)\)',
            r'<a href="\2" style="color: #1976D2;">\1</a>',
            html
        )

        # Bold: **text** or __text__ -> <b>text</b>
        html = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', html)
        html = re.sub(r'__([^_]+)__', r'<b>\1</b>', html)

        # Italic: *text* or _text_ -> <i>text</i>
        # Be careful not to match inside words with underscores
        html = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', html)
        html = re.sub(r'(?<![a-zA-Z])_([^_]+)_(?![a-zA-Z])', r'<i>\1</i>', html)

        # Line breaks: \n -> <br>
        html = html.replace("\n", "<br>")

        return html


def render_markdown(text: str) -> str:
    """
    Utility function to convert Markdown to HTML.

    Args:
        text: Markdown text

    Returns:
        HTML string
    """
    label = MarkdownLabel()
    return label._markdown_to_html(text)
