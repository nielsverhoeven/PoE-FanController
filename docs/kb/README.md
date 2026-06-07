# PoE FanController — Knowledge Base

<!-- Last updated: 2026-06-07 -->

This directory contains **pre-loaded domain facts** for this project. All agents MUST
check here before spawning expert sub-agents or performing web searches. Reading a KB file
costs far less than a sub-agent invocation.

## Files

| File | Contents | Primary consumers |
|---|---|---|
| `kicad-10-reference.md` | KiCad 10 S-expression format, ERC/DRC rules, known-good patterns | implementer, kicad.expert |
| `esp32-p4-reference.md` | ESP32-P4 RMII fixed pins, GPIO allocation, PlatformIO config, arduino-esp32 3.x APIs | implementer, esp32.expert |
| `poe-reference.md` | 802.3af/at/bt class table, Ag9905M specs, power budget, EMC rules | implementer, poe.expert |
| `component-library.md` | All project MPNs, KiCad footprints, key datasheet facts | implementer, kicad.expert |
| `model-routing.md` | Decision guide: when to use local Ollama vs cloud Haiku vs cloud Sonnet | all agents, orchestrator |
| `local-ai-setup.md` | Ollama installation + recommended models for this project | developer setup |

## KB-First Rule

Before calling any expert sub-agent, ask: "Is this fact already in the KB?"

- **YES** → read the KB file and use the answer directly. No sub-agent needed.
- **UNCERTAIN** → read the KB file first; spawn sub-agent only if the KB doesn't cover it.
- **NO** → spawn the sub-agent, then **add the new fact to the KB** so the next invocation is free.

After any expert consultation that adds a new fact, the **implementer or architect must
update the relevant KB file** and commit it to the feature branch.

## Update Protocol

When a verified fact is newly established (e.g., RMII pin confirmed against TRM):
1. Add it to the relevant KB file under the appropriate heading.
2. Commit the update with message: `docs(kb): add <fact> from <source>`
3. The fact is now permanently available to all future agent invocations at zero cost.
