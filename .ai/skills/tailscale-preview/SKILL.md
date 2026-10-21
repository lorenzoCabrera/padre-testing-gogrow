---
name: tailscale-preview
description: >-
  Publishes the pis-gogrow dev app of the current branch on the user's private
  tailnet (tailscale serve, never funnel) so they can open it from their phone,
  and takes it down again. TRIGGER: `/tailscale-preview` or `/tailscale-preview
  subir`, "publicá la app en tailscale", "quiero verla desde el celular";
  `/tailscale-preview bajar`, "bajá la app de tailscale".
---

Two actions: **subir** (default when no argument) and **bajar**. Nothing in
`pis-gogrow/` is edited: everything the tailnet needs lives in this skill's
folder and in the `pis-gogrow-tailscale` entry of `.claude/launch.json`.

## How it fits together

- `tailscale serve` terminates HTTPS with the machine's tailnet cert:
  `:443 → localhost:3001` (Rails) and `:8443 → localhost:5173` (Vite).
  Only devices in the user's tailnet reach it. **Never use `tailscale funnel`**,
  which would put the dev app on the public internet.
- Rails blocks unknown hosts, so the launch entry passes
  `RAILS_DEVELOPMENT_HOSTS=<host>`. It must be the full host: Rails' `.ts.net`
  form only allows one subdomain level and the host has two.
- pis-gogrow's `vite.config.ts` pins `hmr.host: "localhost"`, and
  rails-vite-plugin builds the asset URL from it, so the phone would ask its
  own localhost. `vite.config.mts` here wraps the project config and swaps in
  the tailnet host (`wss`, port 8443), its `allowedHosts` and CORS origin.
  `Procfile` runs Rails and Vite with that config, from inside `pis-gogrow/`.
- SSR goes through the same URL, so it only works while Tailscale is up; if it
  fails the page still renders client-side.

## subir

1. `tailscale status`. If it says *stopped*, run `tailscale up`. If that asks
   for root, stop and ask the user to run once, in their own terminal:
   `sudo tailscale set --operator=$USER` and then `tailscale up`. Never try
   sudo yourself.
2. Read the host:
   `tailscale status --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))'`.
   If it differs from `H=` in the `pis-gogrow-tailscale` entry of
   `.claude/launch.json`, update it there.
3. Free port 3001: `preview_list`, and `preview_stop` a running `pis-gogrow`
   entry. Then check `pis-gogrow/tmp/pids/server.pid` and
   `pis-gogrow/tmp/rails-vite.json`: Docker leaves them owned by root. If the
   pid in `server.pid` is not a running Rails process, `rm -f` both (no sudo
   needed, `tmp/` is the user's).
4. `preview_start` with name `pis-gogrow-tailscale`. If it fails, read the
   output and fix the cause; don't fall back to another entry.
5. Publish:
   ```bash
   tailscale serve --bg 3001
   tailscale serve --bg --https=8443 5173
   ```
6. Verify from this machine (it is on the tailnet too):
   `curl -s -o /dev/null -w "%{http_code}" https://<host>/` must be 200, and
   `https://<host>:8443/@vite/client` must be 200. Check `preview_logs` for
   `SSR render failed` or `Blocked hosts`. Don't judge it from the built-in
   browser pane: it blocks the `:8443` assets as another origin
   (`ERR_BLOCKED_BY_CLIENT`) and shows the page unstyled. For a visual check
   use `google-chrome --headless=new --window-size=390,844
   --virtual-time-budget=15000 --screenshot=<scratchpad>/celular.png <url>`.
7. Tell the user: the URL `https://<host>/`, the branch it shows
   (`git -C pis-gogrow branch --show-current`), and that Google sign-in does
   not work there (its OAuth redirect is localhost only): they need the dev
   login form (`DEV_LOGIN_ENABLED=true` in `pis-gogrow/.env`). Don't read
   `.env` to check, the hook blocks it; ask.

Switching branches while it is up needs no republish: Vite reloads, but after
a branch with new migrations run `bin/rails db:migrate` (see the runbook's
gotchas). Restart the preview if Ruby files under `config/` changed.

## bajar

1. `tailscale serve reset` (removes both ports).
2. `preview_stop` the `pis-gogrow-tailscale` server.
3. Confirm with `tailscale serve status` that nothing is served. Leave
   Tailscale itself up; the user uses it for other things.
