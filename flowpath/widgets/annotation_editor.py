"""
Annotation Editor for FlowPath.

Provides tools for annotating screenshots with arrows, rectangles, text, and callouts.
"""

import os
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QDialog, QLineEdit, QDialogButtonBox, QButtonGroup, QFrame,
    QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal, QSize
from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QPen, QBrush, QFont,
    QPolygon, QPainterPath, QFontMetrics
)


class Tool(Enum):
    """Available annotation tools."""
    ARROW = auto()
    RECTANGLE = auto()
    TEXT = auto()
    CALLOUT = auto()


@dataclass
class Annotation:
    """Base class for annotations."""
    tool: Tool
    color: QColor
    start: QPoint
    end: QPoint
    text: str = ""
    number: int = 0


class ColorButton(QPushButton):
    """A button that displays a color."""

    def __init__(self, color: QColor, parent=None):
        super().__init__(parent)
        self.color = color
        self.setFixedSize(28, 28)
        self.setCheckable(True)
        self._update_style()

    def _update_style(self):
        """Update button style based on color and checked state."""
        border = "3px solid #333" if self.isChecked() else "2px solid #888"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color.name()};
                border: {border};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid #333;
            }}
        """)

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self._update_style()


class ToolButton(QPushButton):
    """A styled tool button."""

    def __init__(self, text: str, tool: Tool, parent=None):
        super().__init__(text, parent)
        self.tool = tool
        self.setCheckable(True)
        self.setMinimumWidth(80)
        self.setStyleSheet("""
            QPushButton {
                padding: 8px 12px;
                font-size: 13px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: #f5f5f5;
            }
            QPushButton:hover {
                background: #e8e8e8;
            }
            QPushButton:checked {
                background: #4CAF50;
                color: white;
                border-color: #45a049;
            }
        """)


class AnnotationCanvas(QWidget):
    """Canvas widget for displaying and annotating screenshots."""

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.original_pixmap = pixmap
        self.annotations: List[Annotation] = []
        self.current_annotation: Optional[Annotation] = None
        self.current_tool = Tool.ARROW
        self.current_color = QColor("#FF0000")  # Red default
        self.callout_counter = 1

        # Set fixed size to match image
        self.setFixedSize(pixmap.size())
        self.setMouseTracking(True)

    def set_tool(self, tool: Tool):
        """Set the current drawing tool."""
        self.current_tool = tool

    def set_color(self, color: QColor):
        """Set the current drawing color."""
        self.current_color = color

    def add_text_annotation(self, pos: QPoint, text: str):
        """Add a text annotation at the given position."""
        annotation = Annotation(
            tool=Tool.TEXT,
            color=QColor(self.current_color),
            start=pos,
            end=pos,
            text=text
        )
        self.annotations.append(annotation)
        self.update()

    def add_callout_annotation(self, pos: QPoint):
        """Add a numbered callout at the given position."""
        annotation = Annotation(
            tool=Tool.CALLOUT,
            color=QColor(self.current_color),
            start=pos,
            end=pos,
            number=self.callout_counter
        )
        self.annotations.append(annotation)
        self.callout_counter += 1
        self.update()

    def undo(self):
        """Remove the last annotation."""
        if self.annotations:
            removed = self.annotations.pop()
            # If it was a callout, we might want to keep the counter
            # or we could decrement - keeping it simple for now
            self.update()
            return True
        return False

    def get_annotated_pixmap(self) -> QPixmap:
        """Return the pixmap with all annotations rendered."""
        result = self.original_pixmap.copy()
        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        for annotation in self.annotations:
            self._draw_annotation(painter, annotation)

        painter.end()
        return result

    def paintEvent(self, event):
        """Paint the canvas with image and annotations."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw original image
        painter.drawPixmap(0, 0, self.original_pixmap)

        # Draw all completed annotations
        for annotation in self.annotations:
            self._draw_annotation(painter, annotation)

        # Draw current annotation being created
        if self.current_annotation:
            self._draw_annotation(painter, self.current_annotation)

        painter.end()

    def _draw_annotation(self, painter: QPainter, annotation: Annotation):
        """Draw a single annotation."""
        if annotation.tool == Tool.ARROW:
            self._draw_arrow(painter, annotation)
        elif annotation.tool == Tool.RECTANGLE:
            self._draw_rectangle(painter, annotation)
        elif annotation.tool == Tool.TEXT:
            self._draw_text(painter, annotation)
        elif annotation.tool == Tool.CALLOUT:
            self._draw_callout(painter, annotation)

    def _draw_arrow(self, painter: QPainter, annotation: Annotation):
        """Draw an arrow annotation."""
        pen = QPen(annotation.color, 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        start = annotation.start
        end = annotation.end

        # Draw main line
        painter.drawLine(start, end)

        # Calculate arrow head
        import math
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        length = math.sqrt(dx * dx + dy * dy)

        if length > 0:
            # Normalize
            dx /= length
            dy /= length

            # Arrow head size
            head_length = 15
            head_width = 8

            # Arrow head points
            p1 = QPoint(
                int(end.x() - head_length * dx + head_width * dy),
                int(end.y() - head_length * dy - head_width * dx)
            )
            p2 = QPoint(
                int(end.x() - head_length * dx - head_width * dy),
                int(end.y() - head_length * dy + head_width * dx)
            )

            # Draw arrow head
            brush = QBrush(annotation.color)
            painter.setBrush(brush)
            arrow_head = QPolygon([end, p1, p2])
            painter.drawPolygon(arrow_head)

    def _draw_rectangle(self, painter: QPainter, annotation: Annotation):
        """Draw a rectangle annotation."""
        pen = QPen(annotation.color, 3)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        rect = QRect(annotation.start, annotation.end).normalized()
        painter.drawRect(rect)

    def _draw_text(self, painter: QPainter, annotation: Annotation):
        """Draw a text annotation."""
        font = QFont("Arial", 14, QFont.Weight.Bold)
        painter.setFont(font)

        # Draw text with background for readability
        metrics = QFontMetrics(font)
        text_rect = metrics.boundingRect(annotation.text)

        bg_rect = QRect(
            annotation.start.x() - 2,
            annotation.start.y() - text_rect.height(),
            text_rect.width() + 6,
            text_rect.height() + 4
        )

        # Semi-transparent background
        painter.fillRect(bg_rect, QColor(255, 255, 255, 200))

        # Draw text
        painter.setPen(annotation.color)
        painter.drawText(annotation.start, annotation.text)

    def _draw_callout(self, painter: QPainter, annotation: Annotation):
        """Draw a numbered callout circle."""
        radius = 14
        center = annotation.start

        # Draw circle
        painter.setPen(QPen(annotation.color, 2))
        painter.setBrush(QBrush(annotation.color))
        painter.drawEllipse(center, radius, radius)

        # Draw number
        font = QFont("Arial", 12, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(Qt.GlobalColor.white)

        text = str(annotation.number)
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(text)
        text_height = metrics.height()

        text_x = center.x() - text_width // 2
        text_y = center.y() + text_height // 4
        painter.drawText(text_x, text_y, text)

    def mousePressEvent(self, event):
        """Handle mouse press to start annotation."""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()

            if self.current_tool == Tool.TEXT:
                # Show text input dialog
                self._show_text_dialog(pos)
            elif self.current_tool == Tool.CALLOUT:
                self.add_callout_annotation(pos)
            else:
                # Start drawing arrow or rectangle
                self.current_annotation = Annotation(
                    tool=self.current_tool,
                    color=QColor(self.current_color),
                    start=pos,
                    end=pos
                )
                self.update()

    def mouseMoveEvent(self, event):
        """Handle mouse move to update annotation."""
        if self.current_annotation:
            self.current_annotation.end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release to complete annotation."""
        if event.button() == Qt.MouseButton.LeftButton and self.current_annotation:
            self.current_annotation.end = event.pos()

            # Only add if it has some size
            start = self.current_annotation.start
            end = self.current_annotation.end
            if abs(end.x() - start.x()) > 5 or abs(end.y() - start.y()) > 5:
                self.annotations.append(self.current_annotation)

            self.current_annotation = None
            self.update()

    def _show_text_dialog(self, pos: QPoint):
        """Show dialog to input text for annotation."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Text")
        layout = QVBoxLayout(dialog)

        label = QLabel("Enter annotation text:")
        layout.addWidget(label)

        text_input = QLineEdit()
        text_input.setMinimumWidth(250)
        layout.addWidget(text_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted and text_input.text():
            self.add_text_annotation(pos, text_input.text())


class AnnotationEditor(QDialog):
    """
    Dialog for annotating screenshots.

    Provides tools for adding arrows, rectangles, text, and numbered callouts.
    """

    # Signal emitted when editing is complete, with the annotated image path
    completed = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.setWindowTitle("Annotate Screenshot")
        self.setModal(True)

        # Load the image
        self.original_pixmap = QPixmap(image_path)
        if self.original_pixmap.isNull():
            raise ValueError(f"Could not load image: {image_path}")

        self._setup_ui()
        self._connect_signals()

        # Set reasonable initial size
        self._adjust_dialog_size()

    def _setup_ui(self):
        """Set up the editor UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Scrollable canvas area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(False)
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.canvas = AnnotationCanvas(self.original_pixmap)
        scroll_area.setWidget(self.canvas)
        layout.addWidget(scroll_area, 1)

        # Bottom buttons
        bottom_bar = self._create_bottom_bar()
        layout.addWidget(bottom_bar)

    def _create_toolbar(self) -> QWidget:
        """Create the annotation toolbar."""
        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame {
                background: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(10, 5, 10, 5)

        # Tool buttons
        tools_label = QLabel("Tools:")
        tools_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(tools_label)

        self.tool_group = QButtonGroup(self)
        self.tool_buttons = {}

        tools = [
            ("↗ Arrow", Tool.ARROW),
            ("▢ Rectangle", Tool.RECTANGLE),
            ("T Text", Tool.TEXT),
            ("① Callout", Tool.CALLOUT),
        ]

        for text, tool in tools:
            btn = ToolButton(text, tool)
            self.tool_buttons[tool] = btn
            self.tool_group.addButton(btn)
            layout.addWidget(btn)

        # Default to arrow
        self.tool_buttons[Tool.ARROW].setChecked(True)

        layout.addSpacing(20)

        # Color buttons
        colors_label = QLabel("Color:")
        colors_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(colors_label)

        self.color_group = QButtonGroup(self)
        self.color_buttons = []

        colors = [
            QColor("#FF0000"),  # Red
            QColor("#00AA00"),  # Green
            QColor("#0066FF"),  # Blue
            QColor("#FF9900"),  # Orange
            QColor("#9933FF"),  # Purple
        ]

        for color in colors:
            btn = ColorButton(color)
            self.color_buttons.append(btn)
            self.color_group.addButton(btn)
            layout.addWidget(btn)

        # Default to red
        self.color_buttons[0].setChecked(True)

        layout.addStretch()

        # Undo button
        self.undo_btn = QPushButton("↶ Undo")
        self.undo_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                font-size: 13px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: #fff;
            }
            QPushButton:hover {
                background: #f0f0f0;
            }
        """)
        layout.addWidget(self.undo_btn)

        return toolbar

    def _create_bottom_bar(self) -> QWidget:
        """Create the bottom action bar."""
        bar = QWidget()
        layout = QHBoxLayout(bar)

        # Instructions
        instructions = QLabel(
            "Arrow/Rectangle: Click and drag  •  "
            "Text: Click to place  •  "
            "Callout: Click to place numbered marker"
        )
        instructions.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(instructions)

        layout.addStretch()

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 24px;
                font-size: 14px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: #f5f5f5;
            }
            QPushButton:hover {
                background: #e8e8e8;
            }
        """)
        cancel_btn.clicked.connect(self._on_cancel)
        layout.addWidget(cancel_btn)

        # Save button
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 24px;
                font-size: 14px;
                border: none;
                border-radius: 4px;
                background: #4CAF50;
                color: white;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        save_btn.clicked.connect(self._on_save)
        layout.addWidget(save_btn)

        return bar

    def _connect_signals(self):
        """Connect toolbar signals."""
        # Tool selection
        self.tool_group.buttonClicked.connect(self._on_tool_changed)

        # Color selection
        self.color_group.buttonClicked.connect(self._on_color_changed)

        # Undo
        self.undo_btn.clicked.connect(self._on_undo)

    def _adjust_dialog_size(self):
        """Adjust dialog size based on image size."""
        img_size = self.original_pixmap.size()

        # Add padding for toolbar and buttons
        width = min(img_size.width() + 40, 1200)
        height = min(img_size.height() + 150, 900)

        self.resize(width, height)

    def _on_tool_changed(self, button):
        """Handle tool button click."""
        if isinstance(button, ToolButton):
            self.canvas.set_tool(button.tool)

    def _on_color_changed(self, button):
        """Handle color button click."""
        if isinstance(button, ColorButton):
            self.canvas.set_color(button.color)
            # Update button styles
            for btn in self.color_buttons:
                btn._update_style()

    def _on_undo(self):
        """Handle undo button click."""
        self.canvas.undo()

    def _on_save(self):
        """Save the annotated image."""
        annotated = self.canvas.get_annotated_pixmap()

        # Overwrite the original file
        if annotated.save(self.image_path, 'PNG'):
            self.completed.emit(self.image_path)
            self.accept()
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Failed to save annotated image.")

    def _on_cancel(self):
        """Cancel annotation editing."""
        self.cancelled.emit()
        self.reject()
