# padre-testing-gogrow

Repo orquestador personal alrededor de [`pis-gogrow`](https://github.com/PIS-GoGrow/pis-gogrow)
(clonado adentro, con su propio git). Acá viven los skills de testing y revisión
para Claude Code, OpenCode y otros agentes (`.ai/skills/`, ver `AGENTS.md`); los reportes van a `docs/reports/` de **este** repo, nunca a
`pis-gogrow/`. Detalle en `CLAUDE.md` y `docs/runbook.md`. `docs/reports/` está en
`.gitignore`: los informes quedan solo en tu disco.

```bash
scripts/setup.sh            # clona pis-gogrow si falta
cd pis-gogrow && bin/setup
```

Abrir el agente en la raíz de este repo para que los comandos estén disponibles:

- **Claude Code:** lee `.claude/skills` (symlink a `.ai/skills`) y `CLAUDE.md`.
- **OpenCode:** `opencode.json` carga `AGENTS.md`, los skills y define los cinco comandos.
- **Otros (Codex, Cursor, Aider…):** leen `AGENTS.md`; sin slash commands, pedir
  "corré system-tests con: <bloques>" y el agente sigue `.ai/skills/system-tests/SKILL.md`.

## Comandos de testing de historias

`/integration-tests`, `/system-tests` y `/regression-tests` escriben specs
**commiteables** en `pis-gogrow/spec/system/` (Capybara + Chrome headless) y
comparten las mismas reglas:

- `pis-gogrow` tiene que estar en `develop` actualizado y limpio; si no, frenan y preguntan.
- Antes de escribir tests de sistema, listan los tests unitarios faltantes y
  **preguntan** antes de crearlos.
- Además del camino feliz: casos negativos por campo, límites (N y N+1), permisos
  (otro rol / otro usuario del mismo rol por URL directa) y consistencia entre vistas.
- Lo que la historia pide pero la app todavía no tiene queda como comentario
  `# TODO(integración): falta … Historia: IBP-NNN "…"` en el spec — no se saltea en silencio.
- Cada bug encontrado va a su propio archivo `docs/reports/defects/DEFECT-<slug>-<dd-mm-aaaa>.md`.
- Nunca commitean dentro de `pis-gogrow/`; eso es un paso aparte y manual.

### `/integration-tests` — tests a partir de la historia

Deduce los escenarios desde los criterios de aceptación. Usar cuando una historia
se mergea a `develop`.

```
/integration-tests IBP-066 Como proveedor quiero … para …
Criterios:
1. …
2. …
---
IBP-067 Como … quiero … para …
Criterios:
1. …
```

- Historias separadas por una línea con solo `---`.
- Necesita el **texto** de la historia y sus criterios; con solo un ID o nombre de
  rama, lo pide.
- Informe: `docs/reports/integration-tests/integration-tests-<dd-mm-aaaa>.md`.

### `/system-tests` — tests a partir de Pasos y Esperado

Igual que `/integration-tests`, pero el escenario lo dictás vos: cada bloque agrupa
una o más historias con sus **Pasos** y el resultado **Esperado**.

```
/system-tests
IBP-075 Como … quiero … para …
Criterios:
1. …
IBP-076 Como … quiero … para …
Criterios:
1. …
Pasos: Ingresar como E1, H1 y P1. Recorrer desde el inicio sus funciones. Probar URL y archivos ajenos de P2.
Esperado: Cada rol ve solo sus funciones; las URL de P2 devuelven acceso denegado.
---
IBP-050 Como … quiero … para …
Criterios:
1. …
Pasos: P1 edita y publica un menú, E1 elige fecha, plato, … confirma. Repetir con plato agotado y hora límite vencida.
Esperado: … ; con plato agotado … ; con hora límite vencida …
```

- Por bloque: al menos una historia completa (IBP + texto + criterios), un `Pasos:`
  y un `Esperado:`. **Esperado es obligatorio**; si falta (o falta para un
  "Repetir con X"), lo pide.
- Usuarios por alias (letra + número; P1 y P2 son usuarios distintos). Los datos se
  crean dentro del spec:

  | Alias | Rol |
  |---|---|
  | `E<n>` | Empleado (Consumer) |
  | `P<n>` | Proveedor (Provider) |
  | `A<n>` | Admin |
  | `H<n>` | RRHH — todavía no existe en la app, queda como `TODO(integración)` |

- Cada "Repetir con X" es un escenario aparte. Si el Esperado contradice un criterio,
  manda el criterio y la diferencia se registra como defecto.
- Sin argumentos, o con un bloque mal armado, muestra la plantilla.
- Informe: `docs/reports/system-tests/system-tests-<dd-mm-aaaa>.md`, con tabla
  Paso → Esperado → spec → ✅/❌/TODO.

### `/regression-tests` — que las historias queden protegidas y estables

Misma entrada que `/system-tests` (historias + **Pasos** + **Esperado** por
bloque, con la misma plantilla y los mismos alias), pero parte de los tests que
**ya existen**: el objetivo es que cada historia quede cubierta por tests que
existan y sean estables, no escribir tests nuevos.

```
/regression-tests
IBP-003 Como … quiero … para …
Criterios:
1. …
IBP-004 Como … quiero … para …
Criterios:
1. …
Pasos: P1 publica un menú para el martes, E1 elige el martes y consulta los platos. Repetir con un día sin menú.
Esperado: E1 ve solo los platos del martes con sus datos; el día sin menú muestra el estado vacío.
```

1. **Inventario:** cada Paso, Esperado y criterio se mapea al test que ya lo
   protege (`archivo:línea`). Lo cubierto se referencia, no se duplica.
2. **Huecos:** escribe solo lo que falta, en el archivo del flujo que ya existe
   (no hay carpeta aparte de regresión). Lo no construido queda como `TODO(integración)`.
3. **Estabilidad:** el conjunto se corre simulando los 7 días de la semana, fin de
   mes y 31/12, y los tests de sistema 5 veces seguidas. Si uno falla por el test,
   lo arregla tocando solo `spec/` (si es de un compañero, lo marca aparte); si
   falla por la app, registra el defecto y no deja el test en la suite.
4. **Comparación** con el informe anterior de las mismas historias: primero lo que
   antes pasaba y ahora no.

- Informe: `docs/reports/regression-tests/regression-tests-<dd-mm-aaaa>.md`, con
  tablas Paso → Esperado → test → estado y criterio → test → estado
  (✅ estable, 🔧 estabilizado, ➕ nuevo, TODO, 🐞 defecto), la estabilidad por
  archivo y el comando para volver a correr el conjunto.

### `/pending-tests` — qué TODOs ya se pueden testear

Busca los `TODO(integración)` que dejaron corridas anteriores y verifica contra el
código actual de `develop` si lo que faltaba ya está implementado. **No escribe
tests**: te dice cuáles se pueden crear y te pide las historias para correr
`/integration-tests`.

```
/pending-tests                        # todo spec/
/pending-tests spec/system/consumer   # acotado a una carpeta
```

Responde en el chat (sin archivo de informe), agrupado por historia:

- ✅ **Ya se puede testear** — con la referencia `archivo:línea` de lo que se implementó.
- 🟡 **Parcial** — qué falta todavía.
- ⏳ **Sigue pendiente**.
- 🐞 **Era un defecto** — si el `DEFECT-*.md` asociado parece corregido.

Si hay alguno ✅/🟡, lista los IBPs que necesita y deja la plantilla de
`/integration-tests` para completar con el texto y los criterios.

### Flujo típico

1. Se mergea una historia a `develop` → `/integration-tests` (o `/system-tests` si
   ya tenés los pasos armados).
2. Revisar el informe y los `DEFECT-*.md`; commitear los specs en `pis-gogrow` a mano.
3. Cada tanto, tras nuevos merges → `/pending-tests` → pasarle las historias que
   pide a `/integration-tests`.
4. Para asegurar historias ya mergeadas → `/regression-tests` con sus Pasos y
   Esperado; repetirlo con las mismas historias muestra si algo dejó de andar.

## `/code-review` — revisar el PR de otro

```
/code-review feature/IBP-060-cambio-validar-comprobante
/code-review 85
/code-review fix/persistir-carrito --base main
```

- Revisa **solo lo que agrega la rama** contra su base (la del PR, o `develop`):
  `git diff origin/<base>...origin/<rama>`. Lo que ya estaba no se reporta.
- Junta `rails-code-reviewer`, `rails-security-reviewer` y `rails-database-reviewer`,
  más bugs de lógica y tests faltantes. Corre rubocop/eslint/tsc/brakeman sobre los
  archivos cambiados en un worktree temporal: tu checkout de `pis-gogrow` no se toca.
- Informe: `docs/reports/code-review/PR_REVIEW_<rama>_<aaaa-mm-dd>.md`, con
  🔴/🟡/🟢 y veredicto. No comenta en GitHub salvo que se lo pidas.

## Otros skills

Testing: `rspec-developer`, `vitest-rtl-developer`, `capybara-smoke-check`,
`capybara-system-suite`, `capybara-screenshot`. Revisión: `rails-code-reviewer`,
`rails-security-reviewer`, `rails-database-reviewer`, `rails-quality-metrics`.
Cuándo usar cada uno: `docs/runbook.md`.
