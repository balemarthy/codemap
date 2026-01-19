## COMMANDS (mental models, not syntax)

Audience: Users who know the basics but want clarity.

### `s` . search & select function

Use when:
- you don’t know where to start
- you want to jump directly to an API

Think:
> “Put me inside this function.”

---

### `c` . list callees (overview)

Shows **what the current function calls**.

Use when:
- understanding responsibility
- judging complexity

Think:
> “What does this function depend on?”

---

### `cs` . jump to call site (evidence)

Shows **exact locations** where calls happen.

Use when:
- behavior depends on conditions
- you need surrounding logic

Think:
> “Show me where this actually happens.”

---

### `cb` . who calls this symbol (context)

Shows **all callers** of the current function.

Use when:
- tracing execution backward
- finding entry points

Think:
> “Who depends on me?”

---

### Navigation helpers

- `o` . open definition
- `b` / `f` . back / forward
- `m` . bookmark current view
- `marks` . list bookmarks
- `save` . save research session
