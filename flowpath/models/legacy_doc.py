"""
LegacyDocument model for FlowPath application.

Represents a legacy document (Word, PDF, PowerPoint, etc.) found in the team folder.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


# Supported legacy file extensions
LEGACY_EXTENSIONS = {
    '.docx': ('word', 'Word Document'),
    '.doc': ('word', 'Word Document'),
    '.pdf': ('pdf', 'PDF Document'),
    '.pptx': ('powerpoint', 'PowerPoint'),
    '.ppt': ('powerpoint', 'PowerPoint'),
    '.xlsx': ('excel', 'Excel Spreadsheet'),
    '.xls': ('excel', 'Excel Spreadsheet'),
    '.txt': ('text', 'Text File'),
    '.html': ('html', 'HTML Document'),
    '.htm': ('html', 'HTML Document'),
    '.pages': ('pages', 'Pages Document'),
    '.numbers': ('numbers', 'Numbers Spreadsheet'),
    '.key': ('keynote', 'Keynote Presentation'),
}


@dataclass
class LegacyDocument:
    """
    Represents a legacy document in the team folder.
    
    Attributes:
        filepath: Full path to the document
        filename: Just the filename
        file_type: Type identifier (word, pdf, powerpoint, etc.)
        type_label: Human-readable type label
        modified_at: Last modification timestamp
        size_bytes: File size in bytes
    """
    filepath: str
    filename: str
    file_type: str
    type_label: str
    modified_at: datetime
    size_bytes: int
    
    @classmethod
    def from_path(cls, filepath: str) -> Optional['LegacyDocument']:
        """
        Create a LegacyDocument from a file path.
        
        Args:
            filepath: Path to the file
            
        Returns:
            LegacyDocument if file is a supported type, None otherwise
        """
        path = Path(filepath)
        ext = path.suffix.lower()
        
        if ext not in LEGACY_EXTENSIONS:
            return None
            
        file_type, type_label = LEGACY_EXTENSIONS[ext]
        
        try:
            stat = path.stat()
            modified_at = datetime.fromtimestamp(stat.st_mtime)
            size_bytes = stat.st_size
        except OSError:
            modified_at = datetime.now()
            size_bytes = 0
            
        return cls(
            filepath=str(path),
            filename=path.name,
            file_type=file_type,
            type_label=type_label,
            modified_at=modified_at,
            size_bytes=size_bytes,
        )
    
    @property
    def size_display(self) -> str:
        """Return human-readable file size."""
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024 * 1024:
            return f"{self.size_bytes / 1024:.1f} KB"
        else:
            return f"{self.size_bytes / (1024 * 1024):.1f} MB"
    
    @property
    def modified_display(self) -> str:
        """Return human-readable modified date."""
        return self.modified_at.strftime("%b %d, %Y")
    
    def __repr__(self) -> str:
        return f"LegacyDocument(filename='{self.filename}', type='{self.file_type}')"
