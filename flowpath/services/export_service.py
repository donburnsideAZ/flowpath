"""
Export service for FlowPath application.

Provides export functionality for paths in JSON, HTML, and PDF formats.
"""

import base64
import json
import os
import re
from datetime import datetime
from pathlib import Path as FilePath
from typing import List, Optional, Tuple

from ..models import Path, Step


def _markdown_to_html(text: str) -> str:
    """Convert Markdown text to HTML."""
    if not text:
        return ""

    html = text

    # Escape HTML special characters first
    html = html.replace("&", "&amp;")
    html = html.replace("<", "&lt;")
    html = html.replace(">", "&gt;")

    # Links: [text](url) -> <a href="url">text</a>
    html = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        r'<a href="\2">\1</a>',
        html
    )

    # Bold: **text** or __text__ -> <strong>text</strong>
    html = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', html)

    # Italic: *text* or _text_ -> <em>text</em>
    html = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', html)
    html = re.sub(r'(?<![a-zA-Z])_([^_]+)_(?![a-zA-Z])', r'<em>\1</em>', html)

    # Line breaks: \n -> <br>
    html = html.replace("\n", "<br>")

    return html


def _image_to_base64(image_path: str) -> Optional[str]:
    """Convert an image file to base64 data URI."""
    if not image_path or not os.path.exists(image_path):
        return None

    try:
        with open(image_path, 'rb') as f:
            data = f.read()

        # Determine MIME type from extension
        ext = FilePath(image_path).suffix.lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
        }
        mime_type = mime_types.get(ext, 'image/png')

        encoded = base64.b64encode(data).decode('utf-8')
        return f"data:{mime_type};base64,{encoded}"
    except Exception:
        return None


class ExportService:
    """Service for exporting paths to various formats."""

    @staticmethod
    def export_json(
        path: Path,
        steps: List[Step],
        output_path: str,
        embed_images: bool = False
    ) -> bool:
        """
        Export a path to JSON format.

        Args:
            path: The Path object to export
            steps: List of Step objects for the path
            output_path: File path to save the JSON
            embed_images: If True, embed images as base64 in the JSON

        Returns:
            True if export was successful
        """
        try:
            export_data = {
                'version': '1.0',
                'exported_at': datetime.now().isoformat(),
                'path': path.to_dict(),
                'steps': []
            }

            for step in steps:
                step_data = step.to_dict()
                if embed_images and step.screenshot_path:
                    base64_image = _image_to_base64(step.screenshot_path)
                    if base64_image:
                        step_data['screenshot_base64'] = base64_image
                export_data['steps'].append(step_data)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"JSON export error: {e}")
            return False

    @staticmethod
    def export_html(
        path: Path,
        steps: List[Step],
        output_path: str
    ) -> bool:
        """
        Export a path to a self-contained HTML file.

        Images are embedded as base64 data URIs for portability.

        Args:
            path: The Path object to export
            steps: List of Step objects for the path
            output_path: File path to save the HTML

        Returns:
            True if export was successful
        """
        try:
            html = ExportService._generate_html(path, steps)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)

            return True
        except Exception as e:
            print(f"HTML export error: {e}")
            return False

    @staticmethod
    def _generate_html(path: Path, steps: List[Step]) -> str:
        """Generate HTML content for a path."""
        # Format metadata
        created_date = path.created_at.strftime('%B %d, %Y') if path.created_at else 'Unknown'
        updated_date = path.updated_at.strftime('%B %d, %Y') if path.updated_at else 'Unknown'
        description_html = _markdown_to_html(path.description) if path.description else ''

        # Build tags HTML
        tags_html = ''
        if path.tags:
            tags = [tag.strip() for tag in path.tags.split(',') if tag.strip()]
            tags_html = ' '.join(f'<span class="tag">{tag}</span>' for tag in tags)

        # Build steps HTML
        steps_html = ''
        for step in steps:
            instructions_html = _markdown_to_html(step.instructions) if step.instructions else ''

            # Handle screenshot
            image_html = ''
            if step.screenshot_path and os.path.exists(step.screenshot_path):
                base64_img = _image_to_base64(step.screenshot_path)
                if base64_img:
                    image_html = f'<img src="{base64_img}" alt="Step {step.step_number} screenshot" class="screenshot">'

            steps_html += f'''
            <div class="step">
                <h2>Step {step.step_number}</h2>
                {f'<div class="screenshot-container">{image_html}</div>' if image_html else ''}
                <div class="instructions">{instructions_html}</div>
            </div>
            '''

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{path.title}</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 40px;
        }}
        header {{
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 24px;
            margin-bottom: 32px;
        }}
        h1 {{
            font-size: 28px;
            color: #222;
            margin-bottom: 12px;
        }}
        .meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            font-size: 14px;
            color: #666;
            margin-bottom: 12px;
        }}
        .meta-item {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .meta-label {{
            font-weight: 600;
            color: #444;
        }}
        .category {{
            background: #4CAF50;
            color: white;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 12px;
        }}
        .tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 8px;
        }}
        .tag {{
            background: #e3f2fd;
            color: #1976D2;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 12px;
        }}
        .description {{
            color: #555;
            font-size: 15px;
            margin-top: 16px;
        }}
        .step {{
            margin-bottom: 40px;
            padding-bottom: 40px;
            border-bottom: 1px solid #eee;
        }}
        .step:last-child {{
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }}
        .step h2 {{
            font-size: 20px;
            color: #333;
            margin-bottom: 16px;
        }}
        .screenshot-container {{
            margin-bottom: 16px;
        }}
        .screenshot {{
            max-width: 100%;
            height: auto;
            border-radius: 6px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .instructions {{
            font-size: 15px;
            color: #444;
        }}
        .instructions a {{
            color: #1976D2;
            text-decoration: none;
        }}
        .instructions a:hover {{
            text-decoration: underline;
        }}
        footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            font-size: 12px;
            color: #999;
            text-align: center;
        }}
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
                padding: 20px;
            }}
            .step {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{path.title}</h1>
            <div class="meta">
                {f'<div class="meta-item"><span class="category">{path.category}</span></div>' if path.category else ''}
                <div class="meta-item"><span class="meta-label">Created:</span> {created_date}</div>
                <div class="meta-item"><span class="meta-label">Updated:</span> {updated_date}</div>
                {f'<div class="meta-item"><span class="meta-label">By:</span> {path.creator}</div>' if path.creator else ''}
            </div>
            {f'<div class="tags">{tags_html}</div>' if tags_html else ''}
            {f'<div class="description">{description_html}</div>' if description_html else ''}
        </header>

        <main>
            {steps_html if steps_html else '<p style="color: #666; text-align: center;">This path has no steps yet.</p>'}
        </main>

        <footer>
            Exported from FlowPath on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        </footer>
    </div>
</body>
</html>'''

        return html

    @staticmethod
    def export_pdf(
        path: Path,
        steps: List[Step],
        output_path: str
    ) -> bool:
        """
        Export a path to PDF format.

        Uses Qt's print functionality to render HTML to PDF.

        Args:
            path: The Path object to export
            steps: List of Step objects for the path
            output_path: File path to save the PDF

        Returns:
            True if export was successful
        """
        try:
            from PyQt6.QtCore import QMarginsF, QSizeF
            from PyQt6.QtGui import QPageLayout, QPageSize
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtPrintSupport import QPrinter
            from PyQt6.QtWebEngineWidgets import QWebEngineView

            # Generate HTML content
            html = ExportService._generate_html(path, steps)

            # Set up printer
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(output_path)

            # Set page layout
            page_layout = QPageLayout(
                QPageSize(QPageSize.StandardPageSize.Letter),
                QPageLayout.Orientation.Portrait,
                QMarginsF(20, 20, 20, 20)
            )
            printer.setPageLayout(page_layout)

            # Create a web view to render the HTML
            # Note: This requires QWebEngineView which may need to be installed
            view = QWebEngineView()
            view.setHtml(html)

            # Wait for the page to load and then print
            def handle_print_finished(success):
                pass  # PDF writing is handled by QPrinter

            def handle_load_finished(ok):
                if ok:
                    view.page().printToPdf(output_path)

            view.loadFinished.connect(handle_load_finished)

            return True

        except ImportError:
            # Fall back to simple PDF generation without WebEngine
            return ExportService._export_pdf_simple(path, steps, output_path)
        except Exception as e:
            print(f"PDF export error: {e}")
            return False

    @staticmethod
    def _export_pdf_simple(
        path: Path,
        steps: List[Step],
        output_path: str
    ) -> bool:
        """
        Simple PDF export using QTextDocument.

        This is a fallback when QWebEngineView is not available.
        """
        try:
            from PyQt6.QtCore import QMarginsF
            from PyQt6.QtGui import (
                QPageLayout, QPageSize, QTextDocument, QFont
            )
            from PyQt6.QtPrintSupport import QPrinter
            from PyQt6.QtWidgets import QApplication

            # Generate simplified HTML (without complex CSS)
            html = ExportService._generate_simple_html(path, steps)

            # Set up printer
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(output_path)

            # Set page layout
            page_layout = QPageLayout(
                QPageSize(QPageSize.StandardPageSize.Letter),
                QPageLayout.Orientation.Portrait,
                QMarginsF(40, 40, 40, 40)
            )
            printer.setPageLayout(page_layout)

            # Create document and print
            doc = QTextDocument()
            doc.setDefaultFont(QFont('Arial', 11))
            doc.setHtml(html)
            doc.print(printer)

            return True
        except Exception as e:
            print(f"Simple PDF export error: {e}")
            return False

    @staticmethod
    def _generate_simple_html(path: Path, steps: List[Step]) -> str:
        """Generate simplified HTML for QTextDocument rendering."""
        # Format metadata
        created_date = path.created_at.strftime('%B %d, %Y') if path.created_at else 'Unknown'

        # Build steps HTML
        steps_html = ''
        for step in steps:
            instructions_html = _markdown_to_html(step.instructions) if step.instructions else ''

            # Handle screenshot - embed as base64
            image_html = ''
            if step.screenshot_path and os.path.exists(step.screenshot_path):
                base64_img = _image_to_base64(step.screenshot_path)
                if base64_img:
                    image_html = f'<img src="{base64_img}" width="500"><br>'

            steps_html += f'''
            <h2>Step {step.step_number}</h2>
            {image_html}
            <p>{instructions_html}</p>
            <hr>
            '''

        html = f'''
        <h1>{path.title}</h1>
        <p><b>Category:</b> {path.category or 'None'} | <b>Created:</b> {created_date}</p>
        {f'<p>{_markdown_to_html(path.description)}</p>' if path.description else ''}
        <hr>
        {steps_html if steps_html else '<p>This path has no steps yet.</p>'}
        <p style="color: gray; font-size: 10px;">Exported from FlowPath</p>
        '''

        return html

    @staticmethod
    def get_suggested_filename(path: Path, extension: str) -> str:
        """
        Generate a suggested filename for export.

        Args:
            path: The Path object being exported
            extension: File extension (without dot)

        Returns:
            Suggested filename
        """
        # Clean the title for use in a filename
        safe_title = re.sub(r'[^\w\s-]', '', path.title)
        safe_title = re.sub(r'[-\s]+', '-', safe_title).strip('-')

        if not safe_title:
            safe_title = 'flowpath-export'

        return f"{safe_title}.{extension}"
