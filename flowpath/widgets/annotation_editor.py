"""
Annotation Editor for FlowPath.

Provides tools for annotating screenshots with arrows, rectangles, text, callouts,
blur regions, and cropping.
"""

import math
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, List
from copy import deepcopy

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QDialog, QLineEdit, QDialogButtonBox, QButtonGroup, QFrame,
    QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QPen, QBrush, QFont,
    QPolygon, QFontMetrics, QImage
)


class Tool(Enum):
    """Available annotation tools."""
    ARROW = auto()
    RECTANGLE = auto()
    TEXT = auto()
    CALLOUT = auto()
    BLUR = auto()
    CROP = auto()


@dataclass
class Annotation:
    """Represents a single annotation."""
    tool: Tool
    color: QColor
    start: QPoint
    end: QPoint
    text: str = ""
    number: int = 0

    def copy(self) -> 'Annotation':
        """Create a copy of this annotation."""
        return Annotation(
            tool=self.tool,
            color=QColor(self.color),
            start=QPoint(self.start),
            end=QPoint(self.end),
            text=self.text,
            number=self.number
        )


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
        self.setMinimumWidth(70)
        self.setStyleSheet("""
            QPushButton {
                padding: 8px 10px;
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


@dataclass
class CanvasState:
    """Represents the complete state of the canvas for undo/redo."""
    pixmap: QPixmap
    annotations: List[Annotation]
    callout_counter: int

    def copy(self) -> 'CanvasState':
        """Create a deep copy of this state."""
        return CanvasState(
            pixmap=self.pixmap.copy(),
            annotations=[a.copy() for a in self.annotations],
            callout_counter=self.callout_counter
        )


class AnnotationCanvas(QWidget):
    """Canvas widget for displaying and annotating screenshots."""

    # Signal emitted when canvas state changes (for undo/redo button states)
    state_changed = pyqtSignal()

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.base_pixmap = pixmap.copy()  # The current base image (can change with crop)
        self.annotations: List[Annotation] = []
        self.current_annotation: Optional[Annotation] = None
        self.current_tool = Tool.ARROW
        self.current_color = QColor("#FF0000")  # Red default
        self.callout_counter = 1

        # Undo/redo stacks
        self.undo_stack: List[CanvasState] = []
        self.redo_stack: List[CanvasState] = []
        self.max_history = 50

        # Set fixed size to match image
        self.setFixedSize(pixmap.size())
        self.setMouseTracking(True)

    def _save_state(self):
        """Save current state to undo stack."""
        state = CanvasState(
            pixmap=self.base_pixmap.copy(),
            annotations=[a.copy() for a in self.annotations],
            callout_counter=self.callout_counter
        )
        self.undo_stack.append(state)

        # Clear redo stack when new action is performed
        self.redo_stack.clear()

        # Limit history size
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

        self.state_changed.emit()

    def _restore_state(self, state: CanvasState):
        """Restore canvas to a saved state."""
        self.base_pixmap = state.pixmap.copy()
        self.annotations = [a.copy() for a in state.annotations]
        self.callout_counter = state.callout_counter
        self.setFixedSize(self.base_pixmap.size())
        self.update()

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self.redo_stack) > 0

    def undo(self) -> bool:
        """Undo the last action."""
        if not self.undo_stack:
            return False

        # Save current state to redo stack
        current_state = CanvasState(
            pixmap=self.base_pixmap.copy(),
            annotations=[a.copy() for a in self.annotations],
            callout_counter=self.callout_counter
        )
        self.redo_stack.append(current_state)

        # Restore previous state
        previous_state = self.undo_stack.pop()
        self._restore_state(previous_state)
        self.state_changed.emit()
        return True

    def redo(self) -> bool:
        """Redo the last undone action."""
        if not self.redo_stack:
            return False

        # Save current state to undo stack
        current_state = CanvasState(
            pixmap=self.base_pixmap.copy(),
            annotations=[a.copy() for a in self.annotations],
            callout_counter=self.callout_counter
        )
        self.undo_stack.append(current_state)

        # Restore next state
        next_state = self.redo_stack.pop()
        self._restore_state(next_state)
        self.state_changed.emit()
        return True

    def set_tool(self, tool: Tool):
        """Set the current drawing tool."""
        self.current_tool = tool

    def set_color(self, color: QColor):
        """Set the current drawing color."""
        self.current_color = color

    def add_text_annotation(self, pos: QPoint, text: str):
        """Add a text annotation at the given position."""
        self._save_state()
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
        self._save_state()
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

    def apply_crop(self, rect: QRect):
        """Crop the base image to the given rectangle."""
        self._save_state()

        # Crop the base pixmap
        self.base_pixmap = self.base_pixmap.copy(rect)

        # Adjust all annotation positions
        offset = rect.topLeft()
        adjusted_annotations = []
        for ann in self.annotations:
            new_start = QPoint(ann.start.x() - offset.x(), ann.start.y() - offset.y())
            new_end = QPoint(ann.end.x() - offset.x(), ann.end.y() - offset.y())

            # Only keep annotations that are at least partially in the crop area
            if new_start.x() >= -50 and new_start.y() >= -50:
                ann_copy = ann.copy()
                ann_copy.start = new_start
                ann_copy.end = new_end
                adjusted_annotations.append(ann_copy)

        self.annotations = adjusted_annotations
        self.setFixedSize(self.base_pixmap.size())
        self.update()

    def apply_blur(self, rect: QRect):
        """Apply pixelation/blur to a region of the base image."""
        self._save_state()

        rect = rect.normalized()
        if rect.width() < 5 or rect.height() < 5:
            return

        # Convert pixmap to image for pixel manipulation
        image = self.base_pixmap.toImage()

        # Pixelation block size
        block_size = 10

        # Process the region
        for y in range(rect.top(), rect.bottom(), block_size):
            for x in range(rect.left(), rect.right(), block_size):
                # Calculate average color for this block
                r_sum, g_sum, b_sum, count = 0, 0, 0, 0

                for by in range(block_size):
                    for bx in range(block_size):
                        px, py = x + bx, y + by
                        if 0 <= px < image.width() and 0 <= py < image.height():
                            pixel = image.pixelColor(px, py)
                            r_sum += pixel.red()
                            g_sum += pixel.green()
                            b_sum += pixel.blue()
                            count += 1

                if count > 0:
                    avg_color = QColor(r_sum // count, g_sum // count, b_sum // count)

                    # Fill block with average color
                    for by in range(block_size):
                        for bx in range(block_size):
                            px, py = x + bx, y + by
                            if 0 <= px < image.width() and 0 <= py < image.height():
                                image.setPixelColor(px, py, avg_color)

        self.base_pixmap = QPixmap.fromImage(image)
        self.update()

    def get_annotated_pixmap(self) -> QPixmap:
        """Return the pixmap with all annotations rendered."""
        result = self.base_pixmap.copy()
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

        # Draw base image
        painter.drawPixmap(0, 0, self.base_pixmap)

        # Draw all completed annotations
        for annotation in self.annotations:
            self._draw_annotation(painter, annotation)

        # Draw current annotation being created
        if self.current_annotation:
            self._draw_annotation(painter, self.current_annotation)

            # For crop tool, dim the area outside the selection
            if self.current_annotation.tool == Tool.CROP:
                self._draw_crop_overlay(painter, self.current_annotation)

        painter.end()

    def _draw_crop_overlay(self, painter: QPainter, annotation: Annotation):
        """Draw semi-transparent overlay outside crop area."""
        rect = QRect(annotation.start, annotation.end).normalized()
        overlay = QColor(0, 0, 0, 150)

        # Draw overlay on four sides of the crop rectangle
        canvas_rect = self.rect()

        # Top
        painter.fillRect(QRect(0, 0, canvas_rect.width(), rect.top()), overlay)
        # Bottom
        painter.fillRect(QRect(0, rect.bottom(), canvas_rect.width(), canvas_rect.height() - rect.bottom()), overlay)
        # Left
        painter.fillRect(QRect(0, rect.top(), rect.left(), rect.height()), overlay)
        # Right
        painter.fillRect(QRect(rect.right(), rect.top(), canvas_rect.width() - rect.right(), rect.height()), overlay)

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
        elif annotation.tool == Tool.BLUR:
            self._draw_blur_preview(painter, annotation)
        elif annotation.tool == Tool.CROP:
            self._draw_crop_preview(painter, annotation)

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
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        length = math.sqrt(dx * dx + dy * dy)

        if length > 0:
            dx /= length
            dy /= length

            head_length = 15
            head_width = 8

            p1 = QPoint(
                int(end.x() - head_length * dx + head_width * dy),
                int(end.y() - head_length * dy - head_width * dx)
            )
            p2 = QPoint(
                int(end.x() - head_length * dx - head_width * dy),
                int(end.y() - head_length * dy + head_width * dx)
            )

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

        metrics = QFontMetrics(font)
        text_rect = metrics.boundingRect(annotation.text)

        bg_rect = QRect(
            annotation.start.x() - 2,
            annotation.start.y() - text_rect.height(),
            text_rect.width() + 6,
            text_rect.height() + 4
        )

        painter.fillRect(bg_rect, QColor(255, 255, 255, 200))
        painter.setPen(annotation.color)
        painter.drawText(annotation.start, annotation.text)

    def _draw_callout(self, painter: QPainter, annotation: Annotation):
        """Draw a numbered callout circle."""
        radius = 14
        center = annotation.start

        painter.setPen(QPen(annotation.color, 2))
        painter.setBrush(QBrush(annotation.color))
        painter.drawEllipse(center, radius, radius)

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

    def _draw_blur_preview(self, painter: QPainter, annotation: Annotation):
        """Draw a preview rectangle for blur area."""
        pen = QPen(QColor("#888888"), 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(QColor(128, 128, 128, 50))

        rect = QRect(annotation.start, annotation.end).normalized()
        painter.drawRect(rect)

        # Draw "BLUR" text in center
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.setPen(QColor("#666666"))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "BLUR")

    def _draw_crop_preview(self, painter: QPainter, annotation: Annotation):
        """Draw a preview rectangle for crop area."""
        pen = QPen(QColor("#4CAF50"), 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        rect = QRect(annotation.start, annotation.end).normalized()
        painter.drawRect(rect)

    def mousePressEvent(self, event):
        """Handle mouse press to start annotation."""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()

            if self.current_tool == Tool.TEXT:
                self._show_text_dialog(pos)
            elif self.current_tool == Tool.CALLOUT:
                self.add_callout_annotation(pos)
            else:
                # Start drawing
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

            start = self.current_annotation.start
            end = self.current_annotation.end
            rect = QRect(start, end).normalized()

            # Check minimum size
            if rect.width() > 5 or rect.height() > 5:
                if self.current_annotation.tool == Tool.BLUR:
                    self.apply_blur(rect)
                elif self.current_annotation.tool == Tool.CROP:
                    self.apply_crop(rect)
                else:
                    self._save_state()
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

    Provides tools for adding arrows, rectangles, text, numbered callouts,
    blur regions, and cropping.
    """

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
        self._update_undo_redo_buttons()
        self._adjust_dialog_size()

    def _setup_ui(self):
        """Set up the editor UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Scrollable canvas area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.canvas = AnnotationCanvas(self.original_pixmap)
        self.scroll_area.setWidget(self.canvas)
        layout.addWidget(self.scroll_area, 1)

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
            ("▢ Rect", Tool.RECTANGLE),
            ("T Text", Tool.TEXT),
            ("① Callout", Tool.CALLOUT),
            ("▦ Blur", Tool.BLUR),
            ("✂ Crop", Tool.CROP),
        ]

        for text, tool in tools:
            btn = ToolButton(text, tool)
            self.tool_buttons[tool] = btn
            self.tool_group.addButton(btn)
            layout.addWidget(btn)

        self.tool_buttons[Tool.ARROW].setChecked(True)

        layout.addSpacing(15)

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

        self.color_buttons[0].setChecked(True)

        layout.addStretch()

        # Undo/Redo buttons
        self.undo_btn = QPushButton("↶ Undo")
        self.undo_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 12px;
                font-size: 13px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: #fff;
            }
            QPushButton:hover {
                background: #f0f0f0;
            }
            QPushButton:disabled {
                color: #aaa;
                background: #f5f5f5;
            }
        """)
        layout.addWidget(self.undo_btn)

        self.redo_btn = QPushButton("↷ Redo")
        self.redo_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 12px;
                font-size: 13px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: #fff;
            }
            QPushButton:hover {
                background: #f0f0f0;
            }
            QPushButton:disabled {
                color: #aaa;
                background: #f5f5f5;
            }
        """)
        layout.addWidget(self.redo_btn)

        return toolbar

    def _create_bottom_bar(self) -> QWidget:
        """Create the bottom action bar."""
        bar = QWidget()
        layout = QHBoxLayout(bar)

        # Instructions
        self.instructions_label = QLabel(
            "Arrow/Rect: Click and drag  •  "
            "Text/Callout: Click to place  •  "
            "Blur/Crop: Click and drag to select area"
        )
        self.instructions_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.instructions_label)

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
        self.tool_group.buttonClicked.connect(self._on_tool_changed)
        self.color_group.buttonClicked.connect(self._on_color_changed)
        self.undo_btn.clicked.connect(self._on_undo)
        self.redo_btn.clicked.connect(self._on_redo)
        self.canvas.state_changed.connect(self._update_undo_redo_buttons)

    def _adjust_dialog_size(self):
        """Adjust dialog size based on image size."""
        img_size = self.original_pixmap.size()
        width = min(img_size.width() + 40, 1200)
        height = min(img_size.height() + 150, 900)
        self.resize(width, height)

    def _update_undo_redo_buttons(self):
        """Update enabled state of undo/redo buttons."""
        self.undo_btn.setEnabled(self.canvas.can_undo())
        self.redo_btn.setEnabled(self.canvas.can_redo())

    def _on_tool_changed(self, button):
        """Handle tool button click."""
        if isinstance(button, ToolButton):
            self.canvas.set_tool(button.tool)

    def _on_color_changed(self, button):
        """Handle color button click."""
        if isinstance(button, ColorButton):
            self.canvas.set_color(button.color)
            for btn in self.color_buttons:
                btn._update_style()

    def _on_undo(self):
        """Handle undo button click."""
        self.canvas.undo()
        # Update scroll area for potential size change from crop undo
        self.scroll_area.setWidget(self.canvas)

    def _on_redo(self):
        """Handle redo button click."""
        self.canvas.redo()
        # Update scroll area for potential size change from crop redo
        self.scroll_area.setWidget(self.canvas)

    def _on_save(self):
        """Save the annotated image."""
        annotated = self.canvas.get_annotated_pixmap()

        if annotated.save(self.image_path, 'PNG'):
            self.completed.emit(self.image_path)
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to save annotated image.")

    def _on_cancel(self):
        """Cancel annotation editing."""
        self.cancelled.emit()
        self.reject()
