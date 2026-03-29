<div align="center">
  <h1>📚 CBZ Merger</h1>
  <p><strong>A blazingly fast, multi-threaded comic archive (.cbz) merger with a modern, responsive UI and E-Reader optimizations.</strong></p>

  <p>
    <img alt="Python Version" src="https://img.shields.io/badge/python-3.8%2B-blue">
    <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
    <img alt="Platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgray">
  </p>
</div>

<br />

## ✨ Features

- ⚡ **Multi-Threaded Performance**: Extracts and packages large comic/manga archives asynchronously. Uses all available CPU cores to reduce processing time drastically!
- 🎨 **Premium Dark Mode GUI**: Fully responsive custom-drawn `tkinter` canvas UI with smooth gradients and hover animations. Adapts perfectly to both small window sizes and fullscreen modes.
- 📱 **E-Reader Optimization Engine**: Built specifically for Kobo, Kindle, and other e-ink displays. Shrinks file size by up to 50–70% via:
  - Lossless Grayscale (B/W) conversion
  - Smart resolution downscaling (Max width: 1600px)
  - Highly efficient JPEG compression 
- 🏷️ **Intelligent Metadata Generation**: Automatically calculates page lengths and injects a standard `ComicInfo.xml` file into the merged `.cbz` archive so e-readers (like Mihon, Perfect Viewer, CDisplayEX) parse chapters and titles flawlessly.
- 📁 **Natural Alphabetical Sorting**: Recognizes numbers inside filenames the way humans do (`Chapter_2.cbz` comes before `Chapter_10.cbz`).
- 💻 **CLI Capability**: Headless use supported! Perfect for batch automation via scripts.

---

## 🚀 Installation

Ensure you have **Python 3.8+** installed on your system. 

1. **Clone the repository:**
```bash
git clone https://github.com/YourUsername/CBZ_Merger.git
cd CBZ_Merger
```

2. **Install the required library for Image Processing (Pillow):**
```bash
pip install -r requirements.txt
# OR simply run:
pip install Pillow
```

---

## 💻 Usage

### 🖼️ Graphical Interface (GUI)
The most convenient way to use the program is via its gorgeous interface.

```bash
python cbz_merger_gui.py
```
**How to use:**
1. Click **Select Folder** and navigate to the directory holding your individual chapter `.cbz` files.
2. Ensure the output target name looks correct (e.g., `MyManga_Volume1.cbz`).
3. *(Optional)* Toggle **E-Reader Optimization** if you want smaller files for e-ink devices.
4. Hit **🔗 Start Merge** and watch the multi-threaded progress bar fly!

### 🖥️ Command Line Interface (CLI)
You can easily automate your manga compilation using the script headless. 

```bash
# Basic usage (merges all files in the current folder):
python cbz_merger.py

# Specify Input & Output:
python cbz_merger.py C:/Manga_Scans/ C:/Books/Volume1.cbz

# Enable DEFLATE Archiving Compression:
python cbz_merger.py --compress

# Enable E-Reader Optimization (Grayscale / Resizing):
python cbz_merger.py --ereader ./ChapterFolder/ ./FinalBook.cbz
```

---

## 🛠️ Architecture

* `cbz_merger.py` - Core logic. Uses `concurrent.futures.ThreadPoolExecutor` to execute unzipping protocols concurrently while side-stepping GIL limitations during file I/O operations. Uses `xml.etree.ElementTree` to write metadata XML trees.
* `cbz_merger_gui.py` - Custom-built Tkinter implementation featuring pure Canvas-based interactive elements (`GradientButton`, `GlowProgressBar`). Features zero external GUI constraints.

---

## 🤝 Contributing

Contributions, issues and feature requests are welcome! Feel free to check the [issues page].

## 📄 License
This project is [MIT](LICENSE) licensed. Feel free to use it, modify it, and distribute it!

<p align="center"><i>Crafted with passion for Manga & Comic enthusiasts!</i></p>
