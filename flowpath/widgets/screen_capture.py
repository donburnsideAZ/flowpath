"""
ScreenCapture utility for FlowPath.

Provides screen capture functionality with full screen and region select modes.
Uses native macOS screencapture command on Darwin for reliability.
"""

import os
import sys
import uuid
import subprocess
import logging
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import QApplication, QWidget, QMessageBox
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QCursor

logger = logging.getLogger(__name__)


def is_macos() -> bool:
    """Check if running on macOS."""
    return sys.platform == 'darwin'


class ScreenCapture(QWidget):
    """
    Screen capture utility that supports full screen and region selection modes.

    On macOS, uses native screencapture command for reliability.
    On other platforms, uses Qt's grabWindow.

    Signals:
        captured(str): Emitted when capture is complete, with the file path
        cancelled(): Emitted when capture is cancelled

    Usage:
        capture = ScreenCapture()
        capture.captured.connect(on_screenshot_taken)
        capture.capture_full_screen(parent_window)
        capture.capture_region(parent_window)
    """

    captured = pyqtSignal(str)  # Emits file path of saved screenshot
    cancelled = pyqtSignal()

    def __init__(self, save_directory: Optional[str] = None):
        super().__init__()
        self.save_directory = save_directory or self._get_default_save_dir()
        self.parent_window = None
        self._ensure_save_directory()

        # For region selection (non-macOS)
        self.selecting = False
        self.selection_start = None
        self.selection_end = None
        self.screen_pixmap = None

    def _get_default_save_dir(self) -> str:
        """Get the default directory for saving screenshots."""
        if sys.platform == 'darwin':
            # macOS: use ~/Library/Application Support
            data_home = os.path.expanduser('~/Library/Application Support')
        elif os.name == 'posix':
            data_home = os.environ.get('XDG_DATA_HOME',
                                       os.path.expanduser('~/.local/share'))
        else:
            data_home = os.environ.get('APPDATA', os.path.expanduser('~'))

        return os.path.join(data_home, 'flowpath', 'screenshots')

    def _ensure_save_directory(self):
        """Ensure the save directory exists."""
        os.makedirs(self.save_directory, exist_ok=True)

    def _generate_filepath(self) -> str:
        """Generate a unique filepath for the screenshot."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        filename = f"screenshot_{timestamp}_{unique_id}.png"
        return os.path.join(self.save_directory, filename)

    def _save_pixmap(self, pixmap: QPixmap) -> Optional[str]:
        """Save a pixmap to a file and return the path."""
        if pixmap.isNull():
            return None

        filepath = self._generate_filepath()
        if pixmap.save(filepath, 'PNG'):
            return filepath
        return None

    # ========== FULL SCREEN CAPTURE ==========

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
        if is_macos():
            self._do_macos_full_screen_capture()
        else:
            self._do_qt_full_screen_capture()

    def _do_macos_full_screen_capture(self):
        """Use native macOS screencapture command."""
        try:
            filepath = self._generate_filepath()

            # Run screencapture: -x = no sound
            result = subprocess.run(
                ['screencapture', '-x', filepath],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Restore parent window
            if self.parent_window:
                self.parent_window.showNormal()
                self.parent_window.activateWindow()

            if result.returncode == 0 and os.path.exists(filepath):
                self.captured.emit(filepath)
            else:
                error_msg = result.stderr or "Unknown error"
                logger.error(f"macOS screencapture failed: {error_msg}")
                self._show_macos_permission_error()

        except subprocess.TimeoutExpired:
            logger.error("screencapture timed out")
            self._restore_and_emit_error("Screen capture timed out.")
        except FileNotFoundError:
            logger.error("screencapture command not found")
            self._restore_and_emit_error("screencapture command not found.")
        except Exception as e:
            logger.exception("Error during macOS screen capture")
            self._restore_and_emit_error(f"Screen capture error: {str(e)}")

    def _do_qt_full_screen_capture(self):
        """Use Qt grabWindow for non-macOS platforms."""
        try:
            screen = QApplication.primaryScreen()
            if screen is None:
                logger.error("No primary screen available")
                self._restore_and_emit_error("No screen available for capture.")
                return

            pixmap = screen.grabWindow(0)

            if pixmap.isNull() or pixmap.width() == 0 or pixmap.height() == 0:
                logger.error("Screen capture returned empty pixmap")
                self._restore_and_emit_error("Screen capture failed.")
                return

            filepath = self._save_pixmap(pixmap)

            if self.parent_window:
                self.parent_window.showNormal()
                self.parent_window.activateWindow()

            if filepath:
                self.captured.emit(filepath)
            else:
                self._restore_and_emit_error("Failed to save screenshot.")

        except Exception as e:
            logger.exception("Error during screen capture")
            self._restore_and_emit_error(f"Screen capture error: {str(e)}")

    # ========== REGION CAPTURE ==========

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
        QTimer.singleShot(delay_ms, self._do_region_capture)

    def _do_region_capture(self):
        """Perform the region capture."""
        if is_macos():
            self._do_macos_region_capture()
        else:
            self._show_region_selector()

    def _do_macos_region_capture(self):
        """Use native macOS screencapture with interactive selection."""
        try:
            filepath = self._generate_filepath()

            # Run screencapture: -x = no sound, -i = interactive (region select)
            result = subprocess.run(
                ['screencapture', '-x', '-i', filepath],
                capture_output=True,
                text=True,
                timeout=120  # Longer timeout for user interaction
            )

            # Restore parent window
            if self.parent_window:
                self.parent_window.showNormal()
                self.parent_window.activateWindow()

            if result.returncode == 0 and os.path.exists(filepath):
                self.captured.emit(filepath)
            elif result.returncode == 1:
                # User cancelled (pressed Escape)
                logger.info("User cancelled region selection")
                self.cancelled.emit()
            else:
                error_msg = result.stderr or "Unknown error"
                logger.error(f"macOS screencapture region failed: {error_msg}")
                self._show_macos_permission_error()

        except subprocess.TimeoutExpired:
            logger.error("screencapture region timed out")
            self._restore_and_emit_error("Screen capture timed out.")
        except FileNotFoundError:
            logger.error("screencapture command not found")
            self._restore_and_emit_error("screencapture command not found.")
        except Exception as e:
            logger.exception("Error during macOS region capture")
            self._restore_and_emit_error(f"Screen capture error: {str(e)}")

    def _show_region_selector(self):
        """Show the Qt-based region selection overlay (non-macOS)."""
        try:
            screen = QApplication.primaryScreen()
            if screen is None:
                logger.error("No primary screen available for region capture")
                self._restore_and_emit_error("No screen available for capture.")
                return

            self.screen_pixmap = screen.grabWindow(0)

            if self.screen_pixmap.isNull() or self.screen_pixmap.width() == 0:
                logger.error("Region capture: screen grab returned empty pixmap")
                self._restore_and_emit_error("Screen capture failed.")
                return

            screen_geometry = screen.geometry()
            self.setGeometry(screen_geometry)
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.Tool
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

            self.selecting = False
            self.selection_start = None
            self.selection_end = None

            self.showFullScreen()

        except Exception as e:
            logger.exception("Error showing region selector")
            self._restore_and_emit_error(f"Screen capture error: {str(e)}")

    # ========== QT REGION SELECTION UI (non-macOS) ==========

    def paintEvent(self, event):
        """Paint the selection overlay."""
        if self.screen_pixmap is None:
            return

        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.screen_pixmap)

        overlay = QColor(0, 0, 0, 100)
        painter.fillRect(self.rect(), overlay)

        if self.selection_start and self.selection_end:
            selection_rect = QRect(self.selection_start, self.selection_end).normalized()
            painter.drawPixmap(selection_rect, self.screen_pixmap, selection_rect)

            pen = QPen(QColor(76, 175, 80), 2)
            painter.setPen(pen)
            painter.drawRect(selection_rect)

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

        selection_rect = QRect(self.selection_start, self.selection_end).normalized()

        if selection_rect.width() < 10 or selection_rect.height() < 10:
            self._restore_and_cancel()
            return

        cropped = self.screen_pixmap.copy(selection_rect)
        self.hide()

        filepath = self._save_pixmap(cropped)

        if self.parent_window:
            self.parent_window.showNormal()
            self.parent_window.activateWindow()

        if filepath:
            self.captured.emit(filepath)
        else:
            self.cancelled.emit()

        self.screen_pixmap = None

    # ========== HELPERS ==========

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

        QMessageBox.warning(
            self.parent_window,
            "Screen Capture Error",
            message
        )
        self.cancelled.emit()
        self.screen_pixmap = None

    def _show_macos_permission_error(self):
        """Show macOS-specific permission error."""
        self._restore_and_emit_error(
            "Screen capture failed.\n\n"
            "Please grant Screen Recording permission:\n"
            "System Settings → Privacy & Security → Screen Recording\n\n"
            "Enable this application, then try again."
        )
