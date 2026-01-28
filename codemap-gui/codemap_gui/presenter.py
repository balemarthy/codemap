from __future__ import annotations

from dataclasses import dataclass, field

from codemap_gui.backend.base import CodeMapBackend, SymbolSummary
from codemap_gui.views.main_window import MainWindow


@dataclass
class NavigationState:
    current_symbol: str | None = None
    back_stack: list[str] = field(default_factory=list)
    forward_stack: list[str] = field(default_factory=list)


class CodeMapPresenter:
    def __init__(self, view: MainWindow, backend: CodeMapBackend) -> None:
        self._view = view
        self._backend = backend
        self._nav = NavigationState()
        self._current_file: str | None = None
        self._full_outline: list[SymbolSummary] = []
        self._project_root: str | None = None
        self._index_path: str | None = None

    def start(self) -> None:
        # Connect view events
        self._view.file_selected.connect(self.on_file_selected)
        self._view.outline_selected.connect(self.on_outline_selected)
        self._view.search_changed.connect(self.on_search_changed)
        self._view.back_clicked.connect(self.on_back)
        self._view.forward_clicked.connect(self.on_forward)
        self._view.constellation_node_clicked.connect(self.on_constellation_node_clicked)
        self._view.open_folder_clicked.connect(self.on_open_folder)


        # Initial load
        files = self._backend.list_files()
        self._view.set_files(files)

    def on_file_selected(self, filename: str) -> None:
        self._current_file = filename
        self._view.show_status(f"Selected file: {filename}")

        self._full_outline = self._backend.list_outline(filename)
        self._view.set_outline(self._full_outline)

    def on_outline_selected(self, text: str) -> None:
        symbol = text.strip()
        if not symbol:
            return
        self.navigate_to(symbol, push_history=True)

    def on_constellation_node_clicked(self, symbol: str) -> None:
        # User clicked a node in the constellation. Go deep.
        self.navigate_to(symbol, push_history=True)

    def on_search_changed(self, query: str) -> None:
        q = query.strip().lower()
        if not q:
            self._view.set_outline(self._full_outline)
            return

        filtered = [s for s in self._full_outline if q in s.name.lower()]
        self._view.set_outline(filtered)

    def on_back(self) -> None:
        if not self._nav.back_stack or not self._nav.current_symbol:
            return
        prev = self._nav.back_stack.pop()
        self._nav.forward_stack.append(self._nav.current_symbol)
        self.navigate_to(prev, push_history=False)

    def on_forward(self) -> None:
        if not self._nav.forward_stack or not self._nav.current_symbol:
            return
        nxt = self._nav.forward_stack.pop()
        self._nav.back_stack.append(self._nav.current_symbol)
        self.navigate_to(nxt, push_history=False)

    def on_open_folder(self) -> None:
        folder = self._view.choose_project_folder()
        if not folder:
            self._view.show_status("Open folder cancelled.")
            return

        info = self._backend.open_project(folder)
   
        # Clear UI
        self._view.file_list.clear()
        self._view.outline_list.clear()
        self._view.callers_list.clear()
        self._view.callees_list.clear()
        self._view.callsites_list.clear()
        self._view.constellation.clear()

        self._view.show_status(f"Opened: {info.root_dir}  |  Index: {info.index_json_path}")

        # Files are empty for now. Next action will load real JSON and populate.
        self._view.set_files(self._backend.list_files())



    def navigate_to(self, symbol: str, push_history: bool) -> None:
        # history rules
        if push_history and self._nav.current_symbol and self._nav.current_symbol != symbol:
            self._nav.back_stack.append(self._nav.current_symbol)
            self._nav.forward_stack.clear()

        self._nav.current_symbol = symbol

        hop = self._backend.one_hop(symbol)

        self._view.set_callers(list(hop.callers))
        self._view.set_callees(list(hop.callees))
        self._view.set_callsites(list(hop.callsites))
        self._view.constellation.set_graph(center=hop.center, callers=list(hop.callers), callees=list(hop.callees))

        file_part = f"{self._current_file}  |  " if self._current_file else ""
        self._view.show_status(f"{file_part}{symbol}")
