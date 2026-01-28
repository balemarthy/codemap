from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog

from PySide6.QtWidgets import (
    QLineEdit,
    QListWidget,
    QMainWindow,
    QLabel,
    QSplitter,
    QTabWidget,
    QToolBar,
    QStatusBar,
    QWidget,
    QVBoxLayout,
)

from codemap_gui.backend.base import SymbolSummary
from codemap_gui.views.constellation import ConstellationView


class MainWindow(QMainWindow):
    # “View events” (Presenter will subscribe)
    file_selected = Signal(str)
    outline_selected = Signal(str)
    search_changed = Signal(str)
    back_clicked = Signal()
    forward_clicked = Signal()
    constellation_node_clicked = Signal(str)
    open_folder_clicked = Signal()


    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CodeMap GUI v0")
        self.resize(1200, 800)

        # Toolbar
        toolbar = QToolBar("Navigation")
        self.addToolBar(toolbar)

        self.action_open = QAction("Open Folder", self)
        toolbar.addAction(self.action_open)
        toolbar.addSeparator()


        self.action_back = QAction("Back", self)
        self.action_forward = QAction("Forward", self)
        self.action_open.triggered.connect(self.open_folder_clicked.emit)

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

        # Left panel: Files + Outline
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(6, 6, 6, 6)

        left_layout.addWidget(QLabel("Files"))
        self.file_list = QListWidget()
        left_layout.addWidget(self.file_list, 2)

        left_layout.addWidget(QLabel("Outline (functions/structs/macros)"))
        self.outline_list = QListWidget()
        left_layout.addWidget(self.outline_list, 3)

        # Center: Constellation canvas
        self.constellation = ConstellationView()

        # Right: Tabs
        right_tabs = QTabWidget()

        self.callers_list = QListWidget()
        self.callees_list = QListWidget()
        self.callsites_list = QListWidget()

        right_tabs.addTab(self.callers_list, "Callers")
        right_tabs.addTab(self.callees_list, "Callees")
        right_tabs.addTab(self.callsites_list, "Call Sites")

        # Split layout
        splitter = QSplitter()
        splitter.addWidget(left_panel)
        splitter.addWidget(self.constellation)
        splitter.addWidget(right_tabs)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 1)
        splitter.setSizes([260, 760, 300])
        self.setCentralWidget(splitter)

        # Wire raw widget events -> view signals
        self.file_list.currentTextChanged.connect(self.file_selected.emit)
        self.outline_list.currentTextChanged.connect(self.outline_selected.emit)
        self.search_box.textChanged.connect(self.search_changed.emit)

        self.action_back.triggered.connect(self.back_clicked.emit)
        self.action_forward.triggered.connect(self.forward_clicked.emit)

        self.constellation.node_clicked.connect(self.constellation_node_clicked.emit)

    # “View update” methods (Presenter will call)
    def set_files(self, files: list[str]) -> None:
        self.file_list.clear()
        self.file_list.addItems(files)
        if self.file_list.count() > 0:
            self.file_list.setCurrentRow(0)

    def set_outline(self, symbols: list[SymbolSummary]) -> None:
        self.outline_list.clear()
        for s in symbols:
            # show kind lightly, but keep label readable
            self.outline_list.addItem(f"{s.name}")

        if self.outline_list.count() > 0:
            self.outline_list.setCurrentRow(0)

    def set_callers(self, callers: list[str]) -> None:
        self.callers_list.clear()
        self.callers_list.addItems(callers if callers else ["(none)"])

    def set_callees(self, callees: list[str]) -> None:
        self.callees_list.clear()
        self.callees_list.addItems(callees if callees else ["(none)"])

    def set_callsites(self, callsites: list[str]) -> None:
        self.callsites_list.clear()
        self.callsites_list.addItems(callsites if callsites else ["(none)"])

    def show_status(self, msg: str) -> None:
        self.statusBar().showMessage(msg)

    def choose_project_folder(self) -> str | None:
        folder = QFileDialog.getExistingDirectory(self, "Select project folder")
        return folder or None

