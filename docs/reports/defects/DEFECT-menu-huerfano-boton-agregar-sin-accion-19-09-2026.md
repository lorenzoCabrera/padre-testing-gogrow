# Registro del defecto

**Título:**
En `/menus` ("Menú del día" de IBP-003), el botón "Agregar" de cada plato no
realiza ninguna acción — la página nunca quedó conectada al flujo de pedido y
convive sin uso con `/dashboard`, que sí implementa el pedido.

**Tipo:**
Funcional.

**Historia o requisito relacionado:**
IBP-003 ("consultar menú disponible por fecha") es la historia dueña de esta
pantalla (`Consumer::MenusController` + `pages/consumer/menus/index.tsx`).
Detectado durante el análisis de integración de IBP-006 ("realizar pedido
empleado"), que construyó el flujo de pedido real en una pantalla distinta
(`/dashboard`) sin dar de baja ni terminar de cablear esta.

**Criterio de aceptación afectado:**
No se dispone del texto original de los criterios de aceptación de IBP-003.
El defecto se redacta contra el comportamiento esperado de cualquier control
interactivo visible y habilitado (debe producir un efecto al activarse) y
contra IBP-006, criterio 1 ("el empleado puede seleccionar una fecha y
visualizar en un mismo lugar los platos publicados por todos los proveedores
habilitados"): en `/menus` la visualización se cumple, pero la "selección"
del plato (paso previo obligatorio para poder reservarlo) no tiene ningún
efecto.

**Severidad:**
Media. No bloquea la historia IBP-006 (que se resuelve íntegramente por
`/dashboard`, verificado con tests automatizados), pero es una ruta real,
alcanzable en `develop`, que responde con una interfaz completa y sin ningún
error visible al usuario ni al desarrollador — el empleado puede creer que
agregó un plato a su pedido cuando no ocurrió nada.

**Entorno o versión:**
`pis-gogrow`, rama `develop`, commit `7454e63` (18-09-2026) — el defecto ya
está presente ahí, no es exclusivo de una rama en desarrollo. También
verificado en `feature/IBP-006-realizar-pedido-empleado`, commit `c647df5`.
Entorno local de desarrollo (Rails 8.1 + Vite), ruta `GET /menus`.

**Precondiciones:**
- Un usuario con rol `consumer` (empleado) con sesión iniciada.
- Al menos un `Schedule` (plato publicado) vigente para la fecha por
  defecto que muestra la página (hoy).

**Pasos para reproducir:**
1. Iniciar sesión como empleado.
2. Navegar directamente a `/menus` (no hay ningún link a esta ruta desde la
   navegación de la app — hay que tipear la URL).
3. Con al menos un plato disponible visible (no agotado, no de una fecha
   pasada), hacer clic en el botón "+" ("Agregar `<nombre del plato>`") de
   ese plato.

**Resultado esperado:**
Alguna reacción visible: que se abra un detalle del plato, se agregue a un
carrito, se muestre una cantidad seleccionada, o como mínimo que la página
redirija al flujo de pedido real (`/dashboard`). Cualquier UI que sea "la
pantalla para elegir qué pedir" debe permitir, en algún paso siguiente,
efectivamente pedir.

**Resultado obtenido:**
No pasa nada. El botón no tiene `onClick`/`onSelect` cableado — en
`app/javascript/pages/consumer/menus/index.tsx:152-162`, `<MenuItem>` se
renderiza sin la prop `onSelect` que el componente sí soporta y usa
(`app/javascript/components/consumer/menus/menu-item.tsx:23,60`, y sí está
cableada en la otra pantalla:
`app/javascript/pages/consumer/dashboard/weekly-menu.tsx:135`,
`onSelect={() => openDetail(item)}`). No hay carrito, ni navegación, ni
mensaje de ningún tipo: el clic se pierde en silencio.

**Evidencia:**
- `app/javascript/pages/consumer/menus/index.tsx:152-162` — `<MenuItem>` sin
  `onSelect`.
- `app/javascript/components/consumer/menus/menu-item.tsx:23,56-60` — el
  botón depende de la prop `onSelect`; si no se pasa, `onClick={undefined}`.
- `app/javascript/components/app-sidebar.tsx:56-62` (rama `develop`) — el
  único ítem de navegación del rol `consumer` ("Menú del día") apunta a
  `consumerDashboard.index().url`, nunca a `consumerMenus.index().url` — no
  hay forma de llegar a `/menus` navegando la app.
- `app/controllers/home_controller.rb:6-7` — el redirect de la home para un
  consumer autenticado va a `dashboard_path`, no a `menus_path`.
- `config/routes.rb:41` — la ruta `GET /menus` (`consumer#menus#index`) sigue
  viva y responde 200; solo es inalcanzable desde la navegación, no desde la
  URL directa.

**Ubicación o artefacto:**
Página `Menú del día` en `/menus` (`Consumer::MenusController#index` /
`app/javascript/pages/consumer/menus/index.tsx`), componente
`app/javascript/components/consumer/menus/menu-item.tsx`.
