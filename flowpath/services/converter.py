"""
Legacy Document Converter for FlowPath.

Converts legacy documents (docx, pptx, txt) to FlowPath markdown format.
"""

import os
import re
import subprocess
import shutil
import zipfile
import platform
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class ConversionResult:
    """Result of a document conversion."""
    success: bool
    markdown_path: Optional[str] = None
    images_dir: Optional[str] = None
    error: Optional[str] = None
    title: str = ""
    step_count: int = 0


def _find_executable(name: str, extra_paths: List[str] = None) -> Optional[str]:
    """
    Find an executable by checking common locations.
    
    GUI apps on macOS don't inherit the shell's PATH, so we need to
    check common installation locations explicitly.
    """
    # First try shutil.which (uses current PATH)
    found = shutil.which(name)
    if found:
        return found
    
    # Common locations to check
    search_paths = [
        f"/opt/homebrew/bin/{name}",  # Apple Silicon Homebrew
        f"/usr/local/bin/{name}",      # Intel Homebrew / manual installs
        f"/usr/bin/{name}",            # System
    ]
    
    # Add extra paths (like LibreOffice app bundle)
    if extra_paths:
        search_paths = extra_paths + search_paths
    
    for path in search_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    
    return None


def _find_soffice() -> Optional[str]:
    """Find LibreOffice soffice executable."""
    return _find_executable('soffice', [
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        os.path.expanduser("~/Applications/LibreOffice.app/Contents/MacOS/soffice"),
    ])


def _find_pdftoppm() -> Optional[str]:
    """Find pdftoppm executable (from poppler)."""
    return _find_executable('pdftoppm')


def _find_pandoc() -> Optional[str]:
    """Find pandoc executable."""
    return _find_executable('pandoc')


class LegacyConverter:
    """
    Converts legacy documents to FlowPath markdown format.
    
    Supported formats:
    - .docx -> Markdown with extracted images
    - .pptx -> Markdown with slides as steps, extracted images
    - .txt  -> Markdown with frontmatter wrapper
    """
    
    def __init__(self, output_dir: str):
        """
        Initialize the converter.
        
        Args:
            output_dir: Directory where converted files will be saved
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._is_macos = platform.system() == 'Darwin'
        
        # Find tools (GUI apps don't inherit shell PATH)
        self._soffice = _find_soffice()
        self._pdftoppm = _find_pdftoppm()
        self._pandoc = _find_pandoc()
        
        if self._soffice:
            print(f"Found LibreOffice: {self._soffice}")
        if self._pdftoppm:
            print(f"Found pdftoppm: {self._pdftoppm}")
        if self._pandoc:
            print(f"Found pandoc: {self._pandoc}")
    
    def convert(self, filepath: str) -> ConversionResult:
        """
        Convert a legacy document to FlowPath markdown.
        
        Args:
            filepath: Path to the document to convert
            
        Returns:
            ConversionResult with status and output paths
        """
        path = Path(filepath)
        
        if not path.exists():
            return ConversionResult(success=False, error=f"File not found: {filepath}")
        
        ext = path.suffix.lower()
        
        if ext in ('.docx', '.doc'):
            return self._convert_docx(path)
        elif ext in ('.pptx', '.ppt'):
            return self._convert_pptx(path)
        elif ext == '.txt':
            return self._convert_txt(path)
        else:
            return ConversionResult(success=False, error=f"Unsupported format: {ext}")
    
    def _convert_docx(self, path: Path) -> ConversionResult:
        """Convert a Word document to FlowPath markdown."""
        try:
            # Create output directory for this document
            slug = self._slugify(path.stem)
            doc_dir = self.output_dir / slug
            doc_dir.mkdir(exist_ok=True)
            images_dir = doc_dir / "images"
            images_dir.mkdir(exist_ok=True)
            
            # Extract images from docx
            self._extract_docx_images(path, images_dir)
            
            # Convert to markdown using pandoc
            md_content = self._docx_to_markdown(path)
            
            if md_content is None:
                return ConversionResult(
                    success=False, 
                    error="Failed to convert document. Is pandoc installed?"
                )
            
            # Parse the markdown to extract title and structure
            title, steps = self._parse_docx_markdown(md_content, path.stem)
            
            # Build FlowPath markdown with frontmatter
            frontmatter = self._build_frontmatter(
                title=title,
                category="Imported",
                tags=["imported", "docx"],
                description=f"Imported from {path.name}"
            )
            
            # Update image references to use local paths
            md_content = self._fix_image_paths(md_content, slug)
            
            # Combine frontmatter and content
            final_content = frontmatter + "\n" + md_content
            
            # Write the markdown file
            md_path = doc_dir / f"{slug}.md"
            md_path.write_text(final_content, encoding='utf-8')
            
            return ConversionResult(
                success=True,
                markdown_path=str(md_path),
                images_dir=str(images_dir),
                title=title,
                step_count=len(steps)
            )
            
        except Exception as e:
            return ConversionResult(success=False, error=str(e))
    
    def _convert_pptx(self, path: Path) -> ConversionResult:
        """Convert a PowerPoint to FlowPath markdown with slides as steps."""
        try:
            # Create output directory for this document
            slug = self._slugify(path.stem)
            doc_dir = self.output_dir / slug
            doc_dir.mkdir(exist_ok=True)
            images_dir = doc_dir / "images"
            images_dir.mkdir(exist_ok=True)
            
            # Extract text content first to know how many slides we have
            slides_text = self._extract_pptx_text(path)
            num_slides = len(slides_text)
            
            # Extract slide images (try multiple methods)
            slide_images = self._extract_pptx_slides(path, images_dir, num_slides)
            
            # Get title from first slide or filename
            title = slides_text[0].get('title', path.stem) if slides_text else path.stem
            
            # Build FlowPath markdown with frontmatter
            frontmatter = self._build_frontmatter(
                title=title,
                category="Imported",
                tags=["imported", "pptx", "presentation"],
                description=f"Imported from {path.name}"
            )
            
            # Build steps from slides
            steps_md = []
            for i, slide in enumerate(slides_text):
                step_num = i + 1
                slide_title = slide.get('title', f'Slide {step_num}')
                slide_content = slide.get('content', '')
                
                # Check if we have an image for this slide
                image_ref = ""
                if i < len(slide_images) and slide_images[i]:
                    img_name = slide_images[i]
                    image_ref = f"![Slide {step_num}]({slug}/images/{img_name})\n\n"
                
                step_md = f"## Step {step_num}: {slide_title}\n\n{image_ref}{slide_content}\n"
                steps_md.append(step_md)
            
            # Combine everything
            final_content = frontmatter + "\n" + "\n".join(steps_md)
            
            # Write the markdown file
            md_path = doc_dir / f"{slug}.md"
            md_path.write_text(final_content, encoding='utf-8')
            
            return ConversionResult(
                success=True,
                markdown_path=str(md_path),
                images_dir=str(images_dir),
                title=title,
                step_count=len(slides_text)
            )
            
        except Exception as e:
            return ConversionResult(success=False, error=str(e))
    
    def _convert_txt(self, path: Path) -> ConversionResult:
        """Convert a text file to FlowPath markdown."""
        try:
            # Read the text content
            content = path.read_text(encoding='utf-8', errors='replace')
            
            # Create output directory
            slug = self._slugify(path.stem)
            doc_dir = self.output_dir / slug
            doc_dir.mkdir(exist_ok=True)
            
            # Try to extract title from first line
            lines = content.strip().split('\n')
            title = lines[0].strip() if lines else path.stem
            
            # Clean up title (remove markdown headers if present)
            title = re.sub(r'^#+\s*', '', title)
            
            # If title is too long, truncate
            if len(title) > 60:
                title = title[:57] + "..."
            
            # Build frontmatter
            frontmatter = self._build_frontmatter(
                title=title,
                category="Imported",
                tags=["imported", "text"],
                description=f"Imported from {path.name}"
            )
            
            # Wrap content as a single step
            step_content = f"## Step 1: {title}\n\n{content}\n"
            
            # Combine
            final_content = frontmatter + "\n" + step_content
            
            # Write
            md_path = doc_dir / f"{slug}.md"
            md_path.write_text(final_content, encoding='utf-8')
            
            return ConversionResult(
                success=True,
                markdown_path=str(md_path),
                title=title,
                step_count=1
            )
            
        except Exception as e:
            return ConversionResult(success=False, error=str(e))
    
    def _docx_to_markdown(self, path: Path) -> Optional[str]:
        """Convert docx to markdown using pandoc."""
        if not self._pandoc:
            print("Pandoc not found. Please install pandoc.")
            return None
        
        try:
            result = subprocess.run(
                [self._pandoc, str(path), '-t', 'markdown', '--wrap=none'],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"Pandoc error: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            print("Pandoc timed out")
            return None
    
    def _extract_docx_images(self, path: Path, output_dir: Path) -> List[str]:
        """Extract images from a docx file."""
        images = []
        try:
            with zipfile.ZipFile(path, 'r') as zf:
                for name in zf.namelist():
                    if name.startswith('word/media/'):
                        # Extract just the filename
                        img_name = os.path.basename(name)
                        if img_name:
                            # Extract to output directory
                            img_data = zf.read(name)
                            img_path = output_dir / img_name
                            img_path.write_bytes(img_data)
                            images.append(img_name)
        except Exception as e:
            print(f"Error extracting images: {e}")
        return images
    
    def _extract_pptx_slides(self, path: Path, output_dir: Path, num_slides: int) -> List[str]:
        """
        Extract slide images from a pptx file.
        Tries multiple methods in order of preference:
        1. LibreOffice + pdftoppm (best quality)
        2. LibreOffice + sips (macOS)
        3. pdf2image Python library
        4. Embedded media extraction (fallback)
        """
        images = []
        
        # Method 1: Try LibreOffice + pdftoppm
        images = self._try_libreoffice_conversion(path, output_dir)
        if images:
            print(f"Extracted {len(images)} slide images using LibreOffice")
            return images
        
        # Method 2: On macOS, try using sips to convert PDF pages
        if self._is_macos:
            images = self._try_macos_pdf_conversion(path, output_dir)
            if images:
                print(f"Extracted {len(images)} slide images using macOS tools")
                return images
        
        # Method 3: Try pdf2image Python library
        images = self._try_pdf2image_conversion(path, output_dir)
        if images:
            print(f"Extracted {len(images)} slide images using pdf2image")
            return images
        
        # Note: We no longer use embedded media as a fallback for slide images.
        # Embedded media (ppt/media/*) contains images USED IN slides (logos, photos, icons),
        # not screenshots OF the slides. Using them is misleading.
        
        # No images extracted - return empty strings for each slide
        print("Warning: Could not extract slide images.")
        print("  For slide screenshots, install LibreOffice: brew install --cask libreoffice")
        print("  And pdftoppm (poppler): brew install poppler")
        return [''] * num_slides
    
    def _try_libreoffice_conversion(self, path: Path, output_dir: Path) -> List[str]:
        """Try to convert PPTX to images using LibreOffice + pdftoppm."""
        try:
            # Check if we found soffice during init
            if not self._soffice:
                print("LibreOffice (soffice) not found")
                return []
            
            if not self._pdftoppm:
                print("pdftoppm not found")
                return []
            
            # Convert to PDF first
            print(f"Converting to PDF using: {self._soffice}")
            pdf_result = subprocess.run(
                [self._soffice, '--headless', '--convert-to', 'pdf', 
                 '--outdir', str(output_dir), str(path)],
                capture_output=True,
                timeout=120
            )
            
            if pdf_result.returncode != 0:
                print(f"LibreOffice PDF conversion failed: {pdf_result.stderr}")
                return []
            
            pdf_path = output_dir / f"{path.stem}.pdf"
            if not pdf_path.exists():
                print(f"PDF not created at expected path: {pdf_path}")
                return []
            
            print(f"PDF created, converting to images using: {self._pdftoppm}")
            
            # Convert PDF to images with pdftoppm
            pdftoppm_result = subprocess.run(
                [self._pdftoppm, '-jpeg', '-r', '150', 
                 str(pdf_path), str(output_dir / 'slide')],
                capture_output=True,
                timeout=120
            )
            
            if pdftoppm_result.returncode == 0:
                # Clean up PDF
                pdf_path.unlink()
                
                # Find generated slide images (pdftoppm names them slide-1.jpg, slide-2.jpg, etc.)
                slide_images = sorted(output_dir.glob('slide-*.jpg'))
                
                # Rename to consistent format: slide-01.jpg, slide-02.jpg
                renamed_images = []
                for img in slide_images:
                    # Extract number from filename
                    match = re.search(r'slide-(\d+)\.jpg', img.name)
                    if match:
                        num = int(match.group(1))
                        new_name = f"slide-{num:02d}.jpg"
                        new_path = output_dir / new_name
                        img.rename(new_path)
                        renamed_images.append(new_name)
                
                return sorted(renamed_images)
            else:
                print(f"pdftoppm failed: {pdftoppm_result.stderr}")
            
            # pdftoppm failed, clean up PDF
            if pdf_path.exists():
                pdf_path.unlink()
                
        except subprocess.TimeoutExpired:
            print("LibreOffice conversion timed out")
        except Exception as e:
            print(f"LibreOffice conversion error: {e}")
        
        return []
    
    def _try_macos_pdf_conversion(self, path: Path, output_dir: Path) -> List[str]:
        """Try to convert PPTX to images using macOS native tools."""
        try:
            # First need a PDF - try LibreOffice or other tools
            pdf_path = output_dir / f"{path.stem}.pdf"
            
            # Try to create PDF if it doesn't exist
            if not pdf_path.exists() and self._soffice:
                try:
                    subprocess.run(
                        [self._soffice, '--headless', '--convert-to', 'pdf', 
                         '--outdir', str(output_dir), str(path)],
                        capture_output=True,
                        timeout=120
                    )
                except:
                    pass
            
            if not pdf_path.exists():
                return []
            
            # Use sips to convert PDF to images (macOS native)
            # First, need to use Quartz to render PDF pages
            # Unfortunately sips can't directly split PDF pages
            
            # Try using Preview via AppleScript to export pages
            # This is complex, so let's try qlmanage for a thumbnail at least
            try:
                # qlmanage can generate thumbnails
                ql_result = subprocess.run(
                    ['qlmanage', '-t', '-s', '1024', '-o', str(output_dir), str(path)],
                    capture_output=True,
                    timeout=30
                )
                
                # qlmanage creates files like "filename.pptx.png"
                thumb_path = output_dir / f"{path.name}.png"
                if thumb_path.exists():
                    # Rename to slide-01.png
                    new_path = output_dir / "slide-01.png"
                    thumb_path.rename(new_path)
                    pdf_path.unlink() if pdf_path.exists() else None
                    # This only gives us one thumbnail, not per-slide
                    # Return it for the first slide at least
                    return ["slide-01.png"]
                    
            except Exception as e:
                print(f"qlmanage error: {e}")
            
            # Clean up
            if pdf_path.exists():
                pdf_path.unlink()
                
        except Exception as e:
            print(f"macOS conversion error: {e}")
        
        return []
    
    def _try_pdf2image_conversion(self, path: Path, output_dir: Path) -> List[str]:
        """Try to convert PPTX to images using pdf2image Python library."""
        try:
            from pdf2image import convert_from_path
            
            # First need a PDF
            pdf_path = output_dir / f"{path.stem}.pdf"
            
            # Try to create PDF if it doesn't exist
            if not pdf_path.exists() and self._soffice:
                try:
                    subprocess.run(
                        [self._soffice, '--headless', '--convert-to', 'pdf', 
                         '--outdir', str(output_dir), str(path)],
                        capture_output=True,
                        timeout=120
                    )
                except:
                    return []
            
            if not pdf_path.exists():
                return []
            
            # Convert PDF pages to images
            images = convert_from_path(str(pdf_path), dpi=150)
            
            image_names = []
            for i, image in enumerate(images):
                img_name = f"slide-{i+1:02d}.jpg"
                img_path = output_dir / img_name
                image.save(str(img_path), 'JPEG', quality=85)
                image_names.append(img_name)
            
            # Clean up PDF
            pdf_path.unlink()
            
            return image_names
            
        except ImportError:
            # pdf2image not installed
            pass
        except Exception as e:
            print(f"pdf2image conversion error: {e}")
        
        return []
    
    def _extract_pptx_embedded_media(self, path: Path, output_dir: Path) -> List[str]:
        """Extract embedded media from a pptx file as fallback."""
        images = []
        try:
            with zipfile.ZipFile(path, 'r') as zf:
                media_files = sorted([
                    n for n in zf.namelist() 
                    if n.startswith('ppt/media/') and 
                    any(n.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif'])
                ])
                
                for i, name in enumerate(media_files):
                    img_data = zf.read(name)
                    # Use consistent naming
                    ext = os.path.splitext(name)[1]
                    img_name = f"slide-{i+1:02d}{ext}"
                    img_path = output_dir / img_name
                    img_path.write_bytes(img_data)
                    images.append(img_name)
                    
        except Exception as e:
            print(f"Error extracting pptx media: {e}")
        
        return images
    
    def _extract_pptx_text(self, path: Path) -> List[dict]:
        """Extract text content from each slide."""
        slides = []
        
        try:
            with zipfile.ZipFile(path, 'r') as zf:
                # Find all slide XML files
                slide_files = sorted([
                    n for n in zf.namelist() 
                    if re.match(r'ppt/slides/slide\d+\.xml', n)
                ], key=lambda x: int(re.search(r'slide(\d+)', x).group(1)))
                
                for slide_file in slide_files:
                    xml_content = zf.read(slide_file).decode('utf-8')
                    
                    # Extract text using regex (simple but effective)
                    # Look for <a:t> tags which contain text
                    texts = re.findall(r'<a:t>([^<]+)</a:t>', xml_content)
                    
                    if texts:
                        # First text is often the title
                        title = texts[0] if texts else ""
                        content = '\n'.join(texts[1:]) if len(texts) > 1 else ""
                        slides.append({'title': title, 'content': content})
                    else:
                        slides.append({'title': '', 'content': ''})
                        
        except Exception as e:
            print(f"Error extracting pptx text: {e}")
        
        return slides
    
    def _parse_docx_markdown(self, md_content: str, fallback_title: str) -> Tuple[str, List[str]]:
        """Parse markdown content to extract title and steps."""
        lines = md_content.strip().split('\n')
        title = fallback_title
        
        # Try to find title from first heading
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break
            elif line.startswith('## '):
                title = line[3:].strip()
                break
        
        # Find all headings as potential steps
        steps = []
        for line in lines:
            if line.startswith('#'):
                steps.append(line)
        
        return title, steps
    
    def _fix_image_paths(self, md_content: str, slug: str) -> str:
        """Fix image paths in markdown to use local references."""
        # Replace word/media/ references with local path
        md_content = re.sub(
            r'!\[([^\]]*)\]\(word/media/([^)]+)\)',
            rf'![\1]({slug}/images/\2)',
            md_content
        )
        return md_content
    
    def _build_frontmatter(self, title: str, category: str, 
                           tags: List[str], description: str) -> str:
        """Build YAML frontmatter for FlowPath markdown."""
        tags_str = ', '.join(f'"{t}"' for t in tags)
        created = datetime.now().strftime("%Y-%m-%d")
        
        return f'''---
title: "{title}"
category: "{category}"
tags: [{tags_str}]
creator: "converter"
created: "{created}"
description: "{description}"
---
'''
    
    def _slugify(self, text: str) -> str:
        """Convert text to a URL-safe slug."""
        # Convert to lowercase
        slug = text.lower()
        # Replace spaces and underscores with hyphens
        slug = re.sub(r'[\s_]+', '-', slug)
        # Remove non-alphanumeric characters (except hyphens)
        slug = re.sub(r'[^a-z0-9-]', '', slug)
        # Remove multiple consecutive hyphens
        slug = re.sub(r'-+', '-', slug)
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        return slug or 'untitled'
