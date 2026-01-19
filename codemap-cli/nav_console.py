# nav_console_v3.py
# Console Code Map Navigator 
# - Discoverable help banner on startup (no full help dump)
# - Back/Forward history
# - Bookmarks + session.json save
# - Jump to definitions + callsites + caller sites
#
# Usage:
#   python nav_console_v3.py <path_to_callgraph_json OR folder_containing_json>

import json
import sys
from pathlib import Path
from datetime import datetime

HELP = """
Commands:
  s          - search & select function (substring match)
  o          - open current function definition (choose candidate)
  c          - list callees (unique) for current function
  cs         - jump to a call site (choose callee, then site)
  cb         - list who-calls-this (choose a caller site to jump)
  jd         - jump to definition of a symbol (if found in functions)
  b          - back
  f          - forward
  m          - bookmark current view
  marks      - list bookmarks
  save       - save session.json (history + bookmarks)
  help / ?   - show this help
  q          - quit
"""

BANNER = """
===================================================
 Console Code Map Navigator (V3)
===================================================
Type 'help' or '?' at any time to see all commands.

Quick start:
  s   -> search & select function
  o   -> open function definition
  cs  -> jump to call site
  cb  -> who calls this symbol
  b/f -> back / forward
  m   -> bookmark current view
  q   -> quit
"""


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_lines(file_path, encoding="utf-8"):
    return Path(file_path).read_text(encoding=encoding, errors="replace").splitlines()


def snippet(file_path, line, context=8):
    lines = read_lines(file_path)
    n = len(lines)
    start = max(1, line - context)
    end = min(n, line + context)
    out = []
    for ln in range(start, end + 1):
        prefix = ">>" if ln == line else "  "
        out.append(f"{prefix} {ln:5d}: {lines[ln - 1]}")
    return "\n".join(out)


def pick(items, prompt):
    if not items:
        return None
    for i, item in enumerate(items, 1):
        print(f"{i:3d}) {item}")
    while True:
        s = input(prompt).strip()
        if s.lower() in ("q", "quit", "exit"):
            return None
        if s.isdigit():
            k = int(s)
            if 1 <= k <= len(items):
                return items[k - 1]
        print("Enter a valid number, or 'q' to cancel.")


class Navigator:
    def __init__(self, data, session_path: Path):
        self.data = data
        self.functions = data.get("functions", {})               # name -> list[loc]
        self.calls = data.get("calls", {})                       # caller -> [callee...]
        self.call_sites = data.get("call_sites", {})             # caller -> [site...]
        self.called_by_sites = data.get("called_by_sites", {})   # callee -> [callerSite...]

        self.session_path = session_path
        self.history = []
        self.future = []
        self.bookmarks = []

        self.current = None  # dict describing current view

    def _push(self, state):
        if self.current is not None:
            self.history.append(self.current)
            self.future.clear()
        self.current = state

    def back(self):
        if not self.history:
            print("No back history.")
            return
        self.future.append(self.current)
        self.current = self.history.pop()

    def forward(self):
        if not self.future:
            print("No forward history.")
            return
        self.history.append(self.current)
        self.current = self.future.pop()

    def save_session(self):
        payload = {
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "root": self.data.get("root"),
            "index_file": str(self.session_path.parent),
            "current": self.current,
            "history": self.history[-200:],      # cap
            "bookmarks": self.bookmarks[-200:],  # cap
        }
        self.session_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Saved session: {self.session_path}")

    def mark(self):
        if not self.current:
            print("Nothing to bookmark.")
            return
        self.bookmarks.append(self.current)
        print("Bookmarked.")

    def list_marks(self):
        if not self.bookmarks:
            print("No bookmarks yet.")
            return
        for i, bm in enumerate(self.bookmarks, 1):
            kind = bm.get("kind", "view")
            title = bm.get("title", "")
            loc = bm.get("loc", "")
            print(f"{i:3d}) [{kind}] {title} {loc}")

    def search_function(self, query):
        names = sorted(self.functions.keys())
        return [n for n in names if query in n]

    def set_current_function(self, fn_name):
        locs = self.functions.get(fn_name, [])
        loc_hint = f"{len(locs)} defs" if locs else "no def"
        self._push({"kind": "function", "title": fn_name, "loc": loc_hint, "fn": fn_name})

    def open_definition(self, fn_name):
        locs = self.functions.get(fn_name, [])
        if not locs:
            print(f"No definition locations found for {fn_name} in this snapshot.")
            return

        menu = [f'{l["file"]}:{l["start_line"]}-{l["end_line"]}' for l in locs[:80]]
        picked = pick(menu, "Pick definition #> ")
        if not picked:
            return

        file_part, range_part = picked.rsplit(":", 1)
        start_line = int(range_part.split("-", 1)[0])

        self._push({
            "kind": "definition",
            "title": fn_name,
            "loc": f"{file_part}:{start_line}",
            "file": file_part,
            "line": start_line,
        })
        print("\n" + snippet(file_part, start_line, context=10) + "\n")

    def list_callees(self, fn_name):
        callees = self.calls.get(fn_name, [])
        return sorted(set(callees))

    def jump_callsite(self, fn_name):
        sites = self.call_sites.get(fn_name, [])
        if not sites:
            print("No call sites for this function.")
            return

        # callee -> count
        counts = {}
        for s in sites:
            counts[s["callee"]] = counts.get(s["callee"], 0) + 1

        callee_menu = [f"{k}  ({v} sites)" for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]
        chosen = pick(callee_menu[:120], "Pick callee #> ")
        if not chosen:
            return
        callee = chosen.split("  (")[0]

        chosen_sites = [s for s in sites if s["callee"] == callee]
        site_menu = [f'{s["file"]}:{s["line"]}:{s["col"]}' for s in chosen_sites[:300]]
        picked_site = pick(site_menu, "Pick site #> ")
        if not picked_site:
            return

        file_part, line_part, col_part = picked_site.rsplit(":", 2)
        line = int(line_part)
        col = int(col_part)

        self._push({
            "kind": "callsite",
            "title": f"{fn_name} -> {callee}",
            "loc": f"{file_part}:{line}:{col}",
            "file": file_part,
            "line": line,
            "col": col,
            "caller": fn_name,
            "callee": callee,
        })

        print("\n" + snippet(file_part, line, context=10) + "\n")

    def who_calls_symbol_menu(self, symbol):
        items = self.called_by_sites.get(symbol, [])
        menu = [f'{i["caller"]} @ {i["file"]}:{i["line"]}:{i["col"]}' for i in items[:400]]
        return menu

    def jump_to_definition_of_symbol(self, symbol):
        if symbol not in self.functions:
            print(f"No definitions found for {symbol} in this snapshot.")
            return
        self.open_definition(symbol)

    def describe_current(self):
        if not self.current:
            return "(no selection)"
        return f'[{self.current.get("kind")}] {self.current.get("title")} {self.current.get("loc","")}'


def resolve_index_path(arg: str) -> Path:
    p = Path(arg)
    if p.is_dir():
        # Auto-select the newest callgraph json in folder
        candidates = sorted(p.glob("*callgraph*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        if not candidates:
            candidates = sorted(p.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        if not candidates:
            raise SystemExit(f"No JSON found in folder: {p}")
        p = candidates[0]
        print(f"Auto-selected JSON: {p}")
    return p


def main(index_json_or_folder: str):
    p = resolve_index_path(index_json_or_folder)
    data = load_json(p)

    session_path = p.parent / "session.json"
    nav = Navigator(data, session_path)

    print(BANNER.strip())
    print()
    print("Loaded index:", p)
    print()

    while True:
        print("Current:", nav.describe_current())
        cmd = input("cmd> ").strip().lower()

        if cmd in ("q", "quit", "exit"):
            break

        if cmd in ("help", "?"):
            print(HELP.strip() + "\n")
            continue

        if cmd == "s":
            q = input("Search substring> ").strip()
            if not q:
                continue
            matches = nav.search_function(q)
            if not matches:
                print("No matches.\n")
                continue
            chosen = pick(matches[:120], "Pick function #> ")
            if not chosen:
                print()
                continue
            nav.set_current_function(chosen)
            print()
            continue

        if cmd == "o":
            if not nav.current or nav.current.get("kind") != "function":
                print("Select a function first (cmd: s).\n")
                continue
            nav.open_definition(nav.current["fn"])
            continue

        if cmd == "c":
            if not nav.current or nav.current.get("kind") != "function":
                print("Select a function first (cmd: s).\n")
                continue
            fn = nav.current["fn"]
            callees = nav.list_callees(fn)
            if not callees:
                print("No callees.\n")
                continue
            for c in callees[:200]:
                print("  ->", c)
            print()
            continue

        if cmd == "cs":
            if not nav.current or nav.current.get("kind") != "function":
                print("Select a function first (cmd: s).\n")
                continue
            nav.jump_callsite(nav.current["fn"])
            continue

        if cmd == "cb":
            if not nav.current:
                print("No current selection.\n")
                continue

            # If current is function, use its name. If callsite/caller_site, use its symbol fields.
            if nav.current.get("kind") == "function":
                symbol = nav.current.get("fn")
            else:
                symbol = nav.current.get("callee") or nav.current.get("title")

            if not symbol:
                print("No symbol to query.\n")
                continue

            menu = nav.who_calls_symbol_menu(symbol)
            if not menu:
                print("No callers found for:", symbol, "\n")
                continue

            chosen = pick(menu, "Pick caller site #> ")
            if not chosen:
                print()
                continue

            caller_part, loc_part = chosen.split(" @ ", 1)
            file_part, line_part, col_part = loc_part.rsplit(":", 2)
            line = int(line_part)
            col = int(col_part)

            nav._push({
                "kind": "caller_site",
                "title": f"{caller_part} -> {symbol}",
                "loc": f"{file_part}:{line}:{col}",
                "file": file_part,
                "line": line,
                "col": col,
                "caller": caller_part,
                "callee": symbol,
            })

            print("\n" + snippet(file_part, line, context=10) + "\n")
            continue

        if cmd == "jd":
            sym = input("Symbol name> ").strip()
            if not sym:
                continue
            nav.jump_to_definition_of_symbol(sym)
            continue

        if cmd == "b":
            nav.back()
            print()
            continue

        if cmd == "f":
            nav.forward()
            print()
            continue

        if cmd == "m":
            nav.mark()
            print()
            continue

        if cmd == "marks":
            nav.list_marks()
            print()
            continue

        if cmd == "save":
            nav.save_session()
            print()
            continue

        print("Unknown command. Type 'help' or '?'.\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python nav_console_v3.py <path_to_callgraph_json OR folder_containing_json>")
        raise SystemExit(1)

    main(sys.argv[1])
