<div align="center">
  <h1>📚 CBZ Merger</h1>
  <p><strong>Combine multiple .cbz comic/manga chapter archives into a single, properly ordered volume — with a modern dark-themed GUI or a scriptable command line.</strong></p>

  <p>
    <img alt="Python Version" src="https://img.shields.io/badge/python-3.8%2B-blue">
    <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
    <img alt="Platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgray">
  </p>
</div>

<br />

<p align="center">
  <img src="assets/screenshot.png" alt="CBZ Merger Graphical Interface Preview" width="800">
</p>

## 📖 What is this?

If you download manga/comics chapter-by-chapter, you often end up with a folder full of individual `.cbz` files (`Chapter 1.cbz`, `Chapter 2.cbz`, …). Most e-readers and comic apps are much nicer to use with one combined **volume** instead of dozens of separate chapter files.

**CBZ Merger** takes a folder of `.cbz` chapter archives and combines them into a single `.cbz` file:

- Pages are kept in the correct reading order (chapters and images are sorted *naturally*, so `Chapter 2` comes before `Chapter 10`, not after).
- Standard `ComicInfo.xml` metadata is generated automatically so comic readers show a proper title and page count.
- Optionally shrinks file size for e-readers (grayscale, downscale, JPEG re-compression) — useful for Kobo/Kindle devices with limited storage.
- Optionally splits a huge series into multiple volumes instead of one giant file.
- Optionally sets a custom cover image for the merged volume.

## ✨ Features

- ⚡ **Multi-threaded extraction** — uses all available CPU cores to unpack chapters in parallel.
- 🎨 **Dark mode GUI** — custom-drawn `tkinter` interface, no clunky default widgets.
- 📱 **E-Reader optimization** — grayscale conversion, downscaling to 1600px width, and JPEG re-compression can shrink file size by 50–70%.
- 🏷️ **Cover & metadata** — auto-detects the first page as a cover, or click/drag-and-drop your own image onto the cover box (right-click to reset to auto). Standard `ComicInfo.xml` metadata is injected automatically.
- 📦 **Volume splitting** — divide a massive series into fixed-size chunks (e.g. 15 chapters per volume) automatically, without loading everything into memory at once.
- 🎛️ **File management** — reorder chapters (⬆️/⬇️), deselect individual files, or use *Select All* / *Select None*. Drag-and-drop folders or files directly onto the window.
- 🛡️ **Overwrite protection** — asks for confirmation before silently replacing an existing output file.
- 🌍 **Localization** — switch between English and German at runtime.
- 💻 **CLI mode** — headless usage for scripts and automation.

## 🧰 Requirements

- **Python 3.8 or newer** (only if running from source — see below).
- **Pillow** — required for e-reader optimization and cover previews.
- **tkinterdnd2** — optional, only needed for drag-and-drop in the GUI. Without it, everything still works via the *Select Folder* and click-to-browse-cover buttons instead.
- `tkinter` — included with most Python installations by default (on some Linux distros you may need to install it separately, e.g. `sudo apt install python3-tk`).

---

## 🚀 Installation

### Option A: Standalone Executable (no Python required)
Go to the **[Releases](https://github.com/alxdru007/CBZ_Merger/releases)** page and download the build for your system:
- 🪟 `CBZ_Merger_Windows.exe`
- 🍎 `CBZ_Merger_macOS.zip` (extract to get the `.app`)
- 🐧 `CBZ_Merger_Linux` (mark as executable before running: `chmod +x CBZ_Merger_Linux`)

### Option B: Run from Source
Requires **Python 3.8+**.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/alxdru007/CBZ_Merger.git
   cd CBZ_Merger
   ```

2. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   # or manually:
   pip install Pillow tkinterdnd2
   ```

---

## 💻 Usage

### 🖼️ Graphical Interface (GUI)

```bash
python cbz_merger_gui.py
```

1. Click **📁 Select Folder** and choose the directory containing your chapter `.cbz` files (or drag the folder straight onto the window).
2. Review the discovered chapters in the list — deselect any you don't want, reorder them with the ⬆️/⬇️ buttons, or use **Select All** / **Select None**.
3. *(Optional)* Click the cover box (or drag an image onto it) to set a custom cover; right-click it to go back to the automatic cover.
4. *(Optional)* Toggle **E-Reader Optimization** for a smaller file, or **Split into Volumes** to break a large series into chunks.
5. Check the output filename, then hit **🔗 Start Merge** and watch the progress bar. Once done, use **📂 Open Output Folder** to jump straight to the result.

### 🖥️ Command Line Interface (CLI)

```bash
# Merge every .cbz file in the current folder into merged_manga.cbz:
python cbz_merger.py

# Specify an input folder and output file:
python cbz_merger.py ./Manga_Scans/ ./Books/Volume1.cbz

# Enable DEFLATE compression (smaller file, slower to create):
python cbz_merger.py --compress ./Manga_Scans/

# Enable E-Reader optimization (grayscale, downscaled, re-compressed):
python cbz_merger.py --ereader ./Manga_Scans/ ./FinalBook.cbz

# Combine both flags:
python cbz_merger.py -c -e ./Manga_Scans/ ./FinalBook.cbz
```

Run `python cbz_merger.py --help` for the full list of options.

---

## 🛠️ Architecture

* [`cbz_merger.py`](cbz_merger.py) — Core logic, also usable standalone as a CLI. Uses `concurrent.futures.ThreadPoolExecutor` to extract chapters in parallel and `xml.etree.ElementTree` to write `ComicInfo.xml` metadata. Can be imported as a module:
  ```python
  from cbz_merger import merge_cbz_files
  merge_cbz_files("./my_manga/", "combined.cbz")
  ```
* [`cbz_merger_gui.py`](cbz_merger_gui.py) — `tkinter` / `tkinterdnd2` GUI built on custom Canvas widgets (`GradientButton`, `GlowProgressBar`, scrollable file list, live cover preview). Runs merges on a background thread so the interface never freezes, with safe cancellation support. Imports and reuses the core logic from `cbz_merger.py` rather than duplicating it.

---

## 🤝 Contributing

Contributions, issues and feature requests are welcome! Feel free to check the [issues page].

## 📄 License
This project is [MIT](LICENSE) licensed. Feel free to use it, modify it, and distribute it!

<p align="center"><i>Crafted with passion for Manga & Comic enthusiasts!</i></p>
