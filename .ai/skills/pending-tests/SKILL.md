---
name: pending-tests
description: >-
  Scans pis-gogrow's specs for `TODO(integración)` comments left by earlier
  integration-tests/system-tests runs, re-checks against the current develop
  whether what each one was waiting on is now implemented, and tells the user which
  ones can be turned into real tests — asking for the historia text + criterios so
  they can run `/integration-tests` with it. Read-only: writes no specs itself.
  TRIGGER: `/pending-tests`, "qué TODOs ya se pueden testear", typically after a
  batch of historias merges to develop.
argument-hint: "(sin argumentos) — o una carpeta/archivo para acotar, ej. spec/system/consumer"
---

Finds deferred coverage that is now unblocked and hands it back to the tester. It
does **not** write specs or delete TODOs — that's `/integration-tests`' job once the
tester supplies the historia (its Gate 2 already says a finished TODO becomes a real
spec, not both).

## 1. Sync first

Same as `integration-tests`: `pis-gogrow` must be on an up-to-date, clean `develop`
(`git status`, `git log -1` vs `origin/develop`). On a feature branch, behind, or
dirty → say so and ask before continuing; "is it implemented now?" is meaningless
against the wrong checkout.

## 2. Collect the TODOs

`grep -rn -A15 "TODO(integración)" spec/` (or the path in `ARGUMENTS`). Each TODO is
the whole contiguous comment block, not just the first line — read until the
comment ends. From each one extract: file:line, what's missing ("falta
implementar/corregir …"), the scenario it blocks, and the historia reference
(`IBP-NNN` if present, otherwise the quoted `Historia: "…"` summary). Also note the
spec file it sits in: its existing scenarios show which flow and roles it belongs to.

## 3. Re-check each one against the code — read, don't pattern-match

Apply `integration-tests`' "what's actually there" rules to *the specific missing
piece* the TODO names: routes, controller action (not an empty stub), model
column/association, frontend page/handler actually wired. Classify:

- **✅ Ya se puede testear** — every piece the TODO names is wired end to end.
- **🟡 Parcial** — some pieces landed; name exactly what's still missing.
- **⏳ Sigue pendiente** — nothing relevant changed.
- **🐞 Era un defecto** — the TODO says "falta corregir" (a bug, not missing work):
  check `docs/reports/defects/` in this repo for the matching `DEFECT-*.md` and say
  whether the bug looks fixed now. Don't edit the defect file.

Cite `file:line` evidence for every ✅ and 🟡 — "the controller now has X" with no
reference is a guess.

## 4. Notify

Reply in chat (no report file), grouped by historia:

```
## Se pueden crear ahora
- IBP-066 (o "Historia: …") — spec/system/provider/hora_limite_pedidos_spec.rb:3
  Faltaba: visualizador del tiempo restante. Ahora: app/javascript/pages/…:42
  Escenario a cubrir: …

## Parciales
- … — falta todavía: …

## Siguen pendientes
- … (una línea cada uno)
```

Then, only if there's at least one ✅/🟡, close with exactly:

> Para crear estos tests necesito el texto de cada historia y sus criterios de
> aceptación. Pasámelos con:
>
> ```
> /integration-tests IBP-066 Como … quiero … para …
> Criterios:
> 1. …
> ---
> IBP-0NN …
> ```

List the IBPs (or historia summaries) that need text, so the tester knows exactly
which ones to paste. Never reconstruct the historia or its criterios from the TODO
comment or the code — the TODO is a summary, not the acceptance criteria.
