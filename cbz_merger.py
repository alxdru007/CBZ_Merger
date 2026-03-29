#!/usr/bin/env python3
"""
CBZ Merger - Merges multiple .cbz files into a single combined .cbz archive.

Usage:
    python cbz_merger.py [input_folder] [output_file]

    input_folder : Path to the folder containing .cbz files (default: current directory)
    output_file  : Name of the merged output file (default: merged_manga.cbz)

Can also be imported as a module:
    from cbz_merger import merge_cbz_files
    merge_cbz_files("./my_manga/", "combined.cbz")
"""

import os
import sys
import zipfile
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional


# ─── Configuration ───────────────────────────────────────────────────────────
SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".tif", ".avif"
}
SUPPORTED_EXTRAS = {".xml", ".json", ".txt"}  # metadata files to skip


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _is_image(filename: str) -> bool:
    """Check if a filename has a supported image extension."""
    return Path(filename).suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS


def _natural_sort_key(path: Path):
    """
    Sort key that handles mixed alpha-numeric filenames correctly.
    e.g. 'chapter2.cbz' comes before 'chapter10.cbz'.
    """
    import re
    parts = re.split(r'(\d+)', path.stem)
    return [int(p) if p.isdigit() else p.lower() for p in parts]


def _format_size(size_bytes: int) -> str:
    """Format byte count to human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def _progress_bar(current: int, total: int, width: int = 40) -> str:
    """Generate a simple text-based progress bar."""
    ratio = current / total if total > 0 else 0
    filled = int(width * ratio)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {current}/{total} ({ratio:.0%})"


# ─── Core Logic ──────────────────────────────────────────────────────────────

def discover_cbz_files(input_folder: str | Path) -> list[Path]:
    """
    Discover and sort all .cbz files in the given folder.
    Returns a naturally sorted list of Path objects.
    """
    folder = Path(input_folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"❌ Input folder not found: {folder}")

    cbz_files = sorted(folder.glob("*.cbz"), key=_natural_sort_key)

    if not cbz_files:
        raise FileNotFoundError(f"❌ No .cbz files found in: {folder}")

    return cbz_files


def extract_cbz(cbz_path: Path, target_dir: Path, chapter_index: int, optimize_for_ereader: bool = False) -> list[Path]:
    """
    Extract image files from a single .cbz archive into the target directory.
    Renames files with a global prefix to maintain order across chapters.
     Optionally optimizations for e-readers (grayscale, resize, jpeg).

    Returns a list of extracted file paths.
    """
    extracted = []

    try:
        with zipfile.ZipFile(cbz_path, "r") as zf:
            # Filter and sort image entries
            image_entries = [
                name for name in zf.namelist()
                if _is_image(name) and not name.startswith("__MACOSX")
            ]
            image_entries.sort(key=lambda n: _natural_sort_key(Path(n)))

            if not image_entries:
                print(f"  ⚠️  No images found in {cbz_path.name} — skipping.")
                return extracted

            for img_index, entry_name in enumerate(image_entries):
                ext = Path(entry_name).suffix.lower()
                # Create unique, ordered filename:
                # Format: CCCC_IIII_originalname.ext
                # CCCC = chapter index, IIII = image index within chapter
                chapter_tag = cbz_path.stem.replace(" ", "_")
                new_name = f"{chapter_index:04d}_{img_index:04d}_{chapter_tag}{ext}"
                out_path = target_dir / new_name

                # Extract the file data and write with new name
                data = zf.read(entry_name)

                if optimize_for_ereader:
                    try:
                        from io import BytesIO
                        from PIL import Image

                        with Image.open(BytesIO(data)) as img:
                            # Handle transparency by drawing over white
                            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                                bg = Image.new("RGB", img.size, (255, 255, 255))
                                bg.paste(img, (0, 0), img if img.mode in ('RGBA', 'LA') else img.convert('RGBA'))
                                img = bg

                            # Convert to Grayscale
                            if img.mode != "L":
                                img = img.convert("L")

                            # Resize for typical E-Reader width (1600px)
                            max_width = 1600
                            if img.width > max_width:
                                ratio = max_width / float(img.width)
                                new_height = int(img.height * ratio)
                                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

                            # Save as optimized JPEG
                            out_path = out_path.with_suffix(".jpg")
                            img.save(out_path, "JPEG", optimize=True, quality=80)
                            extracted.append(out_path)
                            continue  # Optimized, skip writing raw data

                    except Exception as e:
                        print(f"  ⚠️  Skipping optimization for {entry_name}: {e}")

                out_path.write_bytes(data)
                extracted.append(out_path)

    except zipfile.BadZipFile:
        print(f"  ❌ CORRUPTED: {cbz_path.name} — skipping this file!")
    except Exception as e:
        print(f"  ❌ ERROR processing {cbz_path.name}: {e}")

    return extracted


def merge_cbz_files(
    input_folder: str | Path = ".",
    output_file: str | Path = "merged_manga.cbz",
    compression: int = zipfile.ZIP_STORED,
    optimize_for_ereader: bool = False
) -> Optional[Path]:
    """
    Merge all .cbz files from input_folder into a single output .cbz file.

    Args:
        input_folder:  Directory containing source .cbz files.
        output_file:   Path/name for the merged output file.
        compression:   ZIP compression method (ZIP_STORED for speed, ZIP_DEFLATED for size).
        optimize_for_ereader: Reduces size by converting to grayscale, sizing down, and converting to JPG.

    Returns:
        Path to the created merged file, or None on failure.
    """
    start_time = time.time()

    print("=" * 60)
    print("  📚 CBZ MERGER")
    print("=" * 60)
    print()

    # ── Step 1: Discover files ───────────────────────────────────────────
    input_folder = Path(input_folder).resolve()
    output_path = Path(output_file) if Path(output_file).is_absolute() else input_folder / output_file

    print(f"📂 Input folder : {input_folder}")
    print(f"📦 Output file  : {output_path}")
    print()

    try:
        cbz_files = discover_cbz_files(input_folder)
    except FileNotFoundError as e:
        print(str(e))
        return None

    print(f"🔍 Found {len(cbz_files)} .cbz file(s):")
    for i, f in enumerate(cbz_files, 1):
        size = _format_size(f.stat().st_size)
        print(f"   {i:3d}. {f.name}  ({size})")
    print()

    # ── Step 2: Extract into temp directory ──────────────────────────────
    temp_dir = None
    all_images: list[Path] = []

    try:
        temp_dir = Path(tempfile.mkdtemp(prefix="cbz_merger_"))
        print(f"📁 Temp directory: {temp_dir}")
        print()
        print("⏳ Extracting chapters...")

        def extract_task(idx, cbz_file):
            return extract_cbz(cbz_file, temp_dir, chapter_index=idx, optimize_for_ereader=optimize_for_ereader)

        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_file = {
                executor.submit(extract_task, i, f): f 
                for i, f in enumerate(cbz_files)
            }
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_file):
                completed += 1
                cbz_file = future_to_file[future]
                try:
                    images = future.result()
                    all_images.extend(images)
                    print(f"   {_progress_bar(completed, len(cbz_files))}  "
                          f"{cbz_file.name} → {len(images)} images")
                except Exception as e:
                    print(f"   ❌ Error extracting {cbz_file.name}: {e}")

        print()

        if not all_images:
            print("❌ No images were extracted. Aborting merge.")
            return None

        print(f"✅ Total images extracted: {len(all_images)}")
        print()

        # ── Step 3: Create metadata and merged CBZ ───────────────────────
        all_images.sort(key=lambda p: p.name)
        
        import xml.etree.ElementTree as ET
        comic_info_path = temp_dir / "ComicInfo.xml"
        try:
            root = ET.Element("ComicInfo", {
                "xmlns:xsd": "http://www.w3.org/2001/XMLSchema", 
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance"
            })
            ET.SubElement(root, "Title").text = output_path.stem
            ET.SubElement(root, "Summary").text = f"Merged {len(cbz_files)} files using CBZ Merger."
            ET.SubElement(root, "PageCount").text = str(len(all_images))
            
            tree = ET.ElementTree(root)
            tree.write(comic_info_path, encoding="utf-8", xml_declaration=True)
        except Exception:
            pass

        print("📦 Creating merged CBZ archive...")

        with zipfile.ZipFile(output_path, "w", compression=compression) as zf_out:
            if comic_info_path.exists():
                zf_out.write(comic_info_path, arcname="ComicInfo.xml")
                
            for i, img_path in enumerate(all_images):
                zf_out.write(img_path, arcname=img_path.name)

                # Print progress every 100 images or on the last one
                if (i + 1) % 100 == 0 or (i + 1) == len(all_images):
                    print(f"   {_progress_bar(i + 1, len(all_images))}")

        print()

        # ── Step 4: Summary ──────────────────────────────────────────────
        elapsed = time.time() - start_time
        merged_size = _format_size(output_path.stat().st_size)

        print("=" * 60)
        print("  ✅ MERGE COMPLETE!")
        print("=" * 60)
        print(f"  📦 Output     : {output_path}")
        print(f"  🖼️  Images     : {len(all_images)}")
        print(f"  📚 Chapters   : {len(cbz_files)}")
        print(f"  💾 File size  : {merged_size}")
        print(f"  ⏱️  Time       : {elapsed:.1f}s")
        print("=" * 60)

        return output_path

    except PermissionError:
        print(f"❌ Permission denied: Cannot write to {output_path}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error during merge: {e}")
        return None

    finally:
        # ── Step 5: Clean up ─────────────────────────────────────────────
        if temp_dir and temp_dir.exists():
            print(f"\n🧹 Cleaning up temp directory...")
            try:
                shutil.rmtree(temp_dir)
                print("   Done.")
            except Exception as e:
                print(f"   ⚠️  Could not fully clean up: {e}")


# ─── CLI Entry Point ─────────────────────────────────────────────────────────

def main():
    """Command-line interface for the CBZ merger."""
    import argparse

    parser = argparse.ArgumentParser(
        description="📚 CBZ Merger — Combine multiple .cbz files into one.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python cbz_merger.py\n"
            "  python cbz_merger.py ./manga_chapters/\n"
            "  python cbz_merger.py ./manga_chapters/ combined_volume.cbz\n"
            "  python cbz_merger.py -c ./chapters/ -o volume_1.cbz\n"
        )
    )
    parser.add_argument(
        "input_folder",
        nargs="?",
        default=".",
        help="Folder containing .cbz files (default: current directory)"
    )
    parser.add_argument(
        "output_file",
        nargs="?",
        default="merged_manga.cbz",
        help="Output filename (default: merged_manga.cbz)"
    )
    parser.add_argument(
        "-c", "--compress",
        action="store_true",
        help="Apply DEFLATE compression (smaller file, slower creation)"
    )
    parser.add_argument(
        "-e", "--ereader",
        action="store_true",
        help="Optimize for E-Readers (convert to grayscale, downscale to 1600px width, save as JPG)"
    )

    args = parser.parse_args()

    compression = zipfile.ZIP_DEFLATED if args.compress else zipfile.ZIP_STORED
    result = merge_cbz_files(args.input_folder, args.output_file, compression, args.ereader)

    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
