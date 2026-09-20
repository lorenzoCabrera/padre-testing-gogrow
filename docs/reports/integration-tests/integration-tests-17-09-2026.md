# Integration tests — merge del fix de infra — 17-09-2026

**pis-gogrow branch:** `feature/ibp-004-consulta-platos`, mergeada localmente
con `origin/develop` (commit `5f4b5d0`). Nada pusheado todavía.

## Contexto

El 16-09 se habían sacado del working tree el fix de infra en
`authentication_helpers.rb` y la gema SimpleCov (ver
`integration-tests-16-09-2026.md`), porque el fix "ya estaba arreglado en
otra rama" y la gema se iba a agregar después. El 17-09 develop trajo un fix
de login/roles (PR #35, `fix/specs-login-roles`), así que se mergeó a la
rama de la historia y se recrearon los archivos sacados el día anterior.

## Merge de `origin/develop` → `feature/ibp-004-consulta-platos`

Se descartó el cherry-pick de solo 3 commits (el fix de PR #35 depende de
`User#sync_roles!` y del concern `SyncsUserRoles`, introducidos 13 commits
atrás en PR #26 "login-empleado" — no es aislable). Se hizo merge completo,
6 conflictos:

- `spec/support/authentication_helpers.rb` — se combinó la derivación
  automática de rol de develop (`sync_roles!`, `roles.first`) con el fix de
  Selenium que develop todavía no tiene (`page.driver.set_cookie` no existe
  en el driver Selenium; se usa `page.driver.browser.manage.add_cookie`).
- `app/javascript/locales/en.json` / `config/locales/en.yml` — develop los
  borró (español como único idioma). Se aceptó el borrado, pero se migraron
  a mano los strings de "consulta de platos" a `config/locales/es.yml`
  (`nav.menus`, `pages.consumer.menus.*`) para no perder la traducción de
  la historia.
- `app/javascript/routes/index.ts` — generado (Typelizer), nunca se edita a
  mano; se resolvió tomando la versión de develop y regenerando después con
  `bin/rails typelizer:generate:refresh`.
- `spec/fixtures/companies.yml` / `consumers.yml` — conflicto add/add
  (ambas ramas los crearon independientemente); se fusionaron tomando el
  naming de develop (`consumers: one`, no `employee` — sin uso explícito
  por label en el código).

Se recrearon `spec/support/capybara.rb` y
`spec/system/consumer/menus_spec.rb` con el contenido guardado el 16-09.

## Bloqueante encontrado al intentar confirmar los tests

No se pudo correr la suite para confirmar los "2 escenarios en verde" del
system spec. **Todo `bin/rspec` (cualquier archivo) falla en la carga de
fixtures**, con:

```
PG::ForeignKeyViolation: ERROR: insert or update on table "admins" violates
foreign key constraint "fk_rails_e493fcc5fa"
DETAIL: Key (company_id)=(1) is not present in table "companies".
```

**Confirmado que no es nuestro:** se reprodujo corriendo
`bin/rspec spec/requests/sessions_spec.rb` sobre `origin/develop` puro (sin
ningún cambio de esta rama), con la base de test recién creada
(`db:drop db:create db:schema:load`, vía `docker compose exec web`,
Postgres 17). Falla igual, 6 de 6 ejemplos. Bloquea a cualquiera del equipo
que corra tests localmente sobre develop tal cual está, no solo a esta
rama.

**Mecanismo:** `config.global_fixtures = :all` (en `spec/rails_helper.rb`)
carga fixtures de las 6 tablas con archivo en `spec/fixtures/` para
cualquier spec. Rails, al cargar fixtures en Postgres, desactiva TODAS las
FK de la base (no solo las de esas 6 tablas) con un truco directo sobre
`pg_constraint.convalidated`, inserta los datos, y al final revalida TODAS
las FK de toda la base como chequeo de seguridad — ahí explota la de
`admins.company_id → companies.id`, aunque `admins` no tiene fixture propio
y las tablas están vacías al consultarlas después por fuera de esa
transacción.

**Pista, no confirmada del todo:** correr `RAILS_ENV=test bin/rails
db:seed` a mano produce exactamente `Admin(id: 1, company_id: 1,
user_id: 3)` / `Company(id: 1, "GoGrow")` — el mismo shape que se vio la
primera vez que se debuggeó el error (con un `admins.created_at` viejo,
del 14-09). Eso explicaría el dato original: alguien corrió el seed contra
la base de test en algún momento. Pero el mismo error se reproduce incluso
con la base recién limpiada y confirmada vacía antes y después de la
corrida fallida — no se llegó a cerrar el mecanismo exacto de por qué sigue
pasando sin datos de seed de por medio. No hay ningún hook en el código de
la app (`config/`, `lib/tasks/`, `Rakefile`) que dispare `db:seed`
automáticamente.

**Para el equipo:** revisar si algún paso de CI/setup corre `db:seed`
contra la base de test, y si no, tratarlo como bug de infraestructura en el
chequeo de FKs de fixtures (posible relación con el paso a Postgres 17 en
`c4a7bad`, chore/ci-config). Reportado, no arreglado — fuera de alcance de
esta historia.

## Archivos tocados en esta corrida

En `pis-gogrow/` (sobre `feature/ibp-004-consulta-platos`):
```
merge commit 5f4b5d0 (origin/develop → feature/ibp-004-consulta-platos)
 M app/javascript/locales/es.json         # strings de consulta de platos migrados
 M app/javascript/routes/index.ts         # regenerado (Typelizer)
?? spec/support/capybara.rb               # recreado
?? spec/system/consumer/menus_spec.rb     # recreado
```
Nada de esto está pusheado. SimpleCov sigue afuera, como se acordó.
