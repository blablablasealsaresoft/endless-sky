# Atlantean Production Deployment Assets

These assets package the Atlantean Sovereignty backend into a repeatable
Docker Compose deployment. They complement the standalone CLI documented in
[`docs/atlantean/production.md`](../../docs/atlantean/production.md) and assume
the repository root is the Compose build context.

## Quick start

1. Copy `.env.example` to `.env` and review the defaults.
2. Populate API/admin keys. The service accepts comma-separated keys via the
   environment variables in `.env`, or you can mount newline-delimited files in
   `secrets/` for long-form secrets storage.
3. If you use key files, create `ops/atlantean/secrets/api_keys.txt` and
   `ops/atlantean/secrets/admin_keys.txt` with one token per line. Empty files are
   treated as no keys.
4. Launch the stack:

   ```bash
   docker compose -f ops/atlantean/docker-compose.yml up -d --build
   ```

5. The service listens on `http://localhost:${ATLANTEAN_PORT}` (default `8080`).
   Logs stream via `docker compose logs -f atlantean-service`.

The Compose file builds `ops/atlantean/Dockerfile`, mounts a named volume at
`/data` for SQLite durability, and forwards environment variables into the
container so the server picks up API keys, admin keys, and other settings.

## Maintenance tips

- Rotate API or admin keys by updating `.env` or the mounted secrets files, then
  run `docker compose up -d` to recreate the container.
- Run one-off maintenance tasks (e.g., `--init-only`) by overriding the
  `ATLANTEAN_INIT_ONLY` environment variable when invoking Compose:

  ```bash
  ATLANTEAN_INIT_ONLY=true docker compose -f ops/atlantean/docker-compose.yml run --rm atlantean-service
  ```

- Back up the persistent volume with `docker run --rm -v atlantean_data:/data`
  style commands or via your orchestration platform. The SQLite database lives at
  `/data/atlantean_prod.sqlite` by default.

## Adapting to other orchestrators

The container exposes port `8080`, runs as an unprivileged user, and reads all
configuration from the `ATLANTEAN_` environment variables. Translating the
Compose workflow to Kubernetes or systemd involves mounting a writable `/data`
volume and providing the same environment variables or key files.
