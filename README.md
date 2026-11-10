# Pinchana Telegram Bot API Docker image

Prebuilt Telegram Bot API server images for Docker, published at
[`ghcr.io/pinchana/telegram-bot-api`](https://github.com/orgs/Pinchana/packages/container/package/telegram-bot-api).

This image is used by **Pinchana-bot, a closed-source Telegram bot**. This
repository contains the Bot API server and its image publishing workflows;
the closed-source bot application is not included here.

## Available images

| Tag | Contents |
| --- | --- |
| `latest`, `master` | Latest successful `master` build; currently Bot API 10.4 |
| `10.3`, `v10.3` | Bot API 10.3 release |
| `10.2`, `v10.2` | Bot API 10.2 release |
| `10.1`, `v10.1` | Bot API 10.1 release |
| `sha-<12-character-commit>` | A specific published `master` build |

Images currently support **Linux amd64 / x86-64**. They are public: pulling
requires no GHCR account or registry login. Use a release tag or image digest
when you want to pin a deployment instead of following `latest`.

```sh
docker pull ghcr.io/pinchana/telegram-bot-api:latest
```

## Credentials

Obtain an API ID and API hash from [my.telegram.org](https://my.telegram.org).
Create `telegram-bot-api.env` and replace both placeholders with your values:

```dotenv
TELEGRAM_API_ID=YOUR_API_ID
TELEGRAM_API_HASH=YOUR_API_HASH
```

```sh
chmod 600 telegram-bot-api.env
```

These are your Telegram application credentials. They are not a bot token,
and they are not included in the image. Keep this file out of version control.

## Run with Docker

```sh
docker volume create telegram-bot-api-data

docker run --detach \
  --name telegram-bot-api \
  --init \
  --restart unless-stopped \
  --env-file ./telegram-bot-api.env \
  --publish 127.0.0.1:9998:9998 \
  --volume telegram-bot-api-data:/var/lib/telegram-bot-api \
  ghcr.io/pinchana/telegram-bot-api:latest
```

The endpoint is `http://127.0.0.1:9998` for clients on the Docker host. The port
is published on loopback only; keep the server on a trusted local/private network.

Check the running container:

```sh
docker logs --tail 100 telegram-bot-api
docker exec telegram-bot-api telegram-bot-api --version
```

## Run with Docker Compose

Save this as `compose.yml` next to `telegram-bot-api.env`:

```yaml
services:
  telegram-bot-api:
    image: ghcr.io/pinchana/telegram-bot-api:latest
    init: true
    restart: unless-stopped
    env_file:
      - telegram-bot-api.env
    ports:
      - "127.0.0.1:9998:9998"
    volumes:
      - telegram-bot-api-data:/var/lib/telegram-bot-api
    stop_grace_period: 30s
    healthcheck:
      test: ["CMD", "bash", "-c", ": >/dev/tcp/127.0.0.1/9998"]
      interval: 10s
      timeout: 5s
      retries: 6
      start_period: 10s

volumes:
  telegram-bot-api-data:
```

Start or update it without building anything locally:

```sh
docker compose pull telegram-bot-api
docker compose up --detach telegram-bot-api
docker compose ps
docker compose logs --tail 100 telegram-bot-api
```

A bot container attached to the same Compose network can use
`http://telegram-bot-api:9998`. A client running directly on the host can use
`http://127.0.0.1:9998`.

## Storage and defaults

The image runs as **UID/GID 1000:1000** with these default arguments:

```text
--local
--http-port=9998
--dir=/var/lib/telegram-bot-api
--temp-dir=/var/lib/telegram-bot-api/temp
```

Persist `/var/lib/telegram-bot-api` across container replacements. The examples
use a named volume. If you prefer a host directory, prepare its ownership first:

```sh
mkdir -p telegram-bot-api-data
sudo chown -R 1000:1000 telegram-bot-api-data
```

Then replace the volume mount with
`./telegram-bot-api-data:/var/lib/telegram-bot-api`.

Arguments after the image name replace the entire default command. For example,
to use port 8081, pass all required options and publish the matching port:

```sh
docker run --detach \
  --name telegram-bot-api \
  --init \
  --restart unless-stopped \
  --env-file ./telegram-bot-api.env \
  --publish 127.0.0.1:8081:8081 \
  --volume telegram-bot-api-data:/var/lib/telegram-bot-api \
  ghcr.io/pinchana/telegram-bot-api:latest \
  --local --http-port=8081 \
  --dir=/var/lib/telegram-bot-api \
  --temp-dir=/var/lib/telegram-bot-api/temp
```

Use this alternate command instead of the earlier container, not alongside it
with the same container name and data volume.

## Use in Pinchana-bot

The closed-source **Pinchana-bot** deployment pulls this image directly from
GHCR. It does not build its own Bot API server image. Its Compose configuration
preserves port `9998`, UID/GID `1000:1000`, and the persistent Bot API data mount.
`TELEGRAM_BOT_API_IMAGE` in that deployment can override the image tag or digest.

Pinchana also mounts its existing scraper cache read-only at `/app/cache` in
both the bot and Bot API containers. If you integrate a shared file cache,
mount it at the **same absolute path** in both containers so local file uploads
can read it. The standalone examples above do not require that additional mount.

## Image publishing

Successful trusted binary builds and published releases trigger
`.github/workflows/publish-image.yml`. Release binaries are checked against
GitHub's SHA-256 digests; each image is tested for its reported version,
non-root user, and writable data directories before publication.

Maintainers can publish every available version tag plus the latest successful
`master` build, or publish one release:

```sh
gh workflow run publish-image.yml -f version=all
gh workflow run publish-image.yml -f version=v10.3
```

Historical release images never replace `latest`. Publishing uses the workflow's
`GITHUB_TOKEN` with `packages: write`; no registry password secret is needed.
Pull-request and fork builds cannot publish images.

## Upstream and license

Based on [Telegram's Bot API server](https://github.com/tdlib/telegram-bot-api),
licensed under the [Boost Software License 1.0](LICENSE_1_0.txt). The server's
open-source license is separate from the closed-source Pinchana-bot application.
