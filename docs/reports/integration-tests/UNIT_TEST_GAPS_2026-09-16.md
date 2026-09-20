# Unit test gaps blocked on frontend test tooling

**Generated:** 2026-09-16
**Historia:** consulta de platos disponibles (rama `feature/ibp-004-consulta-platos`, commit `930a690`)
**Motivo:** el equipo decidió no instalar Vitest + React Testing Library todavía —
requiere alineación del equipo antes de sumarlo al stack. Este documento junta lo que
queda pendiente para retomar cuando esa decisión se tome.

## Backend

Sin gaps para esta historia. `app/controllers/consumer/menus_controller.rb`,
`app/models/menu.rb`, `app/models/schedule.rb`, `app/models/provider.rb` y los
serializers de `Consumer::Menu*`/`Schedule` ya están al 100% de líneas cubiertas por
`spec/requests/consumer/menus_spec.rb` (medido con SimpleCov, recién instalado en este
mismo trabajo — ver más abajo).

## Frontend — bloqueado por falta de Vitest + RTL

El repo no tiene Vitest ni React Testing Library instalados (`package.json` no
tiene script `test`, no hay ningún `*.test.tsx` en `app/javascript`). Hasta que se
instale:

- **`app/javascript/components/menus/available-menu-card.tsx`** — componente
  presentacional (leaf component, alcance de `vitest-rtl-developer`, no de
  `capybara-system-suite`) con lógica real sin cobertura:
  - Formato de precio (`Intl.NumberFormat` en `es-UY`/`UYU`).
  - Formato de fecha en UTC (`Intl.DateTimeFormat`, comentario en el propio código
    explica por qué UTC: SSR y browser deben coincidir).
  - Renderizado condicional: `provider_name` presente/ausente, `description`
    presente/ausente, `showLink` true/false.
  - Pluralización de "cupos" vía `t("pages.consumer.menus.spots", { count })`.

No hay otros componentes propios de esta historia con lógica no trivial —
`index.tsx` y `show.tsx` son páginas Inertia (list/empty-state, passthrough), fuera
del alcance de Vitest per el propio `vitest-rtl-developer` (les corresponde
`capybara-system-suite`, ver los specs de integración de esta misma historia).

## Qué falta para desbloquear

1. Decisión del equipo: sumar `vitest`, `@testing-library/react`,
   `@testing-library/jest-dom` (o equivalentes) a `package.json`, un config mínimo de
   Vitest (integrado con la config de Vite existente) y un script `npm test`.
2. Una vez instalado: escribir el spec de `AvailableMenuCard` de arriba.
3. A futuro: cualquier otro componente presentacional con lógica (no solo de esta
   historia) queda en la misma situación hasta que la herramienta exista — este no es
   un gap exclusivo de "consulta platos", es un gap de infraestructura del repo.
