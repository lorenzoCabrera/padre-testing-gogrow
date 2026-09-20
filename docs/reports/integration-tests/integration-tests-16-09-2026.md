# Integration tests run — 16-09-2026

**pis-gogrow branch:** `feature/ibp-004-consulta-platos` (commit `930a690`) — no
mergeada a `develop` (15 commits detrás); se procedió sobre esta rama a pedido
explícito, tratando su propio commit como la historia.

## Historia: consulta de platos disponibles

**Unit tests**
- Backend: ninguno necesario — `Consumer::MenusController`, `Menu`, `Schedule`,
  `Provider` y sus serializers ya están al 100% de líneas cubiertas por
  `spec/requests/consumer/menus_spec.rb` (medido con SimpleCov).
- Frontend: gap real en `AvailableMenuCard` (formato de precio/fecha, renderizado
  condicional, pluralización de cupos) — **declinado por el usuario** por ahora,
  pendiente de decisión del equipo sobre instalar Vitest + RTL. Detalle completo en
  `docs/reports/integration-tests/UNIT_TEST_GAPS_2026-09-16.md`.

**Integration tests — escritos**
- `spec/system/consumer/menus_spec.rb` (2 escenarios, ambos verdes):
  - Lista los platos disponibles ordenados por fecha, excluye los no disponibles, y
    navega al detalle de uno.
  - Muestra el estado vacío cuando no hay platos disponibles.

**Deferred:** ninguno — index y show están completamente implementados de punta a
punta, no había nada parcial que comentar con `TODO(integración)`.

**Infra fix aplicado (bloqueaba escribir cualquier system spec):**
- `spec/support/authentication_helpers.rb` — `System#sign_in` usaba
  `page.driver.set_cookie` (no existe en el driver Selenium headless Chrome) y no
  pasaba `role:` (esta misma rama volvió `Session.role` `NOT NULL`). Se arregló para
  usar `page.driver.browser.manage.add_cookie` y aceptar `role:`, igual que
  `Request#sign_in`.
- Primer uso de SimpleCov y de `spec/system/` en el repo: se agregó el gem, el
  require en `spec_helper.rb`, y `spec/support/capybara.rb` (config del driver) —
  ninguno de los dos existía.

**Bug de app encontrado, no arreglado (fuera de alcance de esta historia):**
`SessionsController#create` (`app/controllers/sessions_controller.rb:14`) crea la
sesión sin `role:`; como `role` es `NOT NULL` sin default, **el login por
email/contraseña está roto en esta rama** (`PG::NotNullViolation`, confirmado con
`git stash` que es preexistente a este trabajo). Rompe 19 specs no relacionados con
esta historia al correr la suite completa. Reportado, no arreglado.

## Archivos tocados en esta corrida

En `pis-gogrow/` (`git status --short`):
```
 M .gitignore                            # agrega /coverage
 M Gemfile                               # agrega gem simplecov
 M Gemfile.lock
 M spec/spec_helper.rb                   # require simplecov
 M spec/support/authentication_helpers.rb # fix System#sign_in
?? spec/support/capybara.rb              # nuevo — config driver system specs
?? spec/system/consumer/menus_spec.rb    # nuevo — los 2 escenarios de arriba
```

En `padre-testing-gogrow/` (este repo):
```
docs/reports/integration-tests/UNIT_TEST_GAPS_2026-09-16.md   # nuevo
docs/reports/integration-tests/integration-tests-16-09-2026.md # este archivo
```

Nada de esto está commiteado todavía en ninguno de los dos repos.
