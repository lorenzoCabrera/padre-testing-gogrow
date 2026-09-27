---
name: system-tests
description: >-
  Writes committed system tests (spec/system/, Capybara) for pis-gogrow from test
  scenarios the user dictates: each block groups one or more historias (IBP id +
  Como/quiero/para + criterios de aceptación) with explicit Pasos and a mandatory
  Esperado. Same rules as integration-tests (unit-test gate, negative/boundary
  cases, transversal permission/consistency checks, TODO(integración) for what
  isn't built, defect files), but the scenario flow comes from the user's Pasos
  instead of being derived. TRIGGER: `/system-tests <bloque> --- <bloque> ...`.
argument-hint: "IBP-075 Como… quiero… para… Criterios: 1… 2… | IBP-076 … | Pasos: … | Esperado: … --- (siguiente bloque)"
---

Same job as `integration-tests`, but the user already designed the scenario. Read
`.claude/skills/integration-tests/SKILL.md` and apply it in full — sync/infra
check, "what's actually there", turning criterios into cases, SimpleCov, Gate 1,
Gate 2, transversal checks, verify, defects, DoD checklist — with only the
differences below. Don't restate those rules here; that file is the authority.

## Input format — show this if it's missing or malformed

If `ARGUMENTS` is empty, or any block breaks the rules below, stop and reply with
this template (plus which block/field is wrong), not a guess:

```
/system-tests
IBP-075 Como <rol> quiero <acción> para <beneficio>.
Criterios:
1. ...
2. ...
IBP-076 Como ... quiero ... para ...
Criterios:
1. ...
Pasos: Ingresar como E1, H1 y P1. Recorrer desde el inicio sus funciones. ...
Esperado: Cada rol ve solo sus funciones; las URL de P2 devuelven acceso denegado. ...
---
IBP-050 Como ... quiero ... para ...
Criterios:
1. ...
Pasos: P1 edita y publica un menú, E1 elige fecha, plato, ... Repetir con plato
agotado y hora límite vencida.
Esperado: ...
```

Rules per block (blocks split on a line that is exactly `---`):

- At least one historia: an `IBP-NNN` id **plus** its Como/quiero/para text **plus**
  its criterios. A bare id list (`IBP´s: 075, 076`) is not enough — ask for the text
  and criterios of each missing one, same as `integration-tests`' Gate 0.
- Exactly one `Pasos:` and one `Esperado:`. **Esperado is mandatory** — if it's
  missing, ask for it; never infer it from the criterios or the current code.
- If a Pasos sentence and an Esperado sentence can't be matched up (e.g. "Repetir con
  plato agotado" but Esperado says nothing about agotado), ask what's expected for
  that variant instead of inventing it.

## Users in Pasos

Aliases are letter + number; the number distinguishes distinct users of the same
role (P1 ≠ P2), each created fresh in the spec:

| Alias | Role in pis-gogrow |
|---|---|
| `E<n>` | Empleado — `Consumer` |
| `P<n>` | Proveedor — `Provider` |
| `A<n>` | Admin — `Admin` |
| `H<n>` | RRHH — **no model/role exists yet**; steps needing it go to `TODO(integración)` until it does. Re-check `User#sync_roles!` each run. |

A user with several roles ("una cuenta que sea Empleado y RRHH") is described in
words in Pasos — build one `User` with each role record. An alias letter not in this
table → ask, don't guess.

## Data

All data is created inside the spec (factories in `spec/factories/`, or fixtures
where the existing spec in that flow already uses them) — never seeds, never the
dev DB. Name variables after the alias (`p1`, `e1`, `p2_menu`) so a failing line
maps back to the Pasos at a glance.

## From Pasos/Esperado to specs

- One `spec/system/<flow>_spec.rb` per block (or per distinct flow if a block clearly
  spans several), with a header comment listing the block's IBP ids.
- Pasos are the happy-path scenario, in the user's order. Each Esperado assertion is
  checked against its real effect (persisted record, other role's view) — not just a
  flash message.
- "Repetir con X" → a separate `scenario` per variant, same setup, one thing changed.
- The Pasos don't replace the rest: still add the negative/boundary cases from the
  criterios and the transversal checks (P2's URLs/files is exactly the peer-to-peer
  check) that `integration-tests` requires.
- If Esperado contradicts a criterio, the criterio wins — test the criterio and write
  the mismatch up as a `Documentación` defect.

## Report

Same content as `integration-tests`' report, plus a table per block
`Paso → Esperado → spec:line → ✅/❌/TODO`, written to
`docs/reports/system-tests/system-tests-<dd-mm-aaaa>.md` in **this repo** (never
inside `pis-gogrow/`), overwritten on same-day reruns. Defects still go to
`docs/reports/defects/`.
