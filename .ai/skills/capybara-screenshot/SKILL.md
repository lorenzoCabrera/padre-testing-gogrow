---
name: capybara-screenshot
description: >-
  Shows what a page/dialog in pis-gogrow currently looks like, by driving it through
  Capybara + headless Chrome against the real local stack with a real login — never
  claude-in-chrome or a static mock. TRIGGER when asked "show me what X looks like" or
  "take a screenshot of X" — as opposed to capybara-smoke-check (verifying behaviour) or
  capybara-system-suite (committed regression coverage).
---

Adapted from `feature-screenshot` in the reference project. Same rule carries over
unchanged: **always the real stack through Capybara, never browser automation tooling
that bypasses the actual Rails+Inertia+React render path** — a screenshot of a
hand-mocked page proves nothing about what the app actually renders, including SSR
markup, real serializer props, and real translated strings.

## Prerequisites

Same as `capybara-smoke-check`: `bin/dev` running, `spec/support/capybara.rb` wired
per `capybara-system-suite` if it isn't already.

## Capturing one

A throwaway system spec, same `zz_scratch_` convention as `capybara-smoke-check`,
navigating to the real page with a real signed-in user and real fixture/factory data:

```ruby
# frozen_string_literal: true
# spec/system/zz_scratch_screenshot_spec.rb — delete after use

RSpec.describe "Scratch screenshot" do
  it "captures the menus page" do
    sign_in(users(:one))
    visit menus_path
    page.save_screenshot(Rails.root.join("tmp/screenshots/menus-page.png").to_s)
  end
end
```

```bash
bin/rspec spec/system/zz_scratch_screenshot_spec.rb
rm spec/system/zz_scratch_screenshot_spec.rb
```

Then read `pis-gogrow/tmp/screenshots/menus-page.png` directly to see it.

## Capturing a specific state (a dialog, a validation error, an empty state)

Drive Capybara to that state before calling `save_screenshot` — click through to open a
dialog, submit an invalid form to trigger the error state, sign in as a user with no
records for an empty state. The screenshot is only as representative as the setup that
produced it; don't fabricate the state by editing the DOM or mocking data — use real
fixtures/factories, same as any other spec.

## Full-page vs. viewport

`screen_size: [1400, 1400]` (set in `capybara-system-suite`'s driver config) is a
viewport, not the page — a page taller than that scrolls, and `save_screenshot` only
captures what's rendered in the viewport by default. Scroll or resize before capturing
if the thing being shown is below the fold.
