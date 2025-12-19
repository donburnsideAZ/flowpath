"""
Admin screen for managing categories and tags.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QFrame, QMessageBox, QTabWidget, QDialog,
    QInputDialog, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from ..services import DataService


# Preset colors for categories
PRESET_COLORS = [
    ("#f44336", "Red"),
    ("#4CAF50", "Green"),
    ("#2196F3", "Blue"),
    ("#FFEB3B", "Yellow"),
    ("#FF9800", "Orange"),
]


class ColorPickerDialog(QDialog):
    """Simple color picker with preset colors."""

    def __init__(self, current_color: str = "#4CAF50", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Color")
        self.selected_color = current_color
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)

        label = QLabel("Select a color:")
        label.setStyleSheet("font-size: 14px;")
        layout.addWidget(label)

        # Color buttons in a row
        colors_layout = QHBoxLayout()
        colors_layout.setSpacing(8)

        self.color_buttons = []
        for color_hex, color_name in PRESET_COLORS:
            btn = QPushButton()
            btn.setFixedSize(48, 48)
            btn.setToolTip(color_name)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color_hex};
                    border: 3px solid {"#333" if color_hex == self.selected_color else "#ccc"};
                    border-radius: 8px;
                }}
                QPushButton:hover {{
                    border-color: #666;
                }}
            """)
            btn.clicked.connect(lambda checked, c=color_hex: self._select_color(c))
            colors_layout.addWidget(btn)
            self.color_buttons.append((btn, color_hex))

        layout.addLayout(colors_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _select_color(self, color_hex: str):
        self.selected_color = color_hex
        # Update button borders
        for btn, c in self.color_buttons:
            border_color = "#333" if c == color_hex else "#ccc"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c};
                    border: 3px solid {border_color};
                    border-radius: 8px;
                }}
                QPushButton:hover {{
                    border-color: #666;
                }}
            """)

    def get_color(self) -> str:
        return self.selected_color


class CategoryItem(QFrame):
    """A single category item with edit/delete controls."""
    edit_clicked = pyqtSignal(int)  # Emits category id
    delete_clicked = pyqtSignal(int)  # Emits category id

    def __init__(self, category_id: int, name: str, color: str, usage_count: int):
        super().__init__()
        self.category_id = category_id
        self.name = name
        self.color = color

        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        self.setStyleSheet("""
            CategoryItem {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin: 2px;
            }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)

        # Color indicator
        self.color_label = QLabel()
        self.color_label.setFixedSize(20, 20)
        self.color_label.setStyleSheet(f"""
            background-color: {color};
            border-radius: 4px;
            border: 1px solid #ccc;
        """)
        layout.addWidget(self.color_label)

        # Name
        name_label = QLabel(name)
        name_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(name_label)

        # Usage count
        usage_label = QLabel(f"({usage_count} paths)")
        usage_label.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(usage_label)

        layout.addStretch()

        # Edit button
        edit_btn = QPushButton("Edit")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                padding: 4px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.category_id))
        layout.addWidget(edit_btn)

        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffebee;
                color: #c62828;
                border: 1px solid #ef9a9a;
                padding: 4px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ffcdd2;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.category_id))
        layout.addWidget(delete_btn)

        self.setLayout(layout)


class TagItem(QFrame):
    """A single tag item with edit/delete controls."""
    edit_clicked = pyqtSignal(int)  # Emits tag id
    delete_clicked = pyqtSignal(int)  # Emits tag id

    def __init__(self, tag_id: int, name: str, usage_count: int):
        super().__init__()
        self.tag_id = tag_id
        self.name = name

        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        self.setStyleSheet("""
            TagItem {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin: 2px;
            }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)

        # Tag pill
        tag_pill = QLabel(name)
        tag_pill.setStyleSheet("""
            background-color: #e3f2fd;
            color: #1565c0;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 14px;
        """)
        layout.addWidget(tag_pill)

        # Usage count
        usage_label = QLabel(f"({usage_count} paths)")
        usage_label.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(usage_label)

        layout.addStretch()

        # Rename button
        edit_btn = QPushButton("Rename")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                padding: 4px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.tag_id))
        layout.addWidget(edit_btn)

        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffebee;
                color: #c62828;
                border: 1px solid #ef9a9a;
                padding: 4px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ffcdd2;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.tag_id))
        layout.addWidget(delete_btn)

        self.setLayout(layout)


class AdminScreen(QWidget):
    """Admin screen for managing categories and tags."""
    back_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.data_service = DataService.instance()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # Header
        header_layout = QHBoxLayout()

        back_btn = QPushButton("< Back")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #1976d2;
                font-size: 14px;
                padding: 8px;
            }
            QPushButton:hover {
                color: #1565c0;
            }
        """)
        back_btn.clicked.connect(self.back_clicked.emit)
        header_layout.addWidget(back_btn)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # === TEAM SETTINGS SECTION ===
        team_section = QFrame()
        team_section.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-bottom: 16px;
            }
        """)
        team_layout = QVBoxLayout(team_section)
        team_layout.setContentsMargins(16, 16, 16, 16)
        team_layout.setSpacing(12)

        team_header = QLabel("Team Settings")
        team_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; border: none;")
        team_layout.addWidget(team_header)

        # Team name row
        team_name_row = QHBoxLayout()
        
        team_name_label = QLabel("Team Name:")
        team_name_label.setStyleSheet("font-size: 14px; color: #666; border: none;")
        team_name_row.addWidget(team_name_label)

        self.team_name_input = QLineEdit()
        self.team_name_input.setText(self.data_service.get_team_name())
        self.team_name_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                font-size: 14px;
                border: 1px solid #ccc;
                border-radius: 4px;
                min-width: 250px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)
        team_name_row.addWidget(self.team_name_input)

        save_team_btn = QPushButton("Save")
        save_team_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_team_btn.clicked.connect(self._on_save_team_name)
        team_name_row.addWidget(save_team_btn)

        team_name_row.addStretch()
        team_layout.addLayout(team_name_row)

        main_layout.addWidget(team_section)

        # Tab widget for Categories and Tags
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #fafafa;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 10px 24px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #fafafa;
                font-weight: bold;
            }
        """)

        # Categories tab
        categories_widget = self._create_categories_tab()
        self.tabs.addTab(categories_widget, "Categories")

        # Tags tab
        tags_widget = self._create_tags_tab()
        self.tabs.addTab(tags_widget, "Tags")

        main_layout.addWidget(self.tabs)

        self.setLayout(main_layout)

    def _create_categories_tab(self) -> QWidget:
        """Create the categories management tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)

        # Add category section
        add_layout = QHBoxLayout()

        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("New category name...")
        self.category_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #ccc;
                border-radius: 4px;
            }
        """)
        self.category_input.returnPressed.connect(self._on_add_category)
        add_layout.addWidget(self.category_input)

        # Color picker button
        self.category_color = "#4CAF50"
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(40, 40)
        self.color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.category_color};
                border: 2px solid #ccc;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border-color: #999;
            }}
        """)
        self.color_btn.setToolTip("Choose color")
        self.color_btn.clicked.connect(self._on_pick_color)
        add_layout.addWidget(self.color_btn)

        add_btn = QPushButton("Add Category")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        add_btn.clicked.connect(self._on_add_category)
        add_layout.addWidget(add_btn)

        layout.addLayout(add_layout)

        # Categories list
        self.categories_container = QVBoxLayout()
        self.categories_container.addStretch()

        categories_frame = QFrame()
        categories_frame.setLayout(self.categories_container)
        categories_frame.setStyleSheet("background-color: transparent;")

        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(categories_frame)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        layout.addWidget(scroll)

        widget.setLayout(layout)
        return widget

    def _create_tags_tab(self) -> QWidget:
        """Create the tags management tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)

        # Add tag section
        add_layout = QHBoxLayout()

        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("New tag name...")
        self.tag_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #ccc;
                border-radius: 4px;
            }
        """)
        self.tag_input.returnPressed.connect(self._on_add_tag)
        add_layout.addWidget(self.tag_input)

        add_btn = QPushButton("Add Tag")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        add_btn.clicked.connect(self._on_add_tag)
        add_layout.addWidget(add_btn)

        layout.addLayout(add_layout)

        # Tags list
        self.tags_container = QVBoxLayout()
        self.tags_container.addStretch()

        tags_frame = QFrame()
        tags_frame.setLayout(self.tags_container)
        tags_frame.setStyleSheet("background-color: transparent;")

        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tags_frame)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        layout.addWidget(scroll)

        widget.setLayout(layout)
        return widget

    def refresh(self):
        """Refresh the categories and tags lists."""
        self._refresh_categories()
        self._refresh_tags()
        # Also refresh team name in case it was changed elsewhere
        self.team_name_input.setText(self.data_service.get_team_name())

    def _on_save_team_name(self):
        """Save the team name setting."""
        name = self.team_name_input.text().strip()
        if name:
            self.data_service.set_team_name(name)
            QMessageBox.information(
                self, 
                "Saved", 
                f"Team name updated to '{name}'."
            )
        else:
            QMessageBox.warning(
                self, 
                "Invalid Name", 
                "Team name cannot be empty."
            )

    def _refresh_categories(self):
        """Refresh the categories list."""
        # Clear existing items
        while self.categories_container.count() > 1:
            item = self.categories_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add category items
        categories = self.data_service.get_managed_categories()
        for cat in categories:
            usage_count = self.data_service.get_category_usage_count(cat['name'])
            item = CategoryItem(cat['id'], cat['name'], cat['color'], usage_count)
            item.edit_clicked.connect(self._on_edit_category)
            item.delete_clicked.connect(self._on_delete_category)
            self.categories_container.insertWidget(
                self.categories_container.count() - 1, item
            )

        # Show empty state if no categories
        if not categories:
            empty_label = QLabel("No categories defined yet. Add one above!")
            empty_label.setStyleSheet("color: #888; font-style: italic; font-size: 14px; padding: 20px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.categories_container.insertWidget(0, empty_label)

    def _refresh_tags(self):
        """Refresh the tags list."""
        # Clear existing items
        while self.tags_container.count() > 1:
            item = self.tags_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add tag items
        tags = self.data_service.get_managed_tags()
        for tag in tags:
            usage_count = self.data_service.get_tag_usage_count(tag['name'])
            item = TagItem(tag['id'], tag['name'], usage_count)
            item.edit_clicked.connect(self._on_edit_tag)
            item.delete_clicked.connect(self._on_delete_tag)
            self.tags_container.insertWidget(
                self.tags_container.count() - 1, item
            )

        # Show empty state if no tags
        if not tags:
            empty_label = QLabel("No tags defined yet. Add one above!")
            empty_label.setStyleSheet("color: #888; font-style: italic; font-size: 14px; padding: 20px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tags_container.insertWidget(0, empty_label)

    def _on_pick_color(self):
        """Open color picker for category color."""
        dialog = ColorPickerDialog(self.category_color, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.category_color = dialog.get_color()
            self.color_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.category_color};
                    border: 2px solid #ccc;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    border-color: #999;
                }}
            """)

    def _on_add_category(self):
        """Add a new category."""
        name = self.category_input.text().strip()
        if not name:
            return

        try:
            self.data_service.add_category(name, self.category_color)
            self.category_input.clear()
            self._refresh_categories()
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                QMessageBox.warning(self, "Error", f"Category '{name}' already exists.")
            else:
                QMessageBox.warning(self, "Error", f"Failed to add category: {e}")

    def _on_edit_category(self, category_id: int):
        """Edit a category."""
        categories = self.data_service.get_managed_categories()
        category = next((c for c in categories if c['id'] == category_id), None)
        if not category:
            return

        # Get new name
        new_name, ok = QInputDialog.getText(
            self, "Edit Category", "Category name:",
            text=category['name']
        )
        if not ok or not new_name.strip():
            return

        # Get new color
        dialog = ColorPickerDialog(category['color'], self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_color = dialog.get_color()
        else:
            new_color = category['color']

        try:
            self.data_service.update_category(category_id, new_name.strip(), new_color)
            self._refresh_categories()
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                QMessageBox.warning(self, "Error", f"Category '{new_name}' already exists.")
            else:
                QMessageBox.warning(self, "Error", f"Failed to update category: {e}")

    def _on_delete_category(self, category_id: int):
        """Delete a category."""
        categories = self.data_service.get_managed_categories()
        category = next((c for c in categories if c['id'] == category_id), None)
        if not category:
            return

        usage_count = self.data_service.get_category_usage_count(category['name'])

        msg = f"Delete category '{category['name']}'?"
        if usage_count > 0:
            msg += f"\n\nThis category is used by {usage_count} path(s). They will become uncategorized."

        reply = QMessageBox.question(
            self, "Confirm Delete", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.data_service.delete_category(category_id)
            self._refresh_categories()

    def _on_add_tag(self):
        """Add a new tag."""
        name = self.tag_input.text().strip()
        if not name:
            return

        try:
            self.data_service.add_tag(name)
            self.tag_input.clear()
            self._refresh_tags()
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                QMessageBox.warning(self, "Error", f"Tag '{name}' already exists.")
            else:
                QMessageBox.warning(self, "Error", f"Failed to add tag: {e}")

    def _on_edit_tag(self, tag_id: int):
        """Rename a tag."""
        tags = self.data_service.get_managed_tags()
        tag = next((t for t in tags if t['id'] == tag_id), None)
        if not tag:
            return

        new_name, ok = QInputDialog.getText(
            self, "Rename Tag", "Tag name:",
            text=tag['name']
        )
        if not ok or not new_name.strip():
            return

        try:
            self.data_service.rename_tag(tag_id, new_name.strip())
            self._refresh_tags()
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                QMessageBox.warning(self, "Error", f"Tag '{new_name}' already exists.")
            else:
                QMessageBox.warning(self, "Error", f"Failed to rename tag: {e}")

    def _on_delete_tag(self, tag_id: int):
        """Delete a tag."""
        tags = self.data_service.get_managed_tags()
        tag = next((t for t in tags if t['id'] == tag_id), None)
        if not tag:
            return

        usage_count = self.data_service.get_tag_usage_count(tag['name'])

        msg = f"Delete tag '{tag['name']}'?"
        if usage_count > 0:
            msg += f"\n\nThis tag is used by {usage_count} path(s). It will be removed from them."

        reply = QMessageBox.question(
            self, "Confirm Delete", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.data_service.delete_tag(tag_id)
            self._refresh_tags()
