FROM debian:bookworm-slim

ARG TELEGRAM_BOT_API_VERSION
ARG TELEGRAM_BOT_API_REVISION
LABEL org.opencontainers.image.source="https://github.com/Pinchana/telegram-bot-api" \
      org.opencontainers.image.title="Pinchana Telegram Bot API" \
      org.opencontainers.image.version="${TELEGRAM_BOT_API_VERSION}" \
      org.opencontainers.image.revision="${TELEGRAM_BOT_API_REVISION}" \
      org.opencontainers.image.licenses="BSL-1.0"

RUN apt-get update \
    && apt-get install --yes --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 telegram \
    && useradd --uid 1000 --gid telegram --create-home telegram \
    && mkdir -p /var/lib/telegram-bot-api/temp \
    && chown -R telegram:telegram /var/lib/telegram-bot-api

COPY --chmod=0755 .docker-bin/telegram-bot-api /usr/local/bin/telegram-bot-api

COPY LICENSE_1_0.txt /usr/share/licenses/telegram-bot-api/LICENSE_1_0.txt

USER telegram
WORKDIR /var/lib/telegram-bot-api
EXPOSE 9998
ENTRYPOINT ["telegram-bot-api"]
CMD ["--local", "--http-port=9998", "--dir=/var/lib/telegram-bot-api", "--temp-dir=/var/lib/telegram-bot-api/temp"]
