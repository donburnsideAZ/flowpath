#!/usr/bin/env python3
"""
Diagnostic script to check why PPTX slide extraction isn't working.
Run this from the terminal: python diagnose_converter.py /path/to/some.pptx
"""

import subprocess
import sys
import os
from pathlib import Path

def run_check(name, cmd):
    """Run a command and report results."""
    print(f"\n{'='*60}")
    print(f"CHECK: {name}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        print(f"Exit code: {result.returncode}")
        if result.stdout.strip():
            print(f"stdout: {result.stdout.strip()[:200]}")
        if result.stderr.strip():
            print(f"stderr: {result.stderr.strip()[:200]}")
        return result.returncode == 0
    except FileNotFoundError:
        print("❌ COMMAND NOT FOUND")
        return False
    except subprocess.TimeoutExpired:
        print("❌ TIMED OUT")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    print("FlowPath PPTX Converter Diagnostics")
    print("=" * 60)
    
    # Check 1: which soffice
    soffice_ok = run_check("Find soffice (LibreOffice)", ["which", "soffice"])
    
    # Check 1b: Try common macOS LibreOffice paths
    if not soffice_ok:
        print("\n...checking common macOS paths...")
        paths_to_check = [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            "/usr/local/bin/soffice",
            os.path.expanduser("~/Applications/LibreOffice.app/Contents/MacOS/soffice")
        ]
        for p in paths_to_check:
            if os.path.exists(p):
                print(f"✅ Found LibreOffice at: {p}")
                print(f"   BUT it's not in your PATH!")
                print(f"   Fix: Add this to your ~/.zshrc or ~/.bash_profile:")
                print(f'   export PATH="/Applications/LibreOffice.app/Contents/MacOS:$PATH"')
                break
        else:
            print("❌ LibreOffice not found in common locations")
    
    # Check 2: which pdftoppm
    pdftoppm_ok = run_check("Find pdftoppm (from poppler)", ["which", "pdftoppm"])
    if not pdftoppm_ok:
        print("   Install with: brew install poppler")
    
    # Check 3: soffice version
    if soffice_ok:
        run_check("LibreOffice version", ["soffice", "--version"])
    
    # Check 4: If a PPTX file was provided, try the actual conversion
    if len(sys.argv) > 1:
        pptx_path = Path(sys.argv[1])
        if pptx_path.exists() and pptx_path.suffix.lower() in ('.pptx', '.ppt'):
            print(f"\n{'='*60}")
            print(f"TESTING ACTUAL CONVERSION: {pptx_path.name}")
            print("=" * 60)
            
            # Create temp output dir
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir = Path(tmpdir)
                
                # Step 1: Convert to PDF
                print(f"\nStep 1: Converting PPTX → PDF...")
                pdf_path = tmpdir / f"{pptx_path.stem}.pdf"
                
                pdf_result = subprocess.run(
                    ['soffice', '--headless', '--convert-to', 'pdf', 
                     '--outdir', str(tmpdir), str(pptx_path)],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                print(f"  Exit code: {pdf_result.returncode}")
                if pdf_result.stderr:
                    print(f"  stderr: {pdf_result.stderr[:300]}")
                
                if pdf_path.exists():
                    print(f"  ✅ PDF created: {pdf_path.stat().st_size} bytes")
                    
                    # Step 2: Convert PDF to images
                    print(f"\nStep 2: Converting PDF → Images with pdftoppm...")
                    
                    ppm_result = subprocess.run(
                        ['pdftoppm', '-jpeg', '-r', '150', 
                         str(pdf_path), str(tmpdir / 'slide')],
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    
                    print(f"  Exit code: {ppm_result.returncode}")
                    if ppm_result.stderr:
                        print(f"  stderr: {ppm_result.stderr[:300]}")
                    
                    # Check for output images
                    images = list(tmpdir.glob('slide-*.jpg'))
                    if images:
                        print(f"  ✅ Created {len(images)} slide images!")
                        for img in sorted(images):
                            print(f"     - {img.name} ({img.stat().st_size} bytes)")
                    else:
                        print("  ❌ No slide images created")
                        print("  Files in temp dir:")
                        for f in tmpdir.iterdir():
                            print(f"     - {f.name}")
                else:
                    print(f"  ❌ PDF was NOT created")
                    print(f"  Files in temp dir:")
                    for f in tmpdir.iterdir():
                        print(f"     - {f.name}")
        else:
            print(f"\n❌ File not found or not a PPTX: {sys.argv[1]}")
    else:
        print("\n" + "=" * 60)
        print("TIP: Run with a PPTX file to test actual conversion:")
        print("  python diagnose_converter.py /path/to/presentation.pptx")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if soffice_ok and pdftoppm_ok:
        print("✅ Both tools found. If conversion still fails, run with a PPTX file.")
    elif not soffice_ok:
        print("❌ LibreOffice (soffice) not in PATH")
        print("   If installed, add to PATH (see above)")
        print("   If not installed: brew install --cask libreoffice")
    if not pdftoppm_ok:
        print("❌ pdftoppm not found")
        print("   Install with: brew install poppler")

if __name__ == "__main__":
    main()
