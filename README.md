# CodeMap

**Map your code. Understand the system.**

A **console‑first source mapping and navigation tool** inspired by Source Insight.

CodeMap helps you **understand large C codebases** (FreeRTOS, Zephyr, BLE, USB, Ethernet, RTOS kernels, drivers) by building a **call‑graph‑driven code map** and letting you navigate:
- functions
- call relationships
- exact call sites
- multiple implementations of the same symbol

It is designed for **research, reading, and comprehension**, not for building or compiling code.

---

## Why CodeMap exists

Modern IDEs are excellent for editing and debugging, but they are **not optimized for subsystem research**.

When you open an unfamiliar codebase, you usually want to answer questions like:
- Where does execution start?
- Which functions are central hubs?
- Who calls this function?
- Where exactly is this function invoked?
- What are the alternative implementations of this API?

IDEs answer these questions indirectly, file by file.

**CodeMap answers them directly** by turning code into a **navigable map**, not just a collection of files.

---

## What CodeMap does (and does not do)

### CodeMap **does**:
- Parse C source code statically (no build required)
- Extract function definitions
- Extract function call relationships
- Record **exact call sites** (file + line + column)
- Support **multiple definitions per function name**
- Allow interactive navigation with history and bookmarks

### CodeMap **does not**:
- Compile code
- Resolve macros fully
- Apply build configurations
- Guarantee runtime correctness

Ambiguity is treated as a **feature**, not a bug.

---

## High‑level architecture

```
C source files
   ↓
Tree‑sitter C parser
   ↓
Static call graph + call sites
   ↓
JSON index (project snapshot)
   ↓
CodeMap Console Navigator (V3)
```

The console navigator is intentionally **UI‑agnostic** so the same core can later power a PyQt / Qt GUI.

---

## Requirements

- Python 3.9 or later
- Windows / Linux / macOS

Python dependencies:
```
pip install tree_sitter==0.20.4 tree_sitter_languages==1.10.2
```

---

## Step 1: Generate the code map (index)

Run the analyzer on a **folder** containing C code.

Example (FreeRTOS):
```
python analyze_folder_callsites_v2.py C:\path\to\FreeRTOS\Source
```

Example (Zephyr USB):
```
python analyze_folder_callsites_v2.py C:\path\to\zephyr\subsys\usb
```

This generates:
```
_callgraph_callsites.json
```
inside the target folder.

This JSON file is the **CodeMap project snapshot**.

---

## Step 2: Start CodeMap (console)

You can launch CodeMap using either the JSON file **or the folder**.

Recommended (folder‑based):
```
python nav_console_v3.py C:\path\to\zephyr\subsys\usb
```

CodeMap will automatically pick the latest callgraph JSON in the folder.

---

## Startup screen (what you should see)

```
===================================================
 CodeMap – Console Navigator (V3)
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
```

---

## Core navigation workflow

### 1. Search for a function
```
cmd> s
Search substring> xQueue
```

Select a function from the list.

---

### 2. Open its definition
```
cmd> o
```

If multiple definitions exist, CodeMap lets you choose which implementation to view.

---

### 3. Jump to call sites
```
cmd> cs
```

- Choose a callee
- Choose an exact call site
- CodeMap prints a **contextual code snippet with line highlighting**

---

### 4. See who calls this symbol
```
cmd> cb
```

This shows all caller locations across the indexed folder.

---

### 5. Navigate freely

- `b` . go back
- `f` . go forward

This makes exploration safe and non‑linear, which is essential for research.

---

### 6. Bookmark important locations
```
cmd> m
```

Bookmarks help you build a **reading and research plan** while exploring.

List bookmarks:
```
cmd> marks
```

---

### 7. Save a research session
```
cmd> save
```

This writes `session.json` next to the index file.

A session stores:
- current location
- navigation history
- bookmarks

---

## Full command reference

Type at any time:
```
help
```

Commands:
- `s` . search & select function
- `o` . open function definition
- `c` . list callees (unique)
- `cs` . jump to call site
- `cb` . who calls this symbol
- `jd` . jump to definition of a symbol
- `b` . back
- `f` . forward
- `m` . bookmark current view
- `marks` . list bookmarks
- `save` . save session
- `q` . quit

---

## Intended usage (important)

CodeMap is built for:
- subsystem research
- onboarding to large embedded codebases
- architectural understanding
- academic or industrial exploration

It is **not** a replacement for an IDE.

Think of CodeMap as a **code map and navigation companion** that complements your editor.

---

## Repository structure (recommended)

```
codemap/
├─ codemap-core/   # indexing + navigation engine
├─ codemap-cli/    # console navigator
├─ codemap-gui/    # (future) PyQt / Qt GUI
├─ docs/
├─ README.md
├─ requirements.txt
└─ LICENSE
```

All components can live in a **single repository** initially and be split later if needed.

---
## Windows helper (recommended)

This repo includes a one-command runner for Windows.

### Run

```powershell
.\run_codemap.ps1 "C:\path\to\zephyr\subsys\usb"
```   
# Start navigator (folder-based)
python .\codemap-cli\nav_console_v3.py "$Folder"

Run it

From PowerShell:

cd C:\codemap
.\run_codemap.ps1 "C:\path\to\zephyr\subsys\usb"


If PowerShell blocks scripts

Run this once:
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

---

## Open‑source roadmap

### v0.1 (current)
- Static indexer with call sites
- Console navigation
- History + bookmarks + sessions

### v0.2
- Larger context views (`open file`, adjustable context)
- Noise filtering (macros, tracing calls)
- Session load / resume

### v0.3
- Stabilize core APIs
- Clean separation: core vs CLI

### v0.4
- PyQt / Qt GUI using the same core

Graph visualization comes **after** navigation is proven useful.

---

## Feedback requested

If you are using CodeMap, please answer:
1. Where did you feel lost?
2. Which command did you use the most?
3. Did call‑site jumping help?
4. What would save you time daily?

Your feedback directly shapes the next iteration of CodeMap.

---

Happy exploring.

