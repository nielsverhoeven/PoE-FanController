# Architecture Validation: PCB Layout — Place All External Connectors on One Board Edge

**Feature:** `pcb-connector-edge`
**GitHub Issue:** #1
**Plan file:** `docs/features/pcb-connector-edge/plan.md`
**Validated against:** `docs/constitution.md` v1.0.1
**Validation date:** 2026-06-06
**Validator:** architect agent

---

## Result

> **APPROVED WITH CHANGES**
>
> The plan is architecturally sound and consistent with all hardware, isolation, and process
> principles in the constitution. One PATCH amendment to `docs/constitution.md` is required before
> implementation begins: P-HW-03 must be updated to formally document J7's right-edge exception
> (amendment applied in this commit — see constitution v1.0.1). Two advisory notes are recorded
> below; neither is a blocking issue.

---

## 1. Principle-by-Principle Findings

### 1.1 Hardware Layer Rules

| Principle | Finding | Status |
|---|---|---|
| **P-HW-01** (2-layer FR4) | Plan adds no layers; all changes are placement and routing only. | ✅ Pass |
| **P-HW-02** (F.Cu placement only) | All connector footprints (J1–J7) are assigned to F.Cu. B.Cu reserved for traces and copper pours. Enforced by DRC courtyard check (Step 8 / AC-3). | ✅ Pass |
| **P-HW-03** (single board-edge rule) | J1, J2–J5, J6 all placed on top edge (y ≈ 5 mm). J7 placed on right edge — now a formally documented exception in P-HW-03 v1.0.1. Amendment applied before implementation. | ✅ Pass (post-amendment) |
| **P-HW-04** (fixed 90×70 mm outline) | No Edge.Cuts changes. The isolation slot (Step 7) is an interior routed feature; it does not modify the board outline. | ✅ Pass |
| **P-HW-05** (generator is schematic source of truth) | This is a PCB layout task only. `generate_project.py` is not modified. | ✅ Pass (N/A) |
| **P-HW-06** (grid discipline) | All proposed X centres land on 0.1 mm grid or finer per P-HW-06. Footprint Y depth must be verified in KiCad footprint editor before placement (noted in plan §4.5). | ✅ Pass |
| **P-HW-07** (track/via standards) | No track widths defined in this plan (connector placement only). Track assignments deferred to routing phase; plan correctly scopes this out. | ✅ Pass (N/A) |
| **P-HW-08** (ground pour split at x=38 mm) | Plan confirms existing pour zones start at x=40 mm (2 mm buffer). Isolation slot reinforces the barrier. No pour changes introduced. | ✅ Pass |

### 1.2 Isolation Barrier Rules (P-ISO-01 through P-ISO-05) — CRITICAL

All five isolation principles are evaluated against the plan's proposed X positions.

#### J1 RJ45 (primary side)
- Centre x = 20.0 mm; right copper edge ≈ 30.65 mm
- Distance to barrier (x=38 mm): **38.0 − 30.65 = 7.35 mm** — exceeds 3.0 mm minimum by 4.35 mm

#### J2 fan header (nearest secondary-side connector to barrier)
- Centre x = 46.1 mm; left copper edge ≈ 41.0 mm (courtyard boundary)
- Distance to barrier: **41.0 − 38.0 = 3.0 mm** — exactly at the P-ISO-03 minimum

| Principle | Calculation | Status |
|---|---|---|
| **P-ISO-01** (≥1.5 kV isolation) | Ag9905M provides the isolation barrier; no PCB trace bridges primary/secondary. J1 copper stops at 30.65 mm. No new primary-side components introduced. | ✅ Pass |
| **P-ISO-02** (no copper crosses x=38 mm) | J1 rightmost copper: 30.65 mm < 38 mm ✓. J2 leftmost copper: ≥41.0 mm > 38 mm ✓. Isolation slot at x=38 mm (Step 7) further enforces the barrier. | ✅ Pass |
| **P-ISO-03** (≥3.0 mm creepage/clearance) | Primary side: 7.35 mm gap ✓ (comfortable margin). Secondary side: exactly 3.0 mm gap ⚠️ — see Advisory Note 1 below. | ✅ Pass ⚠️ Note 1 |
| **P-ISO-04** (PCB slot at barrier) | Specified in Step 7: 1.0 mm wide routed slot, x=38 mm, y=10 mm to y=70 mm. | ✅ Pass |
| **P-ISO-05** (no secondary signals cross barrier) | All secondary connectors (J2–J7) at x > 38 mm. No GPIO, power, or signal trace crosses the barrier. J7 is within secondary domain (right edge). | ✅ Pass |

### 1.3 PoE & Power Standards

| Principle | Finding | Status |
|---|---|---|
| **P-POE-01** (802.3at Class 4) | No change to PoE operating class. J1 placement does not affect PD negotiation. | ✅ Pass (N/A) |
| **P-POE-02** (no primary-side design changes) | J1 is repositioned (layout), not redesigned. No new primary-side components added. U1 Ag9905M is unchanged. | ✅ Pass |

### 1.4 BOM Integrity (§2.2 BOM Lock)

| Component | Constitution entry | Plan decision | Status |
|---|---|---|---|
| J1 | Würth 615008144521 | Repositioned; same MPN and footprint | ✅ Pass |
| J2–J5 | Molex 47053-1000 / `PinHeader_1x04_P2.54mm_Vertical` | Vertical headers retained (Option A). Right-angle substitution explicitly deferred to future amendment. | ✅ Pass |
| J6 | GCT USB4085-GF-A | Repositioned; same MPN and footprint | ✅ Pass |
| J7 | No locked MPN (not in §2.2) | Right-angle 3-pin 2.54 mm header acceptable per plan §6 Step 6. No §2.2 constraint applies. | ✅ Pass |

### 1.5 Firmware Architecture

This feature has **zero firmware impact**. Connector edge assignment does not change any GPIO allocation, peripheral ownership, PWM configuration, or module boundary. All P-FW-01 through P-FW-05 principles are unaffected.

### 1.6 KiCad File Format Standards

| Principle | Finding | Status |
|---|---|---|
| **P-KI-01** (KiCad 10.0.3 exclusively) | Plan Steps 3–9 explicitly require KiCad 10.0.3. | ✅ Pass |
| **P-KI-04** (generator is schematic source of truth) | `generate_project.py` is not modified (no new components, no net changes). PCB layout only. | ✅ Pass |
| **P-KI-05** (in-project symbols/footprints) | All footprints referenced are standard KiCad library entries; no external library paths needed. | ✅ Pass |
| **P-KI-06** (Gerbers in `hardware/gerbers/`) | Step 9 regenerates Gerbers to the specified directory and commits them. | ✅ Pass |

### 1.7 Testing Standards

| Principle | How the plan addresses it | Status |
|---|---|---|
| **P-TEST-01** (zero ERC before layout) | Step 2 gates all PCB work on a confirmed zero-ERC schematic. | ✅ Pass |
| **P-TEST-03** (zero DRC after layout) | Step 8 requires DRC to pass with zero errors and zero unconnected nets, including the 3.0 mm isolation barrier rule. | ✅ Pass |
| **P-TEST-04** (DRC before Gerber export) | Step 8 strictly precedes Step 9 in the implementation sequence. | ✅ Pass |
| **P-TEST-05/06** (firmware unit tests) | No firmware changes; not applicable. | ✅ Pass (N/A) |

### 1.8 Development Agreements

| Principle | Finding | Status |
|---|---|---|
| **P-DEV-01** (commit convention) | Plan §10 specifies `hw:` prefix for all commits. | ✅ Pass |
| **P-DEV-02** (ERC/DRC gate for hardware PRs) | PR must include updated `erc_output.json` + DRC report as merge preconditions. | ✅ Pass |
| **P-DEV-03** (no direct commits to `main`) | All changes via pull request. | ✅ Pass |
| **P-DEV-04** (constitution amendments require documentation) | J7 right-edge exception → PATCH amendment applied to P-HW-03 (v1.0.1) before implementation. | ✅ Pass |

---

## 2. J7 Right-Edge Exception — Constitutional Ruling

**Claimed in plan (§4.6, §8):** J7 is not named in P-HW-03's parenthetical list `(J1, J2–J5, J6)`,
therefore no amendment is needed.

**Architect ruling:** The plan's interpretation is legally defensible, but relying solely on J7's
omission from a parenthetical is insufficient per P-DEV-04, which requires a documented amendment
for *any* deviation from the constitution, however small. The right-edge placement of J7 is a
deviation from the spirit of P-HW-03 ("all external connectors on one edge") and must be
formally memorialised.

**Disposition:** A PATCH amendment (v1.0.0 → v1.0.1) has been applied to P-HW-03 in
`docs/constitution.md` to explicitly name J7 as the sole documented exception to the
single-edge rule, with the following rationale on record:

1. J7 is a development-only debug UART convenience connector; it is not panel-mounted, user-facing,
   or present on production labels.
2. J7 has no locked MPN (§2.2 does not list it); it carries no BOM-amendment risk.
3. J7 physically cannot fit on the top-edge secondary rail: the 53.5 mm secondary rail is
   fully consumed by J2–J5 + J6 (51.64 mm used, 1.86 mm margin), leaving a 5.76 mm shortfall
   for J7's 7.62 mm body width.
4. J7 is entirely within the secondary (SELV) domain (x > 38 mm); its right-edge position
   introduces no isolation risk.

---

## 3. Advisory Notes (Non-Blocking)

### Note 1 — J2 barrier clearance is at the P-ISO-03 minimum with zero margin

The plan places J2's left courtyard edge at x = 41.0 mm, giving exactly 3.0 mm copper clearance
to the isolation barrier at x = 38.0 mm. This is compliant with P-ISO-03 but leaves no margin for:

- Footprint courtyard definitions that may extend slightly beyond the stated body width
- Through-hole annular ring expansion if a larger drill is used
- Manufacturing tolerance on component placement (typically ±0.1 mm for THT)

**Recommendation for hardware designer:** When placing J2 in KiCad, verify that the left edge of
the annular ring of J2 pin 1 (not the courtyard boundary) is ≥ 41.0 mm. If the annular ring
infringes on the 41.0 mm limit, shift J2 right by 0.5 mm (new centre x = 46.6 mm) and cascade
J3–J5 right by the same amount. The plan's §4.4 shows 1.86 mm total margin on the secondary rail —
sufficient to absorb a 0.5 mm rightward shift of all five secondary connectors without any
connector exiting the board boundary. The DRC isolation barrier rule (Step 8) is the definitive
gate; this note is a pre-emptive heads-up.

### Note 2 — Inter-courtyard gap between fan headers (J2–J5) is tight

Plan §4.4 specifies 0.5 mm inter-courtyard gaps between adjacent fan headers. Plan Risk R3
acknowledges that KiCad DRC may flag this. The 0.5 mm gap is within accepted courtyard clearance
norms for vertical THT headers assembled from above, but it is advisable to:

1. Confirm KiCad's courtyard clearance DRC rule is set to ≤ 0.5 mm (not the default 0.25 mm
   which would pass, but some setups use 0.5 mm minimum courtyard gap which would fail).
2. If DRC flags a courtyard collision, widen gaps to 1.0 mm: the 1.86 mm secondary-rail margin
   accommodates three additional 0.5 mm gaps (3 × 0.5 = 1.5 mm) without pushing J6 into the
   board wall.

---

## 4. Proposed X Positions — Verification Summary

| Ref | X centre (mm) | Left copper edge (mm) | Right copper edge (mm) | Distance to barrier (mm) | P-ISO-03 | P-HW-03 edge |
|-----|-------------|----------------------|----------------------|--------------------------|----------|-------------|
| J1 | 20.0 | 9.35 | 30.65 | 7.35 (primary side) | ✅ >3.0 | Top |
| J2 | 46.1 | ~41.0 | ~51.2 | 3.0 (secondary side) | ✅ =3.0 ⚠️ | Top |
| J3 | 56.8 | ~51.7 | ~61.9 | 13.7 | ✅ | Top |
| J4 | 67.4 | ~62.3 | ~72.5 | 24.3 | ✅ | Top |
| J5 | 78.1 | ~73.0 | ~83.2 | 35.0 | ✅ | Top |
| J6 | 88.1 | ~83.6 | ~92.6 | 45.6 | ✅ | Top |
| J7 | x≈94.5 (right edge) | — | x=95.0 (board wall) | >38 mm from barrier | ✅ | Right (exception) |

Board right wall: x = 95 mm. J6 right copper edge 92.6 mm → 2.4 mm board-edge clearance ✅ (> 0.5 mm minimum).

---

## 5. Acceptance Criteria Sign-Off (Pre-implementation)

The following acceptance criteria from plan §7 are architecturally pre-approved:

| # | Criterion | Pre-approval basis |
|---|---|---|
| AC-1 | J1, J2–J5, J6 on top edge | Coordinates verified in §4 of this document |
| AC-2 | J7 only exception to top-edge rule | P-HW-03 amended (v1.0.1); exception documented |
| AC-3 | All footprints on F.Cu | P-HW-02; DRC gate (Step 8) |
| AC-4 | J1 copper ≤ 35 mm; J2 copper ≥ 41 mm | Verified by calculation; DRC barrier rule gates it |
| AC-5 | Zero DRC errors / zero unconnected nets | Step 8 is a merge-blocking gate (P-DEV-02) |
| AC-6 | Isolation slot at x=38 mm | Step 7 specified; P-ISO-04 |
| AC-7 | J6 right courtyard ≤ x=92.7 mm | 92.6 mm per plan §4.4 ✅ |
| AC-8 | bom.csv retains Molex 47053-1000 | §2.2 BOM lock enforced |
| AC-9 | DESIGN.md updated | Steps 1 and 10; P-DEV-01 |
| AC-10 | J7 at right edge, secondary domain, documented | Constitution v1.0.1 P-HW-03 amendment |
| AC-11 | Gerbers regenerated and committed | Step 9; P-KI-06 |

---

## 6. Final Sign-Off

| Item | Value |
|---|---|
| **Overall result** | ✅ APPROVED WITH CHANGES |
| **Blocking issues** | None — amendment applied before implementation |
| **Constitution amendment** | v1.0.0 → v1.0.1 (PATCH): P-HW-03 J7 right-edge exception documented |
| **Advisory notes** | 2 (non-blocking): J2 barrier margin, inter-header courtyard gap |
| **Hardware expert consultation** | Not required — amendment is a clarification of existing scoped language, not a new hardware technology choice |
| **PoE expert consultation** | Not required — no change to power architecture or isolation design |
| **Implementation may proceed** | ✅ Yes, after this document and the constitution amendment are committed |
