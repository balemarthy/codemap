# CodeMap

**Map your code. Understand the system.**

CodeMap is a lightweight **Source Insight style** tool for exploring large C codebases (FreeRTOS, Zephyr, drivers, BLE, USB, Ethernet, RTOS kernels) by building a **static call graph with call sites**, then letting you browse it in:

- **GUI** (PySide6) . constellation view (1-hop callers and callees), clickable navigation
- **CLI** . console navigation with search, history, bookmarks, call-site jumps

CodeMap is for **research and comprehension**, not for building or compiling code.

---

## What CodeMap does (and does not do)

### CodeMap does
- Parse C source statically (no build required)
- Extract function definitions
- Extract call relationships
- Record **exact call sites** (file + line + column)
- Let you navigate callers and callees quickly
- Support non-linear exploration via “go deep by clicking”

### CodeMap does not
- Compile code
- Resolve build configs and macros fully
- Guarantee runtime correctness

Ambiguity is treated as a feature.

---

## Repository layout

```
codemap/
├─ codemap-cli/        # console navigator
├─ codemap-indexer/    # indexer that generates callgraph + callsites
├─ codemap-gui/        # PySide6 GUI
├─ docs/
├─ requirements.txt
├─ run_codemap.ps1
└─ README.md
```

---

## Requirements

- Python 3.9+ (Windows, Linux, macOS)
- Dependencies:
  - tree_sitter==0.20.4
  - tree_sitter_languages==1.10.2
  - PySide6 (GUI)

Install (recommended in a venv):

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install PySide6
```

If your `requirements.txt` already includes PySide6, the last line is not needed.

---

# Quick start. GUI (PySide6)

The GUI is the best way to “see the system” fast.

## Step 1. Run the GUI

From repo root:

```powershell
python .\codemap-gui\app.py
```

Alternative (if you prefer running inside the folder):

```powershell
cd .\codemap-gui
python .\app.py
```

## Step 2. Open a code folder

In the GUI:

1. Click **Open Folder**
2. Select the root folder of the code you want to analyze  
   Example: `FreeRTOS/Source` or `zephyr/subsys/usb`

What happens next:

- CodeMap creates a workspace folder inside your selected project:
  ```
  <your-folder>/.codemap/
  ```
- CodeMap runs the indexer automatically using that selected folder path
- The generated index JSON is stored in:
  ```
  <your-folder>/.codemap/_callgraph_callsites.json
  ```

So you do not need to manually generate or browse for JSON files.

## Step 3. Use the GUI effectively

### Layout
- **Left top**: Files
- **Left bottom**: Outline (symbols in selected file)
- **Center**: Constellation view (1-hop map)
- **Right**: Tabs
  - Callers
  - Callees
  - Call Sites

### Constellation controls
- **Click a node** to make it the new center (go deep step by step)
- **Hover a node** to highlight it (and reduce visual noise)
- **Mouse wheel** zoom
- **Drag** to pan (hand drag)
- **Fit** button to auto-fit to current graph
- **Zoom slider** for controlled zoom

### Navigation flow (recommended)
1. Pick a file on the left
2. Pick a function in Outline
3. See callers and callees in the constellation
4. Click a caller or callee node to go deeper
5. Use Back / Forward to return and explore alternative paths

---

# Quick start. CLI (Console Navigator)

The CLI remains available and unchanged. Use it when you want fast keyboard-driven navigation.

## Step 1. Generate index (manual CLI way)

Run the analyzer on a folder containing C code:

```powershell
python .\codemap-indexer\analyze_folder_callsites.py "C:\path\to\FreeRTOS\Source"
```

This creates a callgraph JSON (depending on version, names may differ), commonly:

- `_callgraph_callsites.json`
- or `_callgraph.json` (intermediate or alternate output)

## Step 2. Start the console navigator

Recommended folder-based mode:

```powershell
python .\codemap-cli\nav_console_v3.py "C:\path\to\zephyr\subsys\usb"
```

---

## Windows helper script (CLI convenience)

This repo includes a one-command runner for Windows:

```powershell
.\run_codemap.ps1 "C:\path\to\zephyr\subsys\usb"
```

If PowerShell blocks scripts, run once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

---

## Generated files (important)

When you open a folder in the GUI, CodeMap creates:

```
<your-project>/.codemap/
```

This folder is project-local and should NOT be committed.

Recommended `.gitignore` entries:

```
.venv/
**/.codemap/
**/_callgraph*.json
```

---

## Roadmap

### v0 (current)
- Indexer produces call sites JSON
- GUI constellation view (1-hop), clickable go-deep navigation
- CLI navigator remains available

### Next
- Open definition and show code snippet in GUI
- Click a callsite and jump to file + line
- Filtering and decluttering (hide macros, test hooks, tracing noise)
- Session save and restore in GUI

---

## Feedback requested

If you use CodeMap, answer these:
1. Where did you feel lost?
2. What helped you understand faster. constellation, call sites, or file outline?
3. What would you want as the next “killer feature”. open definition, jump to callsite, or filtering?

Happy exploring.

