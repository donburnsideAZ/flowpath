# FlowPath Development Recap

## What is FlowPath?

A PyQt6 desktop application for creating step-by-step instruction paths with annotated screenshots. Designed for the Axway Documentation Team to create visual guides and tutorials.

---

## Features Implemented

### 1. Data Model & Persistence Layer
- **Models**: `Path` and `Step` dataclasses
- **Database**: SQLite with schema for paths and steps tables
- **Repositories**: Full CRUD operations for both entities
- **DataService**: Singleton pattern for centralized data access
- **Tests**: 25 passing tests for the persistence layer

### 2. UI Screens Wired to Database
- **HomeScreen**: Displays saved paths with search and category filtering
- **PathEditorScreen**: Create/edit paths with metadata (title, category, tags, description)
- **StepCreatorScreen**: Add steps with screenshots and instructions
- **PathReaderScreen**: View completed paths in presentation mode

### 3. Markdown Formatting
- **MarkdownTextEdit**: Text editor with formatting toolbar
  - Bold (**text**)
  - Italic (*text*)
  - Links ([text](url))
- **MarkdownLabel**: Renders Markdown as styled HTML
- Available in all text editing areas (path descriptions, step instructions)

### 4. Screen Capture
- **Full Screen**: Captures entire screen
- **Select Region**: Interactive crosshair selection (macOS native)
- Uses native `screencapture` command on macOS for reliability
- Falls back to Qt grabWindow on other platforms
- App minimizes during capture, restores after

### 5. Screenshot Annotation Editor
- **Arrow Tool**: Click and drag to draw arrows pointing at UI elements
- **Rectangle Tool**: Click and drag to highlight areas with boxes
- **Text Tool**: Click to place text labels with readable backgrounds
- **Callout Tool**: Click to place numbered circles (①②③) that auto-increment
- **Blur Tool**: Pixelate regions to hide sensitive data
- **Crop Tool**: Trim screenshots to focus area
- **Colors**: Red, Green, Blue, Orange, Purple
- **Undo/Redo**: Full state-based history (up to 50 states)
- **Save/Cancel**: Overwrites screenshot with annotations or keeps original

---

## Project Structure

```
flowpath/
├── main.py                     # App entry point, navigation
├── flowpath/
│   ├── models/
│   │   ├── path.py            # Path dataclass
│   │   └── step.py            # Step dataclass
│   ├── data/
│   │   ├── database.py        # SQLite connection & schema
│   │   ├── path_repository.py # Path CRUD operations
│   │   └── step_repository.py # Step CRUD operations
│   ├── services/
│   │   └── data_service.py    # Singleton data access layer
│   ├── screens/
│   │   ├── home.py            # Home screen with path list
│   │   ├── path_editor.py     # Create/edit path metadata
│   │   ├── step_creator.py    # Add steps with screenshots
│   │   └── path_reader.py     # View completed paths
│   └── widgets/
│       ├── markdown_edit.py    # Markdown text editor + toolbar
│       ├── markdown_label.py   # Markdown → HTML renderer
│       ├── screen_capture.py   # Full screen & region capture
│       └── annotation_editor.py # Screenshot markup tools
└── tests/
    └── test_persistence.py    # Database & repository tests
```

---

## Tech Stack

- **GUI**: PyQt6
- **Database**: SQLite
- **Patterns**: Repository, Singleton, Signal/Slot
- **Screen Capture**: Native macOS `screencapture` command / Qt grabWindow

---

## Future Features (Backlog)

### Annotation Editor
- **Movable/Editable Annotations**: Select and reposition text/callouts after placing

### Path Viewer (PathReaderScreen)
- **Layout Change**: Image should be on top and larger (not thumbnail)
- **Presentation Mode**: Fullscreen slideshow view

### Export & Sharing
- Export path as PDF
- Export as HTML
- Import/export paths as JSON

---

## Git Branch

`claude/flow-path-planning-013ujiXLDZk4vBiLT2nwbYZp`
