# Telegram Bot API

The Telegram Bot API provides an HTTP API for creating [Telegram Bots](https://core.telegram.org/bots).

If you've got any questions about bots or would like to report an issue with your bot, kindly contact us at [@BotSupport](https://t.me/BotSupport) in Telegram.

Please note that only global Bot API issues that affect all bots are suitable for this repository.

## Pinchana GHCR image

Prebuilt Linux x86-64 images are published to `ghcr.io/pinchana/telegram-bot-api`:

- `latest` and `master`: the latest successful trusted build from `master`.
- `sha-COMMIT`: the corresponding source commit (12 hexadecimal characters).
- `10.1` / `v10.1`, `10.2` / `v10.2`, `10.3` / `v10.3`: matching tagged releases.
  Every version tag with a verified release binary is supported by the publisher.

The non-root image uses UID/GID 1000 and listens on port **9998** in `--local`
mode. Supply your own `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` from
[my.telegram.org](https://my.telegram.org). These credentials are not in the image.

```sh
docker run --rm --init \
  -p 127.0.0.1:9998:9998 \
  -e TELEGRAM_API_ID -e TELEGRAM_API_HASH \
  -v telegram-bot-api-data:/var/lib/telegram-bot-api \
  ghcr.io/pinchana/telegram-bot-api:latest
```

Command arguments override the default server options. Keep the service private;
it is intended for trusted bot clients and is not an authenticated public gateway.

`Publish GHCR Docker image` automatically follows successful binary builds and
published releases. It can also publish all existing version tags plus master:

```sh
gh workflow run publish-image.yml -f version=all
```

Release binaries are verified against their GitHub SHA-256 digests. Images are
smoke-tested before publication; pull-request and fork builds cannot publish.
Historical releases never overwrite `latest`. The publisher uses `GITHUB_TOKEN`
with `packages: write`; no registry password secret is required. Docker build
record artifacts are disabled to avoid filling Actions artifact storage.

## Table of Contents
- [Installation](#installation)
- [Dependencies](#dependencies)
- [Usage](#usage)
- [Documentation](#documentation)
- [Moving a bot to a local server](#switching)
- [Moving a bot from one local server to another](#moving)
- [License](#license)

<a name="installation"></a>
## Installation

The simplest way to build and install `Telegram Bot API server` is to use our [Telegram Bot API server build instructions generator](https://tdlib.github.io/telegram-bot-api/build.html).
If you do that, you'll only need to choose the target operating system to receive the complete build instructions.

In general, you need to install all `Telegram Bot API server` [dependencies](#dependencies) and compile the source code using CMake:

```sh
git clone --recursive https://github.com/tdlib/telegram-bot-api.git
cd telegram-bot-api
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build . --target install
```

<a name="dependencies"></a>
## Dependencies
To build and run `Telegram Bot API server` you will need:

* OpenSSL
* zlib
* C++17 compatible compiler (e.g., Clang 5.0+, GCC 7.0+, MSVC 19.1+ (Visual Studio 2017.7+), Intel C++ Compiler 19+) (build only)
* gperf (build only)
* CMake (3.10+, build only)

<a name="usage"></a>
## Usage

Use `telegram-bot-api --help` to receive the list of all available options of the Telegram Bot API server.

The only mandatory options are `--api-id` and `--api-hash`. You must obtain your own `api_id` and `api_hash`
as described in https://core.telegram.org/api/obtaining_api_id and specify them using the `--api-id` and `--api-hash` options
or the `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` environment variables.

To enable Bot API features not available at `https://api.telegram.org`, specify the option `--local`. In the local mode the Bot API server allows to:
* Download files without a size limit.
* Upload files up to 2000 MB.
* Upload files using their local path and [the file URI scheme](https://en.wikipedia.org/wiki/File_URI_scheme).
* Use an HTTP URL for the webhook.
* Use any local IP address for the webhook.
* Use any port for the webhook.
* Set *max_webhook_connections* up to 100000.
* Receive the absolute local path as a value of the *file_path* field without the need to download the file after a *getFile* request.

The Telegram Bot API server accepts only HTTP requests, so a TLS termination proxy needs to be used to handle remote HTTPS requests.

By default the Telegram Bot API server is launched on the port 8081, which can be changed using the option `--http-port`.

<a name="documentation"></a>
## Documentation
See [Bots: An introduction for developers](https://core.telegram.org/bots) for a brief description of Telegram Bots and their features.

See the [Telegram Bot API documentation](https://core.telegram.org/bots/api) for a description of the Bot API interface and a complete list of available classes, methods and updates.

See the [Telegram Bot API server build instructions generator](https://tdlib.github.io/telegram-bot-api/build.html) for detailed instructions on how to build the Telegram Bot API server.

Subscribe to [@BotNews](https://t.me/botnews) to be the first to know about the latest updates and join the discussion in [@BotTalk](https://t.me/bottalk).

<a name="switching"></a>
## Moving a bot to a local server

To guarantee that your bot will receive all updates, you must deregister it with the `https://api.telegram.org` server by calling the method [logOut](https://core.telegram.org/bots/api#logout).
After the bot is logged out, you can replace the address to which the bot sends requests with the address of your local server and use it in the usual way.
If the server is launched in `--local` mode, make sure that the bot can correctly handle absolute file paths in response to `getFile` requests.

<a name="moving"></a>
## Moving a bot from one local server to another

If the bot is logged in on more than one server simultaneously, there is no guarantee that it will receive all updates.
To move a bot from one local server to another you can use the method [logOut](https://core.telegram.org/bots/api#logout) to log out on the old server before switching to the new one.

If you want to avoid losing updates between logging out on the old server and launching on the new server, you can remove the bot's webhook using the method
[deleteWebhook](https://core.telegram.org/bots/api#deletewebhook), then use the method [close](https://core.telegram.org/bots/api#close) to close the bot instance.
After the instance is closed, locate the bot's subdirectory in the working directory of the old server by the bot's user ID, move the subdirectory to the working directory of the new server
and continue sending requests to the new server as usual.

<a name="license"></a>
## License
`Telegram Bot API server` source code is licensed under the terms of the Boost Software License. See [LICENSE_1_0.txt](http://www.boost.org/LICENSE_1_0.txt) for more information.
