# Voice input through a private Telegram bot, not an MCP connector

On the road, CamperLog should be usable by voice: record a refueling at the pump, a stop on arrival, ask what the trip cost so far. We build a private Telegram bot (created with BotFather) as a further entry point next to the web and the CLI. Telegram delivers each message by webhook to `POST /telegram/webhook` in the existing FastAPI app on Railway. The bot calls the same services as the other entry points, so every business rule still exists exactly once.

Access is checked without OAuth: Telegram sends the configured `secret_token` with every webhook call (header `X-Telegram-Bot-Api-Secret-Token`), and the bot only acts on updates whose sender is the one configured Telegram user ID. Everything else is answered with 200 and otherwise ignored, so the bot does not reveal that it exists. Telegram also gives us things a chat with an assistant cannot: inline buttons for confirming a proposal, and shared locations with real coordinates. Telegram queues messages on the phone while there is no network, which suits remote campsites.

## Considered Options

- **MCP connector for the Claude app** — rejected for now. Voice and language understanding would come for free with the Claude app and cost nothing extra, but a remote connector needs a complete OAuth flow (metadata, client registration, authorize, token, refresh, token storage), which is more work than the bot itself. There are also no fixed confirmation buttons and no shared locations. Kept possible later through the shared tool layer ([ADR 0009](0009-language-understanding-via-claude-api-with-shared-tools.md)).
- **Speech input in the web dashboard (Web Speech API)** — rejected: browser support for German is uneven, it needs the dashboard open and logged in, and the parsing of free sentences would still have to be built.
- **Long polling instead of a webhook** — rejected: it needs a process that runs permanently next to the web server. The web app already runs on Railway with HTTPS, so a webhook needs nothing new.

## Consequences

- New environment variables `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET` and `TELEGRAM_ALLOWED_USER_ID`. If they are missing the bot is switched off and the webhook route answers 404; the web app starts as before.
- The webhook route is public in the sense of the login (no session cookie) and is protected by the secret token instead. It is the third public route next to `/health` and `/login`.
- Telegram repeats an update if the webhook does not answer quickly with 200. The route therefore answers at once, handles the update in the background and processes every `update_id` only once.
- Telegram receives the message contents and the bot's replies; this is stated in the docs.
- Telegram's Bot API terms have to be checked before implementing.
