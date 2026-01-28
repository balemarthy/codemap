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



class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CodeMap GUI v0")
        self.resize(1200, 800)

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
        self.file_list.addItems(["(placeholder) file_a.c", "(placeholder) file_b.c"])
        left_layout.addWidget(self.file_list, 2)

        left_layout.addWidget(QLabel("Outline (functions/structs/macros)"))
        self.outline_list = QListWidget()
        self.outline_list.addItems(["(placeholder) foo()", "(placeholder) struct bar", "(placeholder) MACRO_X"])
        left_layout.addWidget(self.outline_list, 3)

        # Center: "Function map" placeholder (later we can use a custom widget)
        self.center_view = QTextEdit()
        self.center_view.setReadOnly(True)
        self.center_view.setPlainText(
            "Function Map Area\n\n"
            "- Later: show selected function details\n"
            "- Later: show callers/callees summary\n"
            "- Later: show call sites and quick jumps\n"
        )

        # Right: Tabs (Callers / Callees / CallSites)
        right_tabs = QTabWidget()

        self.callers_list = QListWidget()
        self.callers_list.addItems(["(placeholder) caller1()", "(placeholder) caller2()"])

        self.callees_list = QListWidget()
        self.callees_list.addItems(["(placeholder) callee1()", "(placeholder) callee2()"])

        self.callsites_list = QListWidget()
        self.callsites_list.addItems(["(placeholder) file.c:123:4", "(placeholder) other.c:77:10"])

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


def main() -> int:
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
