# 🤝 Contributing to CBZ Merger

First of all, thank you for stopping by! 🎉 **CBZ Merger** started as a passion project to make comic collections perfect for E-Readers, and it grows stronger with every contributor. 

Whether you are a Python pro, a UI designer, or just someone who found a typo – **we want your help!**

---

### 🚀 Why Contribute?

* **Performance First:** Work on a "blazingly fast" multi-threaded engine.
* **Modern UI:** Help us refine a custom-drawn `tkinter` Dark Mode interface.
* **Real Impact:** Your code will help thousands of Manga & Comic fans optimize their libraries for Kindle, Kobo, and more.
* **Get Recognized:** Every contributor gets credited. It’s a great way to boost your GitHub portfolio!

---

### 💡 How You Can Help

You don't need to be a senior dev to contribute:

1.  **Reporting Bugs:** Found a crash while merging 100+ chapters? Open an [Issue](https://github.com/alxdru007/CBZ_Merger/issues).
2.  **Suggesting Features:** Want support for `.cbr` or new E-Ink filters? Let’s talk about it!
3.  **Code Improvements:** Help us optimize image compression or refactor the `ThreadPoolExecutor` logic.
4.  **Localization:** Help us translate the UI into more languages (beyond DE/EN).
5.  **Design:** Improve the Canvas-based UI animations or icons.

---

### 🛠️ Quick Start (Development)

1.  **Fork** this repository.
2.  **Clone** your fork:
    ```bash
    git clone [https://github.com/your-username/CBZ_Merger.git](https://github.com/your-username/CBZ_Merger.git)
    cd CBZ_Merger
    ```
3.  **Set up a virtual environment**:
    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # Linux/macOS:
    source venv/bin/activate
    ```
4.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
5.  **Run the GUI**:
    ```bash
    python cbz_merger_gui.py
    ```

---

### 📏 Our Standards

To keep the code clean and the UI "premium", please keep these in mind:

* **PEP 8:** We try to follow standard Python styling.
* **Thread Safety:** Since the merger is multi-threaded, always ensure your changes don't freeze the main GUI thread.
* **UI Consistency:** Use the existing `GradientButton` and canvas styles for any new UI elements.
* **Documentation:** If you add a new CLI flag or feature, please update the README.

---

### 👋 Questions?

Not sure where to start? Just open a "General Question" issue or comment on an existing one. We are a friendly bunch and happy to guide you through your first Pull Request!

**Let's build the ultimate Manga tool together!** 📚⚡
