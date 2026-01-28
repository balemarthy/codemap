from __future__ import annotations

from codemap_gui.backend.base import CodeMapBackend, OneHop, SymbolKind, SymbolSummary


class MockBackend(CodeMapBackend):
    """Fake backend for wiring UI behavior without touching real engine yet."""

    def __init__(self) -> None:
        self._files = ["file_a.c", "file_b.c"]

        self._outline = {
            "file_a.c": [
                SymbolSummary("foo()", SymbolKind.FUNCTION),
                SymbolSummary("bar()", SymbolKind.FUNCTION),
                SymbolSummary("struct device", SymbolKind.STRUCT),
                SymbolSummary("MACRO_X", SymbolKind.MACRO),
            ],
            "file_b.c": [
                SymbolSummary("main()", SymbolKind.FUNCTION),
                SymbolSummary("init()", SymbolKind.FUNCTION),
                SymbolSummary("do_work()", SymbolKind.FUNCTION),
                SymbolSummary("typedef ctx_t", SymbolKind.TYPEDEF),
            ],
        }

        self._callers = {
            "foo()": ["main()", "init()"],
            "bar()": ["foo()"],
            "main()": [],
            "init()": ["main()"],
            "do_work()": ["foo()"],
            "struct device": [],
            "MACRO_X": [],
            "typedef ctx_t": [],
        }

        self._callees = {
            "foo()": ["bar()", "do_work()"],
            "bar()": ["low_level()"],
            "main()": ["init()", "foo()"],
            "init()": ["setup()"],
            "do_work()": ["low_level()"],
            "struct device": [],
            "MACRO_X": [],
            "typedef ctx_t": [],
        }

        self._callsites = {
            "foo()": ["file_a.c:10:2", "file_b.c:44:8"],
            "bar()": ["file_a.c:31:5"],
            "main()": ["file_b.c:7:1"],
            "init()": ["file_b.c:20:3"],
            "do_work()": ["file_b.c:55:12"],
        }

    def list_files(self) -> list[str]:
        return list(self._files)

    def list_outline(self, filename: str) -> list[SymbolSummary]:
        return list(self._outline.get(filename, []))

    def one_hop(self, symbol: str) -> OneHop:
        callers = self._callers.get(symbol, [])
        callees = self._callees.get(symbol, [])
        callsites = self._callsites.get(symbol, [])
        return OneHop(center=symbol, callers=callers, callees=callees, callsites=callsites)
