import json
import os
import sys
from pathlib import Path
from collections import defaultdict

from tree_sitter import Parser
from tree_sitter_languages import get_language

C_LANGUAGE = get_language("c")


def walk(node):
    yield node
    for child in node.children:
        yield from walk(child)


def find_identifier_in_subtree(node, code: bytes):
    for n in walk(node):
        if n.type == "identifier":
            return code[n.start_byte:n.end_byte].decode("utf-8", errors="replace")
    return None


def get_function_name(fn_node, code: bytes) -> str:
    decl = fn_node.child_by_field_name("declarator")
    if not decl:
        return "<unknown>"
    name = find_identifier_in_subtree(decl, code)
    return name or "<unknown>"


def iter_source_files(root: Path):
    ignore_dirs = {
        ".git", ".svn", ".hg",
        "build", "cmake-build-debug", "cmake-build-release",
        ".vscode", ".idea",
        "venv", ".venv", "__pycache__",
        "node_modules"
    }

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.startswith(".")]
        for fn in filenames:
            if fn.endswith((".c", ".h")):
                yield Path(dirpath) / fn


def analyze_folder(folder: Path):
    parser = Parser()
    parser.set_language(C_LANGUAGE)

    # multi-def: name -> list[{file,start_line,end_line}]
    functions = defaultdict(list)

    # caller -> list[callee...]
    calls_map = defaultdict(list)

    # caller -> list[{callee,file,line,col}]
    call_sites = defaultdict(list)

    file_errors = []

    for path in iter_source_files(folder):
        try:
            code = path.read_bytes()
        except Exception as e:
            file_errors.append({"file": str(path), "error": f"read failed: {e}"})
            continue

        try:
            tree = parser.parse(code)
        except Exception as e:
            file_errors.append({"file": str(path), "error": f"parse failed: {e}"})
            continue

        root = tree.root_node

        for n in walk(root):
            if n.type != "function_definition":
                continue

            fn_name = get_function_name(n, code)
            if fn_name == "<unknown>":
                continue

            start_row, _ = n.start_point
            end_row, _ = n.end_point
            functions[fn_name].append({
                "file": str(path),
                "start_line": start_row + 1,
                "end_line": end_row + 1,
            })

            # extract call expressions within this function
            for sub in walk(n):
                if sub.type == "call_expression":
                    fn = sub.child_by_field_name("function")
                    if not fn:
                        continue

                    callee = code[fn.start_byte:fn.end_byte].decode("utf-8", errors="replace")
                    calls_map[fn_name].append(callee)

                    line = fn.start_point[0] + 1
                    col = fn.start_point[1] + 1
                    call_sites[fn_name].append({
                        "callee": callee,
                        "file": str(path),
                        "line": line,
                        "col": col,
                    })

    # callee -> list[{caller,file,line,col}]
    called_by_sites = defaultdict(list)
    for caller, sites in call_sites.items():
        for s in sites:
            called_by_sites[s["callee"]].append({
                "caller": caller,
                "file": s["file"],
                "line": s["line"],
                "col": s["col"],
            })

    result = {
        "root": str(folder),
        "functions": dict(functions),
        "calls": {k: v for k, v in calls_map.items()},
        "call_sites": {k: v for k, v in call_sites.items()},
        "called_by_sites": dict(called_by_sites),
        "stats": {
            "num_functions": sum(len(v) for v in functions.values()),
            "num_unique_function_names": len(functions),
            "num_callers": len(calls_map),
            "num_call_sites": sum(len(v) for v in call_sites.values()),
            "num_files_with_errors": len(file_errors),
        },
        "errors": file_errors,
    }
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_folder_callsites_v2.py <folder_path> [output.json]")
        raise SystemExit(1)

    folder = Path(sys.argv[1]).resolve()
    if not folder.exists() or not folder.is_dir():
        raise SystemExit(f"Folder not found: {folder}")

    out_path = Path(sys.argv[2]).resolve() if len(sys.argv) >= 3 else (folder / "_callgraph_callsites.json")

    result = analyze_folder(folder)

    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Saved: {out_path}")
    print(f"Unique function names: {result['stats']['num_unique_function_names']}")
    print(f"Total function defs:   {result['stats']['num_functions']}")
    print(f"Callers with calls:    {result['stats']['num_callers']}")
    print(f"Call sites:            {result['stats']['num_call_sites']}")
    if result["stats"]["num_files_with_errors"]:
        print(f"Files with errors:     {result['stats']['num_files_with_errors']} (see JSON -> errors)")


if __name__ == "__main__":
    main()
