from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from codemap_gui.backend.base import CodeMapBackend, OneHop, ProjectInfo, SymbolKind, SymbolSummary


class WorkspaceBackend(CodeMapBackend):
    """
    Workspace-backed backend.

    Responsibilities:
      1) open_project(root_dir): runs indexer, stores outputs in <root>/.codemap/
      2) loads .codemap/_callgraph_callsites.json into in-memory structures
      3) serves UI via list_files / list_outline / one_hop
    """

    def __init__(self) -> None:
        self._project: ProjectInfo | None = None

        # Backward-compatible fields (keep these names)
        self._files: list[str] = []
        self._outline: dict[str, list[SymbolSummary]] = {}
        self._callers: dict[str, list[str]] = {}
        self._callees: dict[str, list[str]] = {}
        self._callsites: dict[str, list[str]] = {}

        # Internal (richer) callsite maps used to build _callsites on-demand
        self._call_sites_out: dict[str, list[dict[str, Any]]] = {}
        self._call_sites_in: dict[str, list[dict[str, Any]]] = {}

    def open_project(self, root_dir: str) -> ProjectInfo:
        import sys
        import subprocess
        import shutil

        root = Path(root_dir)
        workspace = root / ".codemap"
        workspace.mkdir(parents=True, exist_ok=True)

        index_callsites_path = workspace / "_callgraph_callsites.json"
        index_callgraph_path = workspace / "_callgraph.json"

        # Find repo root by walking up until we see codemap-indexer/
        here = Path(__file__).resolve()
        repo_root = None
        for p in [here.parent] + list(here.parents):
            if (p / "codemap-indexer").is_dir():
                repo_root = p
                break

        if repo_root is None:
            raise FileNotFoundError("Could not locate repo root containing 'codemap-indexer' folder.")

        script_path = repo_root / "codemap-indexer" / "analyze_folder_callsites.py"
        if not script_path.exists():
            raise FileNotFoundError(f"Missing indexer script: {script_path}")

        cmd = [sys.executable, str(script_path), str(root)]
        result = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(
                "Indexer failed.\n"
                f"CMD: {' '.join(cmd)}\n\n"
                f"STDOUT:\n{result.stdout}\n\n"
                f"STDERR:\n{result.stderr}\n"
            )

        # Script outputs in the selected root folder (current behavior)
        generated_callsites = root / "_callgraph_callsites.json"
        generated_callgraph = root / "_callgraph.json"

        if not generated_callsites.exists():
            raise FileNotFoundError(f"Indexer ran but did not create: {generated_callsites}")

        # Move outputs into .codemap (keep root clean)
        if index_callsites_path.exists():
            index_callsites_path.unlink()
        shutil.move(str(generated_callsites), str(index_callsites_path))

        if generated_callgraph.exists():
            if index_callgraph_path.exists():
                index_callgraph_path.unlink()
            shutil.move(str(generated_callgraph), str(index_callgraph_path))

        self._project = ProjectInfo(
            root_dir=str(root),
            workspace_dir=str(workspace),
            index_json_path=str(index_callsites_path),
        )

        # NEW: load the index right away so UI shows real data
        self._load_index_from_json(index_callsites_path=index_callsites_path, selected_root=root)

        return self._project

    def _load_index_from_json(self, index_callsites_path: Path, selected_root: Path) -> None:
        data = json.loads(index_callsites_path.read_text(encoding="utf-8"))

        # Prefer JSON "root" if present, else fallback to the folder user selected
        root_for_rel = selected_root
        json_root = data.get("root")
        if isinstance(json_root, str) and json_root.strip():
            try:
                root_for_rel = Path(json_root)
            except Exception:
                root_for_rel = selected_root

        root_for_rel_resolved = root_for_rel.resolve()

        def relpath(p: str) -> str:
            try:
                return str(Path(p).resolve().relative_to(root_for_rel_resolved))
            except Exception:
                return p  # fallback: keep absolute if we can't relativize

        functions: dict[str, list[dict[str, Any]]] = data.get("functions", {}) or {}
        calls: dict[str, list[str]] = data.get("calls", {}) or {}
        call_sites: dict[str, list[dict[str, Any]]] = data.get("call_sites", {}) or {}
        called_by_sites: dict[str, list[dict[str, Any]]] = data.get("called_by_sites", {}) or {}

        files_set: set[str] = set()
        outline_names_by_file: dict[str, set[str]] = defaultdict(set)

        # Build files + outline from function definitions
        for func_name, defs in functions.items():
            if not isinstance(defs, list):
                continue
            for d in defs:
                file_abs = d.get("file")
                if not file_abs:
                    continue
                rf = relpath(str(file_abs))
                files_set.add(rf)
                outline_names_by_file[rf].add(str(func_name))

        # Also include files referenced in outgoing call sites (useful sometimes)
        for _, sites in call_sites.items():
            if not isinstance(sites, list):
                continue
            for s in sites:
                file_abs = s.get("file")
                if file_abs:
                    files_set.add(relpath(str(file_abs)))

        # Convert outline names into SymbolSummary (v1: functions only)
        outline: dict[str, list[SymbolSummary]] = {}
        for rf, names in outline_names_by_file.items():
            outline[rf] = [
                SymbolSummary(name=n, kind=SymbolKind.FUNCTION)
                for n in sorted(names, key=str.lower)
            ]

        # Build callees map (caller -> unique callees)
        callees: dict[str, list[str]] = {}
        for caller, callee_list in calls.items():
            if isinstance(callee_list, list):
                callees[str(caller)] = sorted({str(x) for x in callee_list}, key=str.lower)
            else:
                callees[str(caller)] = []

        # Build callers map (callee -> unique callers) from called_by_sites
        callers_set_map: dict[str, set[str]] = defaultdict(set)
        call_sites_in: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for callee, sites in called_by_sites.items():
            if not isinstance(sites, list):
                continue
            for s in sites:
                caller = s.get("caller")
                if caller:
                    callers_set_map[str(callee)].add(str(caller))

                file_abs = s.get("file", "")
                call_sites_in[str(callee)].append(
                    {
                        "caller": str(caller or ""),
                        "file": relpath(str(file_abs)) if file_abs else "",
                        "line": int(s.get("line", 0)),
                        "col": int(s.get("col", 0)),
                    }
                )

        callers = {k: sorted(v, key=str.lower) for k, v in callers_set_map.items()}

        # Normalize outgoing call sites (caller -> list)
        call_sites_out: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for caller, sites in call_sites.items():
            if not isinstance(sites, list):
                continue
            for s in sites:
                file_abs = s.get("file", "")
                call_sites_out[str(caller)].append(
                    {
                        "callee": str(s.get("callee", "")),
                        "file": relpath(str(file_abs)) if file_abs else "",
                        "line": int(s.get("line", 0)),
                        "col": int(s.get("col", 0)),
                    }
                )

        # Save into backward-compatible fields
        self._files = sorted(files_set, key=str.lower)
        self._outline = outline
        self._callers = callers
        self._callees = callees

        # Keep richer maps; _callsites (strings) will be built on demand in one_hop()
        self._call_sites_out = dict(call_sites_out)
        self._call_sites_in = dict(call_sites_in)

        # Optional: clear any stale cached callsite strings
        self._callsites = {}

    # ---- UI-facing API (unchanged signatures) ----

    def list_files(self) -> list[str]:
        return list(self._files)

    def list_outline(self, filename: str) -> list[SymbolSummary]:
        return list(self._outline.get(filename, []))

    def one_hop(self, symbol: str) -> OneHop:
        callers = self._callers.get(symbol, [])
        callees = self._callees.get(symbol, [])

        # Build callsite strings for THIS symbol (v1). Cache in _callsites.
        if symbol not in self._callsites:
            lines: list[str] = []

            # OUT: symbol calls others
            for s in self._call_sites_out.get(symbol, []):
                lines.append(
                    f"OUT  {s.get('file','')}:{s.get('line',0)}:{s.get('col',0)} -> {s.get('callee','')}"
                )

            # IN: others call symbol
            for s in self._call_sites_in.get(symbol, []):
                lines.append(
                    f"IN   {s.get('file','')}:{s.get('line',0)}:{s.get('col',0)} <- {s.get('caller','')}"
                )

            self._callsites[symbol] = lines

        return OneHop(
            center=symbol,
            callers=callers,
            callees=callees,
            callsites=self._callsites.get(symbol, []),
        )
