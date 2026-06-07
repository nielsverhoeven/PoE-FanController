# Local AI Setup — Ollama

<!-- Last updated: 2026-06-07 -->

Run AI models locally to eliminate cloud credit costs for small, mechanical tasks.

---

## 1. Install Ollama (Windows)

```powershell
# Option A: Download installer
# https://ollama.com/download/windows

# Option B: winget
winget install Ollama.Ollama

# Verify install
ollama --version
```

Ollama runs a local API server on `http://localhost:11434` (OpenAI-compatible format).

---

## 2. Recommended Models for This Project

Pull these models once; they're cached locally for free reuse:

```powershell
# Fast model for simple tasks (2B params, <2 GB RAM)
ollama pull llama3.2:3b

# Code-focused model for KiCad/Python/C++ generation (7B params, ~5 GB RAM)
ollama pull qwen2.5-coder:7b

# Higher quality code model for complex patterns (14B params, ~9 GB RAM)
ollama pull qwen2.5-coder:14b

# Optional: general reasoning at medium quality (8B params, ~5 GB RAM)
ollama pull llama3.1:8b
```

**Minimum hardware recommendation:** 16 GB RAM, 8 GB GPU VRAM (RTX 3060 or better).
CPU-only inference works but is 5-10× slower.

---

## 3. Use Cases for This Project

### Validate KiCad S-expression syntax
```powershell
$sch = Get-Content hardware/kicad/PoE-FanController.kicad_sch -Raw
# Check balanced parentheses
$open = ($sch -split '\(' ).Count - 1
$close = ($sch -split '\)').Count - 1
Write-Host "Open: $open  Close: $close  Match: $($open -eq $close)"
```
> Often simpler to just count parens directly — no model needed.

### Generate boilerplate from KB template
```powershell
$prompt = @"
Using this KiCad 10 global_label template from our KB:
$(Get-Content docs/kb/kicad-10-reference.md -Raw)

Generate a global_label for signal EMAC_RXD0 at position (100 50 0), shape=output.
"@

ollama run qwen2.5-coder:7b $prompt
```

### Validate platformio.ini structure
```powershell
$content = Get-Content firmware/platformio.ini -Raw
ollama run qwen2.5-coder:7b "Is this valid PlatformIO INI? List any errors: $content"
```

### Generate unit test stubs
```powershell
$header = Get-Content firmware/src/fan_control.h -Raw
ollama run qwen2.5-coder:14b "Write Unity test stubs for all public functions in: $header"
```

---

## 4. OpenAI-Compatible API (for tool integration)

Ollama exposes an OpenAI-compatible REST API:

```bash
# Test the API
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-coder:7b",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

This means any tool that accepts an OpenAI endpoint can point to `http://localhost:11434/v1`
with API key `ollama` (any non-empty string).

---

## 5. When to Stay on Cloud

Use local Ollama for:
- ✅ Generating boilerplate from templates
- ✅ Syntax/format validation
- ✅ Simple code patterns (known APIs from KB)
- ✅ Text summarization and formatting

Stay on cloud Sonnet for:
- ❌ Architecture decisions
- ❌ Novel problem solving
- ❌ Multi-file codebase reasoning
- ❌ Safety-critical verification (RMII pins, isolation rules)

See `docs/kb/model-routing.md` for the full routing guide.

---

## 6. Checking Ollama Status

```powershell
# Is Ollama running?
Invoke-WebRequest http://localhost:11434 -ErrorAction SilentlyContinue | Select-Object StatusCode

# List downloaded models
ollama list

# Start Ollama if not running (it auto-starts on Windows as a service)
Start-Process ollama serve
```
