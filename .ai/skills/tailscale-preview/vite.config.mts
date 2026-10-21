// Wraps pis-gogrow's own vite.config.ts so the dev server is reachable from the
// tailnet without editing the shared repo. `tailscale serve` terminates TLS on
// :8443 and forwards to localhost:5173, so the page must load assets from there.
import base from "../../../pis-gogrow/vite.config"

const host = process.env.TAILSCALE_HOST

export default (env) => {
  const config = base(env)
  return {
    ...config,
    server: {
      ...config.server,
      allowedHosts: [host],
      cors: { origin: `https://${host}` },
      hmr: { host, protocol: "wss", clientPort: 8443 },
    },
  }
}
