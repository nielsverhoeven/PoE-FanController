# Model Routing Guide

<!-- Last updated: 2026-06-07 -->

This guide decides **which AI model to use for each task type**, ordered from cheapest to most expensive.

---

## Routing Decision Tree

```
Is the answer already in docs/kb/ ?
  YES → read the file, answer directly. No model needed beyond basic reasoning.
  NO  ↓

Is this a simple, mechanical task?
  YES → Local Ollama (free) or cloud Haiku (cheap)
  NO  ↓

Does this require novel reasoning, architecture decisions, or complex code generation?
  YES → Cloud Sonnet (expensive, high quality)
  NO  → Cloud Haiku
```

---

## Task → Model Mapping

### 🟢 Local Ollama (free — run on developer machine)

These tasks do NOT require cloud credits:

| Task | Recommended model | Notes |
|---|---|---|
| YAML / JSON syntax validation | `qwen2.5-coder:7b` | Fast, accurate for structured data |
| Python syntax check | `qwen2.5-coder:7b` | Equivalent to `py_compile` but with context |
| Grep / file search by pattern | `qwen2.5-coder:7b` | Or just use grep directly |
| Simple text formatting / README edits | `qwen2.5-coder:7b` | Very fast |
| Changelog generation from commit list | `qwen2.5-coder:7b` | Templated, no reasoning needed |
| Summarizing a file you've already read | `qwen2.5-coder:7b` | Context already loaded |
| **Git commit message drafts** | `qwen2.5-coder:7b` | Provide diff/description, get conventional commit |
| **Issue/PR summaries** | `qwen2.5-coder:7b` | Draft text to review, not final output |
| Boilerplate code generation (known patterns) | `qwen2.5-coder:7b` | Standard patterns from KB |
| Unit test stubs from function signatures | `qwen2.5-coder:7b` | Deterministic output |
| BOM table formatting / sorting | `qwen2.5-coder:7b` | Structured data |
| KiCad S-expression generation (from KB template) | `qwen2.5-coder:7b` | Use KB template, fill in values |

**How to call Ollama from PowerShell** (always use REST, not CLI — `ollama run` hangs):
```powershell
$body = @{ model = "qwen2.5-coder:7b"; prompt = "YOUR PROMPT"; stream = $false } | ConvertTo-Json
(Invoke-RestMethod http://localhost:11434/api/generate -Method POST -ContentType "application/json" -Body $body).response
```

### 🟡 Cloud Haiku (cheap — ~10× cheaper than Sonnet)

| Task | Notes |
|---|---|
| GitHub API calls (create issue, add comment, create branch) | Simple CRUD, no reasoning needed |
| File search / exploration in unfamiliar codebase | explore agent on Haiku |
| Checking CI status / reading workflow logs | github.action-manager on Haiku |
| Enriching a GitHub issue from a template | Mostly filling in known facts |
| Simple dependency analysis | Low reasoning requirement |
| Reading and summarizing known files | When local model isn't set up |

### 🔴 Cloud Sonnet (expensive — use only when necessary)

| Task | Justification |
|---|---|
| Architecture decisions and validation | Requires deep multi-domain reasoning |
| Constitution amendments | High-stakes, needs careful analysis |
| Novel code generation (new peripheral, new protocol) | Requires reasoning + synthesis |
| Complex bug diagnosis (multiple interacting causes) | Requires hypothesis generation |
| Feature planning for major hardware changes | Multi-domain, many constraints |
| KiCad footprint creation from datasheet | Requires spatial reasoning |
| Reviewing ERC/DRC violations (root cause) | Requires hardware domain knowledge |
| ESP32-P4 RMII pin verification | Safety-critical, verify against TRM |

---

## Sub-Agent Model Override

When calling the `task` tool, use the `model` parameter to override the default:

```
# For cheap GitHub API work:
model: "claude-haiku-4.5"

# For exploration tasks:
model: "claude-haiku-4.5"

# For complex reasoning (default, expensive):
model: "claude-sonnet-4.6"
```

---

## When NOT to Spawn a Sub-Agent

These tasks should be done **directly with tools** — no sub-agent needed at all:

| Task | Direct approach |
|---|---|
| Read a file | `view` tool |
| Search for text | `grep` tool |
| Check if file exists | `glob` or `powershell` |
| Make a small edit | `edit` tool |
| Run a command | `powershell` tool |
| Check git status | `powershell: git status` |
| Validate YAML locally | `powershell: python -c "import yaml..."` |

**The single most expensive habit: spawning a Sonnet sub-agent to do a task
that a direct tool call (view + edit) would complete in 2 steps.**

---

## KB-First Protocol (saves the most credits)

Before spawning any expert agent, check:
1. `docs/kb/kicad-10-reference.md` — KiCad format questions
2. `docs/kb/esp32-p4-reference.md` — ESP32-P4 GPIO, RMII, firmware questions
3. `docs/kb/poe-reference.md` — PoE standards, power budget questions
4. `docs/kb/component-library.md` — MPN, footprint, datasheet questions

If the answer is there → answer directly. Sub-agent cost: **$0**.

If the answer is NOT there → spawn sub-agent, then **add the new fact to the KB**
so future queries are free.

---

## Local Ollama Setup

See `docs/kb/local-ai-setup.md` for installation and configuration instructions.
