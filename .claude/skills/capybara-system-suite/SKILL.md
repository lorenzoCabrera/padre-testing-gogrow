---
name: capybara-system-suite
description: >-
  The maintained, committed browser-regression suite for pis-gogrow — RSpec system specs
  under spec/system/, driven by Capybara + Selenium headless Chrome against the real
  Rails+Vite app (no separate deployment needed, unlike a k8s-backed E2E setup). TRIGGER
  when asked to add committed browser coverage for a user flow, or fix a flaky/failing
  system spec. For a throwaway one-off check, use capybara-smoke-check instead; for pure
  visual capture, use capybara-screenshot.
---

Adapted from `e2e-suite` in the reference project — but simpler, because the reason
that project split "ad-hoc" from "committed against a real cluster" from "mocked" (a
Kafka hostname that only resolves inside a k8s cluster) doesn't exist here. This is a
Rails monolith: Capybara drives headless Chrome straight against the Rack test app, no
deployment step, no separate CI wiring — `bin/rspec` / `bin/ci` already run
`spec/system/` for free as part of the whole `spec/` tree.

## First-time setup — `spec/system/` doesn't exist yet

Neither does any Capybara/Selenium driver config, despite both gems already sitting in
`Gemfile`'s `group :test`. Add `spec/support/capybara.rb`:

```ruby
# frozen_string_literal: true

RSpec.configure do |config|
  config.before(:each, type: :system) do
    driven_by :selenium, using: :headless_chrome, screen_size: [ 1400, 1400 ]
  end
end
```

Every page here is a React app mounted by Inertia — there is no plain-HTML fallback to
fall back to `rack_test` for. Default every system spec to the JS-capable driver;
don't special-case a "simple" page onto `rack_test`, it won't render at all.

Needs a local Chrome/Chromium binary (Selenium Manager fetches the matching driver
automatically, but not the browser itself) — if `bin/rspec spec/system` fails to launch
a browser, that's the first thing to check, not a code problem.

`.rspec` in this repo only auto-requires `spec_helper`, not `rails_helper` — every
spec file needs its own `require "rails_helper"` at the top (like `spec/requests/`
already does), or the file loads with no Rails/Capybara integration at all and fails
confusingly (`fixtures` undefined, app constants like `User` unresolved).

## Where specs live and how they're found

`spec/system/<flow>_spec.rb`, one file per user-facing flow (not per controller —
`spec/requests/` already covers the controller boundary; system specs are for things
that only show up when the browser actually runs, like a client-side validation message
or a multi-step form). `config.infer_spec_type_from_file_location!` means files here get
`type: :system` automatically — no need to pass `type:` explicitly, unlike the existing
`type: :request` convention in `spec/requests/`.

## Auth

Use the `System` module's `sign_in(user)` / `sign_out` from
`spec/support/authentication_helpers.rb` — do not reuse the `Request` module's
version, it targets a different layer and silently does nothing in a browser-driven
spec.

**Known bug, check before first use:** as committed, `System#sign_in` calls
`page.driver.set_cookie(...)`, a method that only exists on the `rack_test` driver.
This project's own `spec/support/capybara.rb` always drives `type: :system` specs
with `:selenium, using: :headless_chrome` (see above — every page is React, there's
no plain-HTML fallback), and `Capybara::Selenium::Driver` has no `set_cookie` —
every system spec fails immediately with `NoMethodError` until this is fixed. Correct
version (needs a page loaded first, so the browser has a domain to attach the cookie
to):

```ruby
module System
  def sign_in(user)
    session = user.sessions.create!(role: AuthenticationHelpers.role_for(user))
    visit "/"
    page.driver.browser.manage.add_cookie(
      name: "session_token",
      value: AuthenticationHelpers.signed_cookie(:session_token, session.id)
    )
  end

  def sign_out
    page.driver.browser.manage.delete_cookie("session_token")
  end
end
```

If `spec/support/authentication_helpers.rb` still has the broken version, fix it
there before writing any system spec — don't work around it per-spec.

## Writing a spec

```ruby
# frozen_string_literal: true

require "rails_helper"

RSpec.describe "Creating a menu" do
  it "shows the new menu in the list" do
    sign_in(users(:one))
    visit menus_path
    click_on "New menu"
    fill_in "Name", with: "Lunch"
    click_on "Save"
    expect(page).to have_content("Lunch")
  end
end
```

Capybara's matchers (`have_content`, `have_selector`, `click_on`) already retry until
`Capybara.default_max_wait_time` — never add a manual `sleep`; a spec that needs one is
usually asserting on the wrong thing (missing an `expect` that would've waited).

Prefer role/label-based finders (`fill_in "Name"`, `click_on "Save"`,
`find_by_id`/`find("[data-testid=...]")` only as a last resort) — same principle as
`vitest-rtl-developer`'s component tests: assert on what a user perceives, not on markup
structure.

## Running

`spec/system/` runs automatically inside `bin/rspec` and `bin/ci` — no separate flag or
pipeline step, unlike a suite that needs its own deployed environment. Target it alone
while iterating: `bin/rspec spec/system`.
