"""
Annotation Editor for FlowPath.

Provides tools for annotating screenshots with arrows, rectangles, text, callouts,
blur regions, and cropping. Supports selecting and moving annotations.
"""

import math
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QDialog, QLineEdit, QDialogButtonBox, QButtonGroup, QFrame,
    QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QPen, QBrush, QFont,
    QPolygon, QFontMetrics, QCursor
)


class Tool(Enum):
    """Available annotation tools."""
    SELECT = auto()
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

    def get_bounding_rect(self) -> QRect:
        """Get the bounding rectangle for hit testing."""
        if self.tool == Tool.ARROW:
            # Arrow bounding box with some padding
            min_x = min(self.start.x(), self.end.x()) - 10
            min_y = min(self.start.y(), self.end.y()) - 10
            max_x = max(self.start.x(), self.end.x()) + 10
            max_y = max(self.start.y(), self.end.y()) + 10
            return QRect(min_x, min_y, max_x - min_x, max_y - min_y)
        elif self.tool == Tool.RECTANGLE:
            return QRect(self.start, self.end).normalized().adjusted(-5, -5, 5, 5)
        elif self.tool == Tool.TEXT:
            # Approximate text bounds
            return QRect(self.start.x() - 5, self.start.y() - 25, 200, 30)
        elif self.tool == Tool.CALLOUT:
            # Circle with radius 14
            return QRect(self.start.x() - 18, self.start.y() - 18, 36, 36)
        return QRect()

    def contains_point(self, point: QPoint) -> bool:
        """Check if a point is within this annotation."""
        if self.tool == Tool.CALLOUT:
            # Circle hit test
            dx = point.x() - self.start.x()
            dy = point.y() - self.start.y()
            return (dx * dx + dy * dy) <= (18 * 18)
        elif self.tool == Tool.ARROW:
            # Line distance test
            return self._point_near_line(point, self.start, self.end, 10)
        else:
            return self.get_bounding_rect().contains(point)

    def _point_near_line(self, point: QPoint, start: QPoint, end: QPoint, threshold: float) -> bool:
        """Check if point is within threshold distance of line segment."""
        # Vector from start to end
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        length_sq = dx * dx + dy * dy

        if length_sq == 0:
            # Start and end are the same point
            return (point.x() - start.x()) ** 2 + (point.y() - start.y()) ** 2 <= threshold ** 2

        # Project point onto line
        t = max(0, min(1, ((point.x() - start.x()) * dx + (point.y() - start.y()) * dy) / length_sq))
        proj_x = start.x() + t * dx
        proj_y = start.y() + t * dy

        # Distance from point to projection
        dist_sq = (point.x() - proj_x) ** 2 + (point.y() - proj_y) ** 2
        return dist_sq <= threshold ** 2

    def move_by(self, delta: QPoint):
        """Move this annotation by the given delta."""
        self.start = QPoint(self.start.x() + delta.x(), self.start.y() + delta.y())
        self.end = QPoint(self.end.x() + delta.x(), self.end.y() + delta.y())


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
        self.setMinimumWidth(65)
        self.setStyleSheet("""
            QPushButton {
                padding: 8px 8px;
                font-size: 12px;
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

    state_changed = pyqtSignal()

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.base_pixmap = pixmap.copy()
        self.annotations: List[Annotation] = []
        self.current_annotation: Optional[Annotation] = None
        self.current_tool = Tool.ARROW
        self.current_color = QColor("#FF0000")
        self.callout_counter = 1

        # Selection state
        self.selected_index: Optional[int] = None
        self.dragging = False
        self.drag_start: Optional[QPoint] = None

        # Undo/redo stacks
        self.undo_stack: List[CanvasState] = []
        self.redo_stack: List[CanvasState] = []
        self.max_history = 50

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
        self.redo_stack.clear()

        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

        self.state_changed.emit()

    def _restore_state(self, state: CanvasState):
        """Restore canvas to a saved state."""
        self.base_pixmap = state.pixmap.copy()
        self.annotations = [a.copy() for a in state.annotations]
        self.callout_counter = state.callout_counter
        self.selected_index = None
        self.setFixedSize(self.base_pixmap.size())
        self.update()

    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0

    def undo(self) -> bool:
        if not self.undo_stack:
            return False

        current_state = CanvasState(
            pixmap=self.base_pixmap.copy(),
            annotations=[a.copy() for a in self.annotations],
            callout_counter=self.callout_counter
        )
        self.redo_stack.append(current_state)

        previous_state = self.undo_stack.pop()
        self._restore_state(previous_state)
        self.state_changed.emit()
        return True

    def redo(self) -> bool:
        if not self.redo_stack:
            return False

        current_state = CanvasState(
            pixmap=self.base_pixmap.copy(),
            annotations=[a.copy() for a in self.annotations],
            callout_counter=self.callout_counter
        )
        self.undo_stack.append(current_state)

        next_state = self.redo_stack.pop()
        self._restore_state(next_state)
        self.state_changed.emit()
        return True

    def set_tool(self, tool: Tool):
        """Set the current drawing tool."""
        self.current_tool = tool
        if tool != Tool.SELECT:
            self.selected_index = None
            self.update()

    def set_color(self, color: QColor):
        """Set the current drawing color."""
        self.current_color = color

    def delete_selected(self):
        """Delete the currently selected annotation."""
        if self.selected_index is not None and 0 <= self.selected_index < len(self.annotations):
            self._save_state()
            del self.annotations[self.selected_index]
            self.selected_index = None
            self.update()

    def _find_annotation_at(self, point: QPoint) -> Optional[int]:
        """Find annotation at the given point (returns index or None)."""
        # Search in reverse order (top-most first)
        for i in range(len(self.annotations) - 1, -1, -1):
            if self.annotations[i].contains_point(point):
                return i
        return None

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
        self.base_pixmap = self.base_pixmap.copy(rect)

        offset = rect.topLeft()
        adjusted_annotations = []
        for ann in self.annotations:
            new_start = QPoint(ann.start.x() - offset.x(), ann.start.y() - offset.y())
            new_end = QPoint(ann.end.x() - offset.x(), ann.end.y() - offset.y())

            if new_start.x() >= -50 and new_start.y() >= -50:
                ann_copy = ann.copy()
                ann_copy.start = new_start
                ann_copy.end = new_end
                adjusted_annotations.append(ann_copy)

        self.annotations = adjusted_annotations
        self.selected_index = None
        self.setFixedSize(self.base_pixmap.size())
        self.update()

    def apply_blur(self, rect: QRect):
        """Apply pixelation/blur to a region of the base image."""
        self._save_state()

        rect = rect.normalized()
        if rect.width() < 5 or rect.height() < 5:
            return

        image = self.base_pixmap.toImage()
        block_size = 10

        for y in range(rect.top(), rect.bottom(), block_size):
            for x in range(rect.left(), rect.right(), block_size):
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
            self._draw_annotation(painter, annotation, selected=False)

        painter.end()
        return result

    def paintEvent(self, event):
        """Paint the canvas with image and annotations."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.drawPixmap(0, 0, self.base_pixmap)

        for i, annotation in enumerate(self.annotations):
            is_selected = (i == self.selected_index)
            self._draw_annotation(painter, annotation, selected=is_selected)

        if self.current_annotation:
            self._draw_annotation(painter, self.current_annotation, selected=False)

            if self.current_annotation.tool == Tool.CROP:
                self._draw_crop_overlay(painter, self.current_annotation)

        painter.end()

    def _draw_crop_overlay(self, painter: QPainter, annotation: Annotation):
        """Draw semi-transparent overlay outside crop area."""
        rect = QRect(annotation.start, annotation.end).normalized()
        overlay = QColor(0, 0, 0, 150)
        canvas_rect = self.rect()

        painter.fillRect(QRect(0, 0, canvas_rect.width(), rect.top()), overlay)
        painter.fillRect(QRect(0, rect.bottom(), canvas_rect.width(), canvas_rect.height() - rect.bottom()), overlay)
        painter.fillRect(QRect(0, rect.top(), rect.left(), rect.height()), overlay)
        painter.fillRect(QRect(rect.right(), rect.top(), canvas_rect.width() - rect.right(), rect.height()), overlay)

    def _draw_annotation(self, painter: QPainter, annotation: Annotation, selected: bool = False):
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

        # Draw selection highlight
        if selected:
            self._draw_selection_highlight(painter, annotation)

    def _draw_selection_highlight(self, painter: QPainter, annotation: Annotation):
        """Draw selection highlight around annotation."""
        rect = annotation.get_bounding_rect()
        pen = QPen(QColor("#0066FF"), 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)

        # Draw corner handles
        handle_size = 6
        painter.setBrush(QBrush(QColor("#0066FF")))
        painter.setPen(Qt.PenStyle.NoPen)

        corners = [
            rect.topLeft(),
            rect.topRight(),
            rect.bottomLeft(),
            rect.bottomRight()
        ]
        for corner in corners:
            painter.drawRect(
                corner.x() - handle_size // 2,
                corner.y() - handle_size // 2,
                handle_size,
                handle_size
            )

    def _draw_arrow(self, painter: QPainter, annotation: Annotation):
        """Draw an arrow annotation."""
        pen = QPen(annotation.color, 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        start = annotation.start
        end = annotation.end

        painter.drawLine(start, end)

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
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()

            if self.current_tool == Tool.SELECT:
                # Try to select an annotation
                clicked_index = self._find_annotation_at(pos)
                if clicked_index is not None:
                    self.selected_index = clicked_index
                    self.dragging = True
                    self.drag_start = pos
                else:
                    self.selected_index = None
                self.update()

            elif self.current_tool == Tool.TEXT:
                self._show_text_dialog(pos)

            elif self.current_tool == Tool.CALLOUT:
                self.add_callout_annotation(pos)

            else:
                self.current_annotation = Annotation(
                    tool=self.current_tool,
                    color=QColor(self.current_color),
                    start=pos,
                    end=pos
                )
                self.update()

    def mouseMoveEvent(self, event):
        """Handle mouse move."""
        pos = event.pos()

        if self.dragging and self.selected_index is not None and self.drag_start is not None:
            # Move the selected annotation
            delta = QPoint(pos.x() - self.drag_start.x(), pos.y() - self.drag_start.y())
            self.annotations[self.selected_index].move_by(delta)
            self.drag_start = pos
            self.update()

        elif self.current_annotation:
            self.current_annotation.end = pos
            self.update()

        # Update cursor based on hover state
        if self.current_tool == Tool.SELECT:
            if self._find_annotation_at(pos) is not None:
                self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            else:
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.dragging:
                # Finish dragging - save state for undo
                if self.drag_start is not None:
                    self._save_state()
                self.dragging = False
                self.drag_start = None

            elif self.current_annotation:
                start = self.current_annotation.start
                end = self.current_annotation.end
                rect = QRect(start, end).normalized()

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

    def mouseDoubleClickEvent(self, event):
        """Handle double-click for editing text annotations."""
        if event.button() == Qt.MouseButton.LeftButton and self.current_tool == Tool.SELECT:
            pos = event.pos()
            clicked_index = self._find_annotation_at(pos)

            if clicked_index is not None:
                annotation = self.annotations[clicked_index]

                if annotation.tool == Tool.TEXT:
                    self._edit_text_annotation(clicked_index)
                elif annotation.tool == Tool.CALLOUT:
                    self._edit_callout_annotation(clicked_index)

    def _show_text_dialog(self, pos: QPoint, initial_text: str = ""):
        """Show dialog to input text for annotation."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Text")
        layout = QVBoxLayout(dialog)

        label = QLabel("Enter annotation text:")
        layout.addWidget(label)

        text_input = QLineEdit()
        text_input.setMinimumWidth(250)
        text_input.setText(initial_text)
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

    def _edit_text_annotation(self, index: int):
        """Edit an existing text annotation."""
        annotation = self.annotations[index]

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Text")
        layout = QVBoxLayout(dialog)

        label = QLabel("Edit annotation text:")
        layout.addWidget(label)

        text_input = QLineEdit()
        text_input.setMinimumWidth(250)
        text_input.setText(annotation.text)
        text_input.selectAll()
        layout.addWidget(text_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted and text_input.text():
            self._save_state()
            self.annotations[index].text = text_input.text()
            self.update()

    def _edit_callout_annotation(self, index: int):
        """Edit an existing callout annotation number."""
        annotation = self.annotations[index]

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Callout")
        layout = QVBoxLayout(dialog)

        label = QLabel("Enter callout number:")
        layout.addWidget(label)

        text_input = QLineEdit()
        text_input.setMinimumWidth(100)
        text_input.setText(str(annotation.number))
        text_input.selectAll()
        layout.addWidget(text_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                new_number = int(text_input.text())
                self._save_state()
                self.annotations[index].number = new_number
                self.update()
            except ValueError:
                pass  # Invalid number, ignore


class AnnotationEditor(QDialog):
    """
    Dialog for annotating screenshots.

    Provides tools for adding arrows, rectangles, text, numbered callouts,
    blur regions, and cropping. Supports selecting and moving annotations.
    """

    completed = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.setWindowTitle("Annotate Screenshot")
        self.setModal(True)

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

        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.canvas = AnnotationCanvas(self.original_pixmap)
        self.scroll_area.setWidget(self.canvas)
        layout.addWidget(self.scroll_area, 1)

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

        tools_label = QLabel("Tools:")
        tools_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(tools_label)

        self.tool_group = QButtonGroup(self)
        self.tool_buttons = {}

        tools = [
            ("☛ Select", Tool.SELECT),
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

        layout.addSpacing(10)

        colors_label = QLabel("Color:")
        colors_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(colors_label)

        self.color_group = QButtonGroup(self)
        self.color_buttons = []

        colors = [
            QColor("#FF0000"),
            QColor("#00AA00"),
            QColor("#0066FF"),
            QColor("#FF9900"),
            QColor("#9933FF"),
        ]

        for color in colors:
            btn = ColorButton(color)
            self.color_buttons.append(btn)
            self.color_group.addButton(btn)
            layout.addWidget(btn)

        self.color_buttons[0].setChecked(True)

        layout.addStretch()

        self.undo_btn = QPushButton("↶ Undo")
        self.undo_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 12px;
                font-size: 13px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: #fff;
            }
            QPushButton:hover { background: #f0f0f0; }
            QPushButton:disabled { color: #aaa; background: #f5f5f5; }
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
            QPushButton:hover { background: #f0f0f0; }
            QPushButton:disabled { color: #aaa; background: #f5f5f5; }
        """)
        layout.addWidget(self.redo_btn)

        return toolbar

    def _create_bottom_bar(self) -> QWidget:
        """Create the bottom action bar."""
        bar = QWidget()
        layout = QHBoxLayout(bar)

        self.instructions_label = QLabel(
            "Select: Click to select, drag to move, double-click to edit  •  "
            "Del key: Delete selected"
        )
        self.instructions_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.instructions_label)

        layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 24px;
                font-size: 14px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: #f5f5f5;
            }
            QPushButton:hover { background: #e8e8e8; }
        """)
        cancel_btn.clicked.connect(self._on_cancel)
        layout.addWidget(cancel_btn)

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
            QPushButton:hover { background: #45a049; }
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
        self.scroll_area.setWidget(self.canvas)

    def _on_redo(self):
        """Handle redo button click."""
        self.canvas.redo()
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

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.canvas.delete_selected()
        else:
            super().keyPressEvent(event)
