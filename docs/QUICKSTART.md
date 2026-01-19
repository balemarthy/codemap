## QUICKSTART (10 minutes to first win)

Audience: Research associates who want to start using CodeMap immediately.

### Prerequisites
- Python 3.9+
- PowerShell (Windows)

### Step 1: Clone the repo

```powershell
git clone <repo-url>
cd codemap
```

### Step 2: Run CodeMap (one command)

```powershell
.\run_codemap.ps1 "C:\path\to\target\source\folder"
```

This will:
1. Install dependencies
2. Build / refresh the code index
3. Launch the CodeMap console

---

### Step 3: First successful navigation

Inside CodeMap:

```
s        # search function
pick one
c        # see what it calls
cs       # jump to a callsite
b        # go back
cb       # see who calls it
q        # quit
```

If you can do this once, you’re set.
