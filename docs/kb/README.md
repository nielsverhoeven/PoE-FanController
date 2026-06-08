# PoE FanController — Knowledge Base

<!-- Last updated: 2026-06-08 -->

This directory contains **pre-loaded domain facts** for this project. All agents MUST
check here before spawning expert sub-agents or performing web searches. Reading a KB file
costs far less than a sub-agent invocation.

## Files

| File | Contents | Primary consumers |
|---|---|---|
| `ESP32-P4-POE-ETH/board-reference.md` | **Read first for any J8/connector question** — confirmed board dimensions (78×21mm), J8 row spacing (15.38mm, NOT 2.81mm), exact pin positions (row1=2.81mm, row2=18.19mm from edge, first pin 4.67mm from end), EMAC pins, power budget, GPIO pinout, OQ list | implementer, kicad.expert, esp32.expert |
| `kicad-10-reference.md` | KiCad 10 format, ERC/DRC baselines, schematic conventions, pcbnew API, custom footprint generation pattern, DRC baseline (4 silk warnings) | implementer, kicad.expert |
| `esp32-p4-reference.md` | ESP32-P4 RMII fixed pins (MDC=31, MDIO=**52**, RST=**51**), GPIO allocation, PlatformIO config, arduino-esp32 3.x APIs | implementer, esp32.expert |
| `poe-reference.md` | 802.3at class table, power budget for daughter board (≈16.6W at 12V for fans) | implementer, poe.expert |
| `component-library.md` | Current BOM (daughter board v3.1.0): J8, U_BOOST, J2–J5, R3–R8, LED1, NTC1; KiCad footprints | implementer, kicad.expert |
| `model-routing.md` | Decision guide: when to use local Ollama vs cloud Haiku vs cloud Sonnet | all agents, orchestrator |
| `local-ai-setup.md` | Ollama installation + recommended models for this project | developer setup |
| `Sample-PCB-Sketch.png` | User-approved PCB layout sketch: portrait 42×78mm, ESP32 left column, fans right column | implementer, kicad.expert |

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
