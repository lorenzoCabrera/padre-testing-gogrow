# Integration tests — realizar pedido empleado (IBP-006) — 19-09-2026

**pis-gogrow branch:** `feature/IBP-006-realizar-pedido-empleado`, commit
`c647df5`. **No mergeada a `develop`** (19 commits por delante de
`origin/develop`) — se corrió el análisis contra esta rama por pedido
explícito del usuario, no contra `develop` como haría el flujo estándar de
esta skill (que asume "recién mergeada"). Working tree limpio al arrancar.

## Historia analizada

> Como EMPLEADO, quiero realizar un pedido seleccionando un plato disponible
> para reservar mi comida.

Criterios de aceptación:

1. El empleado puede seleccionar una fecha y visualizar en un mismo lugar los
   platos publicados por todos los proveedores habilitados.
2. Solo se muestran opciones correspondientes a la fecha seleccionada.
3. Los platos agotados o no disponibles se identifican claramente y no pueden
   pedirse.
4. Si no existe un menú publicado para la fecha, se muestra un estado vacío
   informativo.

## Hallazgo previo: dos implementaciones de "ver el menú", solo una vinculada

Existen dos rutas/páginas que muestran platos por fecha:

- **`/menus`** (`Consumer::MenusController` + `pages/consumer/menus/index.tsx`):
  viene de una historia anterior y distinta (IBP-003, "consultar menú
  disponible por fecha"), mergeada a esta rama como dependencia. Tiene
  selector de fecha, filtro de proveedores y estado vacío, pero el botón
  "Agregar" no tiene `onSelect` cableado — no arma carrito ni pide nada.
  **No está en el nav** (`app-sidebar.tsx`) ni es el destino del redirect de
  `HomeController` para consumers.
- **`/dashboard`** (`Consumer::DashboardController` +
  `pages/consumer/dashboard/index.tsx`): es lo que esta historia (IBP-006)
  construyó encima de lo anterior — mismo patrón de selector de fecha +
  filtro de proveedores, pero con detalle de plato, carrito y confirmación
  real contra `Consumer::OrdersController#create`. Es el único destino del
  nav ("Menú del día") y del redirect de la home para consumers.

El análisis y los tests de esta skill apuntan a `/dashboard`, que es el flujo
real que un empleado usa hoy para "realizar un pedido". `/menus` queda
señalado como código huérfano (ver "Otros hallazgos" abajo), no como gap de
esta historia — sus líneas sin cobertura no se le atribuyen a IBP-006.

## Fix de infra (bug conocido, no parte de la historia)

`spec/support/authentication_helpers.rb`'s `System#sign_in` todavía llamaba
`page.driver.set_cookie(...)`, método que no existe en el driver Selenium que
usa este proyecto para `type: :system` — cualquier system spec fallaba con
`NoMethodError`. Corregido a `page.driver.browser.manage.add_cookie` (con
`visit "/"` antes, para que el navegador tenga un dominio al que atar la
cookie), preservando la lógica de resolución de rol ya existente
(`sync_roles!` + `roles.first`).

## Otros fixes de infra (setup de primera vez, no existían en esta rama)

- `spec/support/capybara.rb` no existía: se agregó el driver Selenium
  headless Chrome para `type: :system`.
- `Capybara.enable_aria_label = true`: viene en `false` por defecto en
  Capybara 3.40, y los botones solo-ícono de esta app (ej. el "+" para
  agregar un plato) dependen enteramente de `aria-label`, sin texto visible.
  Sin esto, ningún finder por rol/label los encuentra — se habría repetido en
  cada system spec futuro que toque uno de estos botones.
- SimpleCov no estaba instalado: se agregó el gem (`group :development,
  :test`) y `require "simplecov"; SimpleCov.start "rails"` como primeras
  líneas de `spec/spec_helper.rb`, y `coverage/` a `.gitignore` (tampoco
  estaba). Esto es lo que permitió basar el gap list en líneas realmente sin
  cubrir en vez de en lectura de código.
- Vitest + React Testing Library tampoco estaban instalados: primer uso de
  `vitest-rtl-developer` en este repo. `vitest.config.ts`,
  `app/javascript/test/setup.ts`, scripts `test`/`test:watch` en
  `package.json`. Dos ajustes que la plantilla de la skill no cubre tal cual
  para este repo:
  - `afterEach(cleanup)` en `test/setup.ts`: sin `globals: true` en
    `vitest.config.ts` (que la skill tampoco pide), React Testing Library no
    limpia el DOM entre tests del mismo archivo — el 2º y 3er test del
    archivo nuevo fallaban por encontrar múltiples botones (el render del
    test anterior seguía montado).
  - `@types/node` no estaba instalado — sin eso, `vitest.config.ts` (que usa
    `node:path` para el alias `@/*`, igual que el propio `vite.config.ts` del
    repo) rompía el lint tipado (`no-unsafe-*`). Se agregó como
    devDependency.
  - `tsconfig.node.json` solo incluía `vite.config.ts`; se agregó
    `vitest.config.ts` a su `include` por la misma razón (si no, ESLint no
    puede resolver el archivo para type-checking).

## Gate 1 — tests unitarios (aprobados por el usuario)

**Backend:** no hizo falta escribir nada. Corrí `spec/models/schedule_spec.rb`,
`spec/models/order_spec.rb` (stub `pending`, sin ejemplos propios),
`spec/requests/orders_spec.rb` y `spec/requests/consumer_dashboard_spec.rb`
bajo SimpleCov — las líneas de `Schedule#remaining_amount`,
`Schedule#available?` y `Order.reserve` que sostienen el criterio 3 (agotado
= no se puede pedir) ya están 100% cubiertas indirectamente por los request
specs existentes, pese a que `order_spec.rb` esté vacío. Las únicas 2 líneas
sin cubrir en `consumer/dashboard_controller.rb` (serialización de reviews
del menú; el fallback `"Entrega"` de `delivery_label`, inalcanzable con las
validaciones actuales de dirección) no son parte de los criterios de esta
historia — no se tocaron.

**Frontend:** `app/javascript/components/consumer/menus/menu-item.test.tsx` —
`MenuItem` es el componente presentacional que implementa el criterio 3:
deshabilita el botón "Agregar" y muestra la etiqueta "Agotado" cuando
`soldOut`, y también deshabilita cuando `isPast`. 3 casos: selecciona un
plato disponible (dispara `onSelect`), bloquea uno agotado (badge visible +
botón disabled + `onSelect` no se llama), bloquea uno de una fecha pasada.

```
npx vitest run
 Test Files  1 passed (1)
      Tests  3 passed (3)
```

## Gate 2 — integration tests

Todo lo que implica la historia está realmente cableado end-to-end en
`/dashboard`, así que no hizo falta ningún comentario `TODO(integración)` —
los 4 criterios más el flujo de reserva en sí se escribieron como specs
reales.

`spec/system/consumer/realizar_pedido_spec.rb` (5 escenarios, un solo
archivo por ser el mismo flujo):

1. **AC1** — muestra en un mismo lugar los platos de dos proveedores
   distintos para la fecha elegida.
2. **AC2** — al cambiar de día en el selector semanal, solo se ven los
   platos de ese día (no los del día anterior).
3. **AC3** — un plato con `amount: 0` se marca "Agotado" y su botón de
   agregar queda `disabled`.
4. **AC4** — sin ningún schedule publicado para la semana, se ve el estado
   vacío "Todavía no hay viandas publicadas para este día."
5. **Camino feliz** — seleccionar un plato disponible, confirmar el pedido y
   llegar a "¡Pedido recibido!" crea un `Order`.

Nota de diseño del spec: el driver Selenium corre en un proceso de Chrome
real con su propio reloj — `travel_to` congela solo el proceso de Rails, no
afecta el `new Date()` del navegador. El chequeo `isPast` del lado del
cliente usa ese reloj real. Por eso la fecha congelada (`2026-09-21`, un
lunes) está en el futuro respecto a la fecha real de hoy (`2026-09-19`,
sábado) — así ninguno de los días de esa semana laboral aparece como "pasado"
para el navegador. Congelar a una fecha pasada habría marcado todos los
platos como no disponibles y roto los asserts de "camino feliz"/"agotado" de
forma confusa.

```
bin/rspec spec/system/consumer/realizar_pedido_spec.rb
5 examples, 0 failures
```

Suite completa (`bin/rspec`) después de todos los cambios: **146 examples, 0
failures, 48 pending** (los pending son stubs generados preexistentes, no
relacionados con esta historia). Cobertura de línea total: 83.59%.

## Otros hallazgos (no arreglados, fuera del alcance de esta corrida)

- `/menus` (`Consumer::MenusController` + `pages/consumer/menus/index.tsx`)
  quedó huérfano tras esta historia: ruta viva, controller y página
  funcionando, pero sin link en el nav y sin acción de pedido cableada
  (`MenuItem` se renderiza sin `onSelect`). Vale la pena que el equipo
  decida si se borra o se termina de cablear — hoy es código muerto desde la
  navegación real de la app.

## Archivos tocados

En `pis-gogrow/` (rama `feature/IBP-006-realizar-pedido-empleado`):

- `spec/support/authentication_helpers.rb` — fix del bug conocido de
  `sign_in` en Selenium.
- `spec/support/capybara.rb` — nuevo, setup del driver Selenium +
  `Capybara.enable_aria_label = true`.
- `Gemfile` / `Gemfile.lock` — agregado `simplecov`.
- `spec/spec_helper.rb` — arranque de SimpleCov.
- `.gitignore` — agregado `/coverage/`.
- `spec/system/consumer/realizar_pedido_spec.rb` — nuevo, los 5 escenarios
  de esta historia.
- `vitest.config.ts` — nuevo, setup de Vitest.
- `app/javascript/test/setup.ts` — nuevo, `jest-dom` + `afterEach(cleanup)`.
- `tsconfig.node.json` — agregado `vitest.config.ts` a `include`.
- `package.json` / `package-lock.json` — agregados vitest, jsdom,
  `@testing-library/*`, `@types/node`, scripts `test`/`test:watch`.
- `app/javascript/components/consumer/menus/menu-item.test.tsx` — nuevo,
  test unitario de `MenuItem`.
