import sys
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QListWidget,
    QLineEdit,
    QTabWidget,
    QTextEdit,
    QLabel,
    QSplitter,
    QToolBar,
    QStatusBar,
)


# Fake data for Step 3 (we'll replace this with real backend later)
FAKE_PROJECT = {
    "file_a.c": {
        "outline": ["foo()", "bar()", "struct device", "MACRO_X"],
        "callers": {"foo()": ["main()", "init()"], "bar()": ["foo()"]},
        "callees": {"foo()": ["bar()", "do_work()"], "bar()": ["low_level()"]},
        "callsites": {"foo()": ["file_a.c:10:2", "file_b.c:44:8"], "bar()": ["file_a.c:31:5"]},
    },
    "file_b.c": {
        "outline": ["main()", "init()", "do_work()", "typedef ctx_t"],
        "callers": {"main()": [], "init()": ["main()"]},
        "callees": {"main()": ["init()", "foo()"], "init()": ["setup()"]},
        "callsites": {"main()": ["file_b.c:7:1"], "init()": ["file_b.c:20:3"]},
    },
}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CodeMap GUI v0")
        self.resize(1200, 800)

        # Track current selections (for Step 3)
        self.current_file: str | None = None
        self.current_symbol: str | None = None

        # Top toolbar (Back/Forward + Search)
        toolbar = QToolBar("Navigation")
        self.addToolBar(toolbar)

        self.action_back = QAction("Back", self)
        self.action_forward = QAction("Forward", self)
        toolbar.addAction(self.action_back)
        toolbar.addAction(self.action_forward)

        toolbar.addSeparator()
        toolbar.addWidget(QLabel(" Search: "))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Type symbol name…")
        toolbar.addWidget(self.search_box)

        # Status bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

        # Left panel: Files + Symbols-in-file
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(6, 6, 6, 6)

        left_layout.addWidget(QLabel("Files"))
        self.file_list = QListWidget()
        self.file_list.addItems(list(FAKE_PROJECT.keys()))
        left_layout.addWidget(self.file_list, 2)

        left_layout.addWidget(QLabel("Outline (functions/structs/macros)"))
        self.outline_list = QListWidget()
        left_layout.addWidget(self.outline_list, 3)

        # Center: "Function map" placeholder
        self.center_view = QTextEdit()
        self.center_view.setReadOnly(True)
        self.center_view.setPlainText("Select a file, then select a symbol.")

        # Right: Tabs (Callers / Callees / CallSites)
        right_tabs = QTabWidget()

        self.callers_list = QListWidget()
        self.callees_list = QListWidget()
        self.callsites_list = QListWidget()

        right_tabs.addTab(self.callers_list, "Callers")
        right_tabs.addTab(self.callees_list, "Callees")
        right_tabs.addTab(self.callsites_list, "Call Sites")

        # Splitters: Left | Center | Right
        splitter = QSplitter()
        splitter.addWidget(left_panel)
        splitter.addWidget(self.center_view)
        splitter.addWidget(right_tabs)

        splitter.setStretchFactor(0, 1)  # left
        splitter.setStretchFactor(1, 3)  # center
        splitter.setStretchFactor(2, 1)  # right

        self.setCentralWidget(splitter)

        # Wire events (Step 3 behavior)
        self.file_list.currentTextChanged.connect(self.on_file_selected)
        self.outline_list.currentTextChanged.connect(self.on_symbol_selected)

        # Auto-select first file to populate outline
        if self.file_list.count() > 0:
            self.file_list.setCurrentRow(0)

    def on_file_selected(self, filename: str) -> None:
        self.current_file = filename
        self.current_symbol = None

        self.statusBar().showMessage(f"Selected file: {filename}")

        # Populate outline list
        self.outline_list.clear()
        outline = FAKE_PROJECT[filename]["outline"]
        self.outline_list.addItems(outline)

        # Clear center + right panels
        self.center_view.setPlainText(f"File: {filename}\n\nSelect a symbol from outline.")
        self.callers_list.clear()
        self.callees_list.clear()
        self.callsites_list.clear()

        # Auto-select first outline item
        if self.outline_list.count() > 0:
            self.outline_list.setCurrentRow(0)

    def on_symbol_selected(self, symbol: str) -> None:
        if not self.current_file:
            return
        if not symbol:
            return

        self.current_symbol = symbol
        self.statusBar().showMessage(f"{self.current_file}  |  {symbol}")

        file_data = FAKE_PROJECT[self.current_file]

        callers = file_data["callers"].get(symbol, [])
        callees = file_data["callees"].get(symbol, [])
        callsites = file_data["callsites"].get(symbol, [])

        # Update center view (placeholder "map")
        self.center_view.setPlainText(
            f"Function/Symbol Map (placeholder)\n\n"
            f"File: {self.current_file}\n"
            f"Symbol: {symbol}\n\n"
            f"Callers: {len(callers)}\n"
            f"Callees: {len(callees)}\n"
            f"Call Sites: {len(callsites)}\n\n"
            f"Next: show real code + clickable jumps."
        )

        # Update right tabs
        self.callers_list.clear()
        self.callers_list.addItems(callers if callers else ["(none)"])

        self.callees_list.clear()
        self.callees_list.addItems(callees if callees else ["(none)"])

        self.callsites_list.clear()
        self.callsites_list.addItems(callsites if callsites else ["(none)"])


def main() -> int:
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
