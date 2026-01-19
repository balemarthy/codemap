## RESEARCH WORKFLOW (how to study a subsystem)

Audience: Engineers doing deep subsystem research (USB / BLE / Ethernet).

### Step 1: Find entry points

- Search for public APIs
- Bookmark 2–3 functions that feel like starting points

```
s
m
```

---

### Step 2: Identify hubs

For each entry point:
- run `c`
- note functions with many callees
- jump into them

Bookmark important hubs.

---

### Step 3: Follow execution paths

Use this loop:

```
c → cs → read → b → cs → read
```

Avoid reading files top-to-bottom.
Follow **control flow**, not file structure.

---

### Step 4: Use bookmarks as a study map

Bookmarks are not favorites. They are **waypoints**.

Typical bookmarks:
- entry point
- scheduler interaction
- ISR boundary
- driver handoff
- confusing logic

---

### Step 5: Save and share sessions

At the end of a session:

```
save
```

Share:
- `session.json`
- 3 bullet points:
  - what you understood
  - where you got stuck
  - one improvement suggestion

This turns CodeMap into a **collaborative research tool**.
