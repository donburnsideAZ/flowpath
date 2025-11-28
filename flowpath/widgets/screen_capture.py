"""
ScreenCapture utility for FlowPath.

Provides screen capture functionality with full screen and region select modes.
"""

import os
import sys
import uuid
import logging
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import QApplication, QWidget, QMessageBox
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect
from PyQt6.QtGui import QScreen, QPixmap, QPainter, QColor, QPen, QCursor

logger = logging.getLogger(__name__)


class ScreenCapture(QWidget):
    """
    Screen capture utility that supports full screen and region selection modes.

    Signals:
        captured(str): Emitted when capture is complete, with the file path
        cancelled(): Emitted when capture is cancelled

    Usage:
        # Full screen capture
        capture = ScreenCapture()
        capture.captured.connect(on_screenshot_taken)
        capture.capture_full_screen(parent_window)

        # Region select (to be implemented)
        capture.capture_region(parent_window)
    """

    captured = pyqtSignal(str)  # Emits file path of saved screenshot
    cancelled = pyqtSignal()

    def __init__(self, save_directory: Optional[str] = None):
        super().__init__()
        self.save_directory = save_directory or self._get_default_save_dir()
        self.parent_window = None
        self._ensure_save_directory()

        # For region selection
        self.selecting = False
        self.selection_start = None
        self.selection_end = None
        self.screen_pixmap = None

    def _get_default_save_dir(self) -> str:
        """Get the default directory for saving screenshots."""
        if os.name == 'posix':
            data_home = os.environ.get('XDG_DATA_HOME',
                                       os.path.expanduser('~/.local/share'))
        else:
            data_home = os.environ.get('APPDATA', os.path.expanduser('~'))

        return os.path.join(data_home, 'flowpath', 'screenshots')

    def _ensure_save_directory(self):
        """Ensure the save directory exists."""
        os.makedirs(self.save_directory, exist_ok=True)

    def _generate_filename(self) -> str:
        """Generate a unique filename for the screenshot."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        return f"screenshot_{timestamp}_{unique_id}.png"

    def _save_pixmap(self, pixmap: QPixmap) -> Optional[str]:
        """Save a pixmap to a file and return the path."""
        if pixmap.isNull():
            return None

        filename = self._generate_filename()
        filepath = os.path.join(self.save_directory, filename)

        if pixmap.save(filepath, 'PNG'):
            return filepath
        return None

    def capture_full_screen(self, parent_window: Optional[QWidget] = None, delay_ms: int = 300):
        """
        Capture the full screen.

        Args:
            parent_window: Window to minimize before capture and restore after
            delay_ms: Delay before capture (to allow window to minimize)
        """
        self.parent_window = parent_window

        # Minimize parent window if provided
        if parent_window:
            parent_window.showMinimized()

        # Delay to allow window to minimize
        QTimer.singleShot(delay_ms, self._do_full_screen_capture)

    def _do_full_screen_capture(self):
        """Perform the actual full screen capture."""
        try:
            screen = QApplication.primaryScreen()
            if screen is None:
                logger.error("No primary screen available")
                self._restore_and_emit_error("No screen available for capture.")
                return

            # Capture the screen
            pixmap = screen.grabWindow(0)

            # Check if capture succeeded (can fail silently on macOS without permissions)
            if pixmap.isNull() or pixmap.width() == 0 or pixmap.height() == 0:
                logger.error("Screen capture returned empty pixmap - likely permissions issue")
                self._restore_and_emit_error(
                    "Screen capture failed.\n\n"
                    "On macOS, please grant Screen Recording permission:\n"
                    "System Preferences → Security & Privacy → Privacy → Screen Recording\n\n"
                    "Add and enable this application, then restart it."
                )
                return

            # Save the screenshot
            filepath = self._save_pixmap(pixmap)

            # Restore parent window
            if self.parent_window:
                self.parent_window.showNormal()
                self.parent_window.activateWindow()

            # Emit result
            if filepath:
                self.captured.emit(filepath)
            else:
                self._restore_and_emit_error("Failed to save screenshot.")

        except Exception as e:
            logger.exception("Error during screen capture")
            self._restore_and_emit_error(
                f"Screen capture error: {str(e)}\n\n"
                "On macOS, ensure Screen Recording permission is granted."
            )

    def capture_region(self, parent_window: Optional[QWidget] = None, delay_ms: int = 300):
        """
        Capture a region of the screen selected by the user.

        Args:
            parent_window: Window to minimize before capture and restore after
            delay_ms: Delay before showing selection overlay
        """
        self.parent_window = parent_window

        # Minimize parent window if provided
        if parent_window:
            parent_window.showMinimized()

        # Delay to allow window to minimize
        QTimer.singleShot(delay_ms, self._show_region_selector)

    def _show_region_selector(self):
        """Show the region selection overlay."""
        try:
            screen = QApplication.primaryScreen()
            if screen is None:
                logger.error("No primary screen available for region capture")
                self._restore_and_emit_error("No screen available for capture.")
                return

            # Capture the full screen first (we'll crop later)
            self.screen_pixmap = screen.grabWindow(0)

            # Check if capture succeeded
            if self.screen_pixmap.isNull() or self.screen_pixmap.width() == 0:
                logger.error("Region capture: screen grab returned empty pixmap")
                self._restore_and_emit_error(
                    "Screen capture failed.\n\n"
                    "On macOS, please grant Screen Recording permission:\n"
                    "System Preferences → Security & Privacy → Privacy → Screen Recording\n\n"
                    "Add and enable this application, then restart it."
                )
                return

            # Set up this widget as a fullscreen overlay
            screen_geometry = screen.geometry()
            self.setGeometry(screen_geometry)
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.Tool
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

            # Reset selection state
            self.selecting = False
            self.selection_start = None
            self.selection_end = None

            # Show fullscreen
            self.showFullScreen()

        except Exception as e:
            logger.exception("Error showing region selector")
            self._restore_and_emit_error(
                f"Screen capture error: {str(e)}\n\n"
                "On macOS, ensure Screen Recording permission is granted."
            )

    def paintEvent(self, event):
        """Paint the selection overlay."""
        if self.screen_pixmap is None:
            return

        painter = QPainter(self)

        # Draw the captured screen
        painter.drawPixmap(0, 0, self.screen_pixmap)

        # Draw semi-transparent overlay
        overlay = QColor(0, 0, 0, 100)
        painter.fillRect(self.rect(), overlay)

        # Draw selection rectangle if selecting
        if self.selection_start and self.selection_end:
            selection_rect = QRect(self.selection_start, self.selection_end).normalized()

            # Clear the overlay in the selection area (show original image)
            painter.drawPixmap(selection_rect, self.screen_pixmap, selection_rect)

            # Draw selection border
            pen = QPen(QColor(76, 175, 80), 2)  # Green border
            painter.setPen(pen)
            painter.drawRect(selection_rect)

        # Draw instructions
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(20, 30, "Click and drag to select a region. Press ESC to cancel.")

        painter.end()

    def mousePressEvent(self, event):
        """Handle mouse press to start selection."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.selecting = True
            self.selection_start = event.pos()
            self.selection_end = event.pos()
            self.update()

    def mouseMoveEvent(self, event):
        """Handle mouse move to update selection."""
        if self.selecting:
            self.selection_end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release to complete selection."""
        if event.button() == Qt.MouseButton.LeftButton and self.selecting:
            self.selecting = False
            self.selection_end = event.pos()
            self._complete_region_capture()

    def keyPressEvent(self, event):
        """Handle key press for cancellation."""
        if event.key() == Qt.Key.Key_Escape:
            self._restore_and_cancel()

    def _complete_region_capture(self):
        """Complete the region capture and save the cropped image."""
        if self.selection_start is None or self.selection_end is None:
            self._restore_and_cancel()
            return

        # Calculate selection rectangle
        selection_rect = QRect(self.selection_start, self.selection_end).normalized()

        # Minimum size check
        if selection_rect.width() < 10 or selection_rect.height() < 10:
            self._restore_and_cancel()
            return

        # Crop the pixmap
        cropped = self.screen_pixmap.copy(selection_rect)

        # Hide the overlay
        self.hide()

        # Save the cropped screenshot
        filepath = self._save_pixmap(cropped)

        # Restore parent window
        if self.parent_window:
            self.parent_window.showNormal()
            self.parent_window.activateWindow()

        # Emit result
        if filepath:
            self.captured.emit(filepath)
        else:
            self.cancelled.emit()

        # Clean up
        self.screen_pixmap = None

    def _restore_and_cancel(self):
        """Restore parent window and emit cancelled signal."""
        self.hide()
        if self.parent_window:
            self.parent_window.showNormal()
            self.parent_window.activateWindow()
        self.cancelled.emit()
        self.screen_pixmap = None

    def _restore_and_emit_error(self, message: str):
        """Restore parent window, show error message, and emit cancelled signal."""
        self.hide()
        if self.parent_window:
            self.parent_window.showNormal()
            self.parent_window.activateWindow()

        # Show error dialog
        QMessageBox.warning(
            self.parent_window,
            "Screen Capture Error",
            message
        )
        self.cancelled.emit()
        self.screen_pixmap = None
