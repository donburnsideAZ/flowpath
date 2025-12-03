"""
Annotation Editor for FlowPath.

Provides tools for annotating screenshots with arrows, rectangles, text, callouts,
blur regions, and cropping. Supports selecting and moving annotations.

Display is scaled to fit within the editor window while maintaining full resolution
for the saved output.
"""

import math
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QDialog, QLineEdit, QDialogButtonBox, QButtonGroup, QFrame,
    QScrollArea, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal, QPointF
from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QPen, QBrush, QFont,
    QPolygon, QFontMetrics, QCursor, QTransform
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
            min_x = min(self.start.x(), self.end.x()) - 10
            min_y = min(self.start.y(), self.end.y()) - 10
            max_x = max(self.start.x(), self.end.x()) + 10
            max_y = max(self.start.y(), self.end.y()) + 10
            return QRect(min_x, min_y, max_x - min_x, max_y - min_y)
        elif self.tool == Tool.RECTANGLE:
            return QRect(self.start, self.end).normalized().adjusted(-5, -5, 5, 5)
        elif self.tool == Tool.TEXT:
            return QRect(self.start.x() - 5, self.start.y() - 25, 200, 30)
        elif self.tool == Tool.CALLOUT:
            return QRect(self.start.x() - 18, self.start.y() - 18, 36, 36)
        return QRect()

    def contains_point(self, point: QPoint) -> bool:
        """Check if a point is within this annotation."""
        if self.tool == Tool.CALLOUT:
            dx = point.x() - self.start.x()
            dy = point.y() - self.start.y()
            return (dx * dx + dy * dy) <= (18 * 18)
        elif self.tool == Tool.ARROW:
            return self._point_near_line(point, self.start, self.end, 10)
        else:
            return self.get_bounding_rect().contains(point)

    def _point_near_line(self, point: QPoint, start: QPoint, end: QPoint, threshold: float) -> bool:
        """Check if point is within threshold distance of line segment."""
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        length_sq = dx * dx + dy * dy

        if length_sq == 0:
            return (point.x() - start.x()) ** 2 + (point.y() - start.y()) ** 2 <= threshold ** 2

        t = max(0, min(1, ((point.x() - start.x()) * dx + (point.y() - start.y()) * dy) / length_sq))
        proj_x = start.x() + t * dx
        proj_y = start.y() + t * dy

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
                color: #333;
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
        return CanvasState(
            pixmap=self.pixmap.copy(),
            annotations=[a.copy() for a in self.annotations],
            callout_counter=self.callout_counter
        )


class ScaledAnnotationCanvas(QWidget):
    """
    Canvas widget for displaying and annotating screenshots.
    
    Displays a scaled version of the image to fit the editor window,
    but maintains full resolution coordinates for annotations.
    """

    state_changed = pyqtSignal()

    # Maximum display dimensions (leaving room for toolbar/buttons)
    MAX_DISPLAY_WIDTH = 950
    MAX_DISPLAY_HEIGHT = 550

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

        # Calculate scale factor
        self._update_scale()
        self.setMouseTracking(True)

    def _update_scale(self):
        """Calculate scale factor to fit image within max display size."""
        img_w = self.base_pixmap.width()
        img_h = self.base_pixmap.height()

        # Calculate scale to fit within bounds
        scale_w = self.MAX_DISPLAY_WIDTH / img_w if img_w > self.MAX_DISPLAY_WIDTH else 1.0
        scale_h = self.MAX_DISPLAY_HEIGHT / img_h if img_h > self.MAX_DISPLAY_HEIGHT else 1.0
        self.scale = min(scale_w, scale_h, 1.0)  # Never scale up

        # Set widget size to scaled dimensions
        display_w = int(img_w * self.scale)
        display_h = int(img_h * self.scale)
        self.setFixedSize(display_w, display_h)

    def _to_image_coords(self, widget_point: QPoint) -> QPoint:
        """Convert widget coordinates to full-resolution image coordinates."""
        return QPoint(
            int(widget_point.x() / self.scale),
            int(widget_point.y() / self.scale)
        )

    def _to_widget_coords(self, image_point: QPoint) -> QPoint:
        """Convert full-resolution image coordinates to widget coordinates."""
        return QPoint(
            int(image_point.x() * self.scale),
            int(image_point.y() * self.scale)
        )

    def _save_state(self):
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
        self.base_pixmap = state.pixmap.copy()
        self.annotations = [a.copy() for a in state.annotations]
        self.callout_counter = state.callout_counter
        self.selected_index = None
        self._update_scale()
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
        self.current_tool = tool
        if tool != Tool.SELECT:
            self.selected_index = None
            self.update()

    def set_color(self, color: QColor):
        self.current_color = color

    def delete_selected(self):
        if self.selected_index is not None and 0 <= self.selected_index < len(self.annotations):
            self._save_state()
            del self.annotations[self.selected_index]
            self.selected_index = None
            self.update()

    def _find_annotation_at(self, image_point: QPoint) -> Optional[int]:
        """Find annotation at the given image coordinates."""
        for i in range(len(self.annotations) - 1, -1, -1):
            if self.annotations[i].contains_point(image_point):
                return i
        return None

    def add_text_annotation(self, pos: QPoint, text: str):
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
        self._update_scale()
        self.update()

    def apply_blur(self, rect: QRect):
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
        """Return the full-resolution pixmap with all annotations rendered."""
        result = self.base_pixmap.copy()
        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw at full resolution (scale = 1.0)
        for annotation in self.annotations:
            self._draw_annotation(painter, annotation, selected=False, scale=1.0)

        painter.end()
        return result

    def paintEvent(self, event):
        """Paint the scaled canvas with image and annotations."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Draw scaled pixmap
        scaled_pixmap = self.base_pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        painter.drawPixmap(0, 0, scaled_pixmap)

        # Draw annotations at display scale
        for i, annotation in enumerate(self.annotations):
            is_selected = (i == self.selected_index)
            self._draw_annotation(painter, annotation, selected=is_selected, scale=self.scale)

        if self.current_annotation:
            self._draw_annotation(painter, self.current_annotation, selected=False, scale=self.scale)

            if self.current_annotation.tool == Tool.CROP:
                self._draw_crop_overlay(painter, self.current_annotation)

        painter.end()

    def _draw_crop_overlay(self, painter: QPainter, annotation: Annotation):
        """Draw semi-transparent overlay outside crop area."""
        # Convert to widget coordinates
        start = self._to_widget_coords(annotation.start)
        end = self._to_widget_coords(annotation.end)
        rect = QRect(start, end).normalized()
        
        overlay = QColor(0, 0, 0, 150)
        canvas_rect = self.rect()

        painter.fillRect(QRect(0, 0, canvas_rect.width(), rect.top()), overlay)
        painter.fillRect(QRect(0, rect.bottom(), canvas_rect.width(), canvas_rect.height() - rect.bottom()), overlay)
        painter.fillRect(QRect(0, rect.top(), rect.left(), rect.height()), overlay)
        painter.fillRect(QRect(rect.right(), rect.top(), canvas_rect.width() - rect.right(), rect.height()), overlay)

    def _draw_annotation(self, painter: QPainter, annotation: Annotation, selected: bool = False, scale: float = 1.0):
        """Draw a single annotation at the given scale."""
        if annotation.tool == Tool.ARROW:
            self._draw_arrow(painter, annotation, scale)
        elif annotation.tool == Tool.RECTANGLE:
            self._draw_rectangle(painter, annotation, scale)
        elif annotation.tool == Tool.TEXT:
            self._draw_text(painter, annotation, scale)
        elif annotation.tool == Tool.CALLOUT:
            self._draw_callout(painter, annotation, scale)
        elif annotation.tool == Tool.BLUR:
            self._draw_blur_preview(painter, annotation, scale)
        elif annotation.tool == Tool.CROP:
            self._draw_crop_preview(painter, annotation, scale)

        if selected:
            self._draw_selection_highlight(painter, annotation, scale)

    def _scale_point(self, point: QPoint, scale: float) -> QPoint:
        """Scale a point by the given factor."""
        return QPoint(int(point.x() * scale), int(point.y() * scale))

    def _draw_selection_highlight(self, painter: QPainter, annotation: Annotation, scale: float):
        rect = annotation.get_bounding_rect()
        # Scale the rect
        scaled_rect = QRect(
            int(rect.x() * scale),
            int(rect.y() * scale),
            int(rect.width() * scale),
            int(rect.height() * scale)
        )
        
        pen = QPen(QColor("#0066FF"), 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(scaled_rect)

        handle_size = 6
        painter.setBrush(QBrush(QColor("#0066FF")))
        painter.setPen(Qt.PenStyle.NoPen)

        corners = [
            scaled_rect.topLeft(),
            scaled_rect.topRight(),
            scaled_rect.bottomLeft(),
            scaled_rect.bottomRight()
        ]
        for corner in corners:
            painter.drawRect(
                corner.x() - handle_size // 2,
                corner.y() - handle_size // 2,
                handle_size,
                handle_size
            )

    def _draw_arrow(self, painter: QPainter, annotation: Annotation, scale: float):
        pen_width = max(2, int(3 * scale))
        pen = QPen(annotation.color, pen_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        start = self._scale_point(annotation.start, scale)
        end = self._scale_point(annotation.end, scale)

        painter.drawLine(start, end)

        dx = end.x() - start.x()
        dy = end.y() - start.y()
        length = math.sqrt(dx * dx + dy * dy)

        if length > 0:
            dx /= length
            dy /= length

            head_length = max(10, int(15 * scale))
            head_width = max(5, int(8 * scale))

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

    def _draw_rectangle(self, painter: QPainter, annotation: Annotation, scale: float):
        pen_width = max(2, int(3 * scale))
        pen = QPen(annotation.color, pen_width)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        start = self._scale_point(annotation.start, scale)
        end = self._scale_point(annotation.end, scale)
        rect = QRect(start, end).normalized()
        painter.drawRect(rect)

    def _draw_text(self, painter: QPainter, annotation: Annotation, scale: float):
        font_size = max(10, int(14 * scale))
        font = QFont("Arial", font_size, QFont.Weight.Bold)
        painter.setFont(font)

        metrics = QFontMetrics(font)
        text_rect = metrics.boundingRect(annotation.text)

        pos = self._scale_point(annotation.start, scale)

        bg_rect = QRect(
            pos.x() - 2,
            pos.y() - text_rect.height(),
            text_rect.width() + 6,
            text_rect.height() + 4
        )

        painter.fillRect(bg_rect, QColor(255, 255, 255, 200))
        painter.setPen(annotation.color)
        painter.drawText(pos, annotation.text)

    def _draw_callout(self, painter: QPainter, annotation: Annotation, scale: float):
        radius = max(10, int(14 * scale))
        center = self._scale_point(annotation.start, scale)

        pen_width = max(1, int(2 * scale))
        painter.setPen(QPen(annotation.color, pen_width))
        painter.setBrush(QBrush(annotation.color))
        painter.drawEllipse(center, radius, radius)

        font_size = max(8, int(12 * scale))
        font = QFont("Arial", font_size, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(Qt.GlobalColor.white)

        text = str(annotation.number)
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(text)
        text_height = metrics.height()

        text_x = center.x() - text_width // 2
        text_y = center.y() + text_height // 4
        painter.drawText(text_x, text_y, text)

    def _draw_blur_preview(self, painter: QPainter, annotation: Annotation, scale: float):
        pen = QPen(QColor("#888888"), 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(QColor(128, 128, 128, 50))

        start = self._scale_point(annotation.start, scale)
        end = self._scale_point(annotation.end, scale)
        rect = QRect(start, end).normalized()
        painter.drawRect(rect)

        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.setPen(QColor("#666666"))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "BLUR")

    def _draw_crop_preview(self, painter: QPainter, annotation: Annotation, scale: float):
        pen = QPen(QColor("#4CAF50"), 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        start = self._scale_point(annotation.start, scale)
        end = self._scale_point(annotation.end, scale)
        rect = QRect(start, end).normalized()
        painter.drawRect(rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            widget_pos = event.pos()
            image_pos = self._to_image_coords(widget_pos)

            if self.current_tool == Tool.SELECT:
                clicked_index = self._find_annotation_at(image_pos)
                if clicked_index is not None:
                    self.selected_index = clicked_index
                    self.dragging = True
                    self.drag_start = image_pos
                else:
                    self.selected_index = None
                self.update()

            elif self.current_tool == Tool.TEXT:
                self._show_text_dialog(image_pos)

            elif self.current_tool == Tool.CALLOUT:
                self.add_callout_annotation(image_pos)

            else:
                self.current_annotation = Annotation(
                    tool=self.current_tool,
                    color=QColor(self.current_color),
                    start=image_pos,
                    end=image_pos
                )
                self.update()

    def mouseMoveEvent(self, event):
        widget_pos = event.pos()
        image_pos = self._to_image_coords(widget_pos)

        if self.dragging and self.selected_index is not None and self.drag_start is not None:
            delta = QPoint(image_pos.x() - self.drag_start.x(), image_pos.y() - self.drag_start.y())
            self.annotations[self.selected_index].move_by(delta)
            self.drag_start = image_pos
            self.update()

        elif self.current_annotation:
            self.current_annotation.end = image_pos
            self.update()

        if self.current_tool == Tool.SELECT:
            if self._find_annotation_at(image_pos) is not None:
                self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            else:
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.dragging:
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
        if event.button() == Qt.MouseButton.LeftButton and self.current_tool == Tool.SELECT:
            image_pos = self._to_image_coords(event.pos())
            clicked_index = self._find_annotation_at(image_pos)

            if clicked_index is not None:
                annotation = self.annotations[clicked_index]

                if annotation.tool == Tool.TEXT:
                    self._edit_text_annotation(clicked_index)
                elif annotation.tool == Tool.CALLOUT:
                    self._edit_callout_annotation(clicked_index)

    def _show_text_dialog(self, pos: QPoint, initial_text: str = ""):
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
                pass


class AnnotationEditor(QDialog):
    """
    Dialog for annotating screenshots.

    Displays a scaled view of the image that fits within the dialog,
    while saving annotations at full resolution.
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
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Canvas container with centered alignment
        canvas_container = QWidget()
        canvas_container.setStyleSheet("background-color: #404040;")
        container_layout = QHBoxLayout(canvas_container)
        container_layout.setContentsMargins(10, 10, 10, 10)

        self.canvas = ScaledAnnotationCanvas(self.original_pixmap)
        container_layout.addStretch()
        container_layout.addWidget(self.canvas)
        container_layout.addStretch()

        layout.addWidget(canvas_container, 1)

        bottom_bar = self._create_bottom_bar()
        layout.addWidget(bottom_bar)

    def _create_toolbar(self) -> QWidget:
        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame {
                background: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
            }
            QLabel {
                color: #333;
            }
        """)
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(10, 5, 10, 5)

        tools_label = QLabel("Tools:")
        tools_label.setStyleSheet("font-weight: bold; color: #333;")
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
        colors_label.setStyleSheet("font-weight: bold; color: #333;")
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
                color: #333;
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
                color: #333;
            }
            QPushButton:hover { background: #f0f0f0; }
            QPushButton:disabled { color: #aaa; background: #f5f5f5; }
        """)
        layout.addWidget(self.redo_btn)

        return toolbar

    def _create_bottom_bar(self) -> QWidget:
        bar = QWidget()
        bar.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(bar)

        # Show scale percentage
        scale_pct = int(self.canvas.scale * 100)
        self.instructions_label = QLabel(
            f"Viewing at {scale_pct}%  •  "
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
                color: #333;
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
        self.tool_group.buttonClicked.connect(self._on_tool_changed)
        self.color_group.buttonClicked.connect(self._on_color_changed)
        self.undo_btn.clicked.connect(self._on_undo)
        self.redo_btn.clicked.connect(self._on_redo)
        self.canvas.state_changed.connect(self._update_undo_redo_buttons)

    def _adjust_dialog_size(self):
        """Set dialog size to fit the scaled canvas plus chrome."""
        canvas_size = self.canvas.size()
        
        # Add space for toolbar, bottom bar, margins
        width = canvas_size.width() + 60  # margins
        height = canvas_size.height() + 150  # toolbar + bottom bar + margins

        # Ensure minimum size
        width = max(width, 800)
        height = max(height, 500)

        self.setFixedSize(width, height)

        # Center on screen
        screen = QApplication.primaryScreen()
        if screen:
            screen_rect = screen.availableGeometry()
            self.move(
                screen_rect.center().x() - width // 2,
                screen_rect.center().y() - height // 2
            )

    def _update_undo_redo_buttons(self):
        self.undo_btn.setEnabled(self.canvas.can_undo())
        self.redo_btn.setEnabled(self.canvas.can_redo())

    def _on_tool_changed(self, button):
        if isinstance(button, ToolButton):
            self.canvas.set_tool(button.tool)

    def _on_color_changed(self, button):
        if isinstance(button, ColorButton):
            self.canvas.set_color(button.color)
            for btn in self.color_buttons:
                btn._update_style()

    def _on_undo(self):
        self.canvas.undo()

    def _on_redo(self):
        self.canvas.redo()

    def _on_save(self):
        """Save the annotated image at full resolution."""
        annotated = self.canvas.get_annotated_pixmap()

        if annotated.save(self.image_path, 'PNG'):
            self.completed.emit(self.image_path)
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to save annotated image.")

    def _on_cancel(self):
        self.cancelled.emit()
        self.reject()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.canvas.delete_selected()
        else:
            super().keyPressEvent(event)
