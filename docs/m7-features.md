# M7 feature breakdown: voice input via Telegram

As of 2026-10-31 · Draft for the issues of [M7 in the PRD](prd-realignment.md#m7--voice-input-via-telegram) · Decisions: [ADR 0007](adr/0007-telegram-bot-as-voice-channel.md), [ADR 0008](adr/0008-speech-to-text-via-cloud-api.md), [ADR 0009](adr/0009-language-understanding-via-claude-api-with-shared-tools.md)

Each section becomes one issue (label `enhancement`, milestone M7). Order of work:

```
F7.1 bot connection ─┐
                     ├─> F7.3 understand text ─> F7.4 proposal + confirmation ─┬─> F7.5 voice messages
F7.2 tool layer ─────┘            │                                            └─> F7.6 shared location → stop
     (needs M4)                   └─> F7.7 answer questions
```

F7.1 and F7.2 can be built in parallel. After F7.4 the milestone is usable with typed text and keyboard dictation; F7.5 to F7.7 are independent of each other.

---

## F7.1 Bot connection and access

### Story
As the owner of CamperLog I want a Telegram bot that only reacts to my own account, so that nobody else can read or change my data through it.

### Acceptance criteria
- [ ] `POST /telegram/webhook` accepts Telegram updates only with the correct `X-Telegram-Bot-Api-Secret-Token` header; otherwise 401
- [ ] Updates from a sender other than `TELEGRAM_ALLOWED_USER_ID` are answered with 200, get no reply in Telegram and change nothing
- [ ] The route answers within a second and handles the update in the background; an `update_id` that arrives twice is handled once
- [ ] Without `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET` or `TELEGRAM_ALLOWED_USER_ID` the bot is off, the route answers 404 and the web app starts as before
- [ ] `camperlog telegram set-webhook <url>` registers the webhook with the secret at Telegram; `camperlog telegram status` shows what Telegram has registered
- [ ] A text message from the owner gets a fixed German reply for now (e.g. „Hallo, ich bin bereit.“), `/start` and `/hilfe` explain what the bot will be able to do
- [ ] The Telegram API is reached through a small client behind an interface; tests use a fake or `httpx.MockTransport`, never the network

### Depends on
- nothing

### Notes
New entry point `src/camperlog/telegram/` (webhook router, Telegram client, update handling). Like `web/` and `commands/` it never imports `sqlalchemy` or `camperlog.models` (`tests/test_layers.py`). The config check goes into `camperlog/config.py`. CLAUDE.md lists the new variables and the public route.

---

## F7.2 Shared tool layer

### Story
As a developer I want every action the bot can take described once, with its arguments and its service call, so that the bot (and later an MCP connector) use the same, tested definitions.

### Acceptance criteria
- [ ] `src/camperlog/assistant/tools.py` defines tools with a name, a German description, a JSON schema for the arguments and a kind (`read` or `write`)
- [ ] Writing tools: `record_refueling` (liters, price per liter, odometer reading, date, trip), `record_expense` (amount, category, date, note, trip), `add_stop` (place name or coordinates, date, trip)
- [ ] Reading tools: `current_trip`, `trip_costs` (total and breakdown by category), `find_trips` (by period or place), `trip_consumption`
- [ ] A writing tool can be checked without saving: it returns the normalized values plus the trip suggestion from M4, or the German message of the `ValidationError` it would raise
- [ ] Running a tool calls only services; business rules are not repeated in the tool layer
- [ ] Each tool has a test against the temporary database; the JSON schemas are checked to be valid

### Depends on
- M4 (expenses, categories, trip suggestion, trip total)

### Notes
Kept free of Telegram and of the language model ([ADR 0009](adr/0009-language-understanding-via-claude-api-with-shared-tools.md)). „Check without saving“ is what F7.4 shows in the proposal; it may need a validating function in the services that does not commit.

---

## F7.3 Understand typed messages

### Story
As a camper I want to write a normal sentence to the bot, so that I do not have to learn a command syntax.

### Acceptance criteria
- [ ] A text message from the owner is sent to the Claude API together with the tool definitions from F7.2, today's date and the current trip
- [ ] A reading tool call is run and its result is phrased as a short German answer
- [ ] A writing tool call is not run but handed to the proposal flow (F7.4)
- [ ] If required values are missing (e.g. no odometer reading for a refueling), the bot asks for exactly these and combines the answer with the earlier message
- [ ] Messages that fit no tool get a short German reply saying what the bot can do
- [ ] API unreachable, timeout or missing `ANTHROPIC_API_KEY`: one sentence that understanding is unavailable right now, plus a hint to the web forms
- [ ] German number formats are understood: decimal comma, thousands dot, numbers in words („achtundvierzig Liter“)
- [ ] Tests use a fake model that returns given tool calls; no test calls the API

### Depends on
- F7.1, F7.2

### Notes
The conversation context is kept per chat in the database for a short time (e.g. the last messages of the past 30 minutes), so follow-up answers work after a restart. The model is set in one place in `assistant/`.

---

## F7.4 Proposal and confirmation

### Story
As a camper I want to see what the bot understood before anything is saved, so that a misheard number never ends up in my data.

### Acceptance criteria
- [ ] Every writing tool call becomes a proposal message with the recognized values in German, the trip (or „ohne Reise“) and the buttons [Speichern] [Abbrechen]
- [ ] [Speichern] runs the service with exactly the values shown and replaces the buttons with a confirmation (e.g. „Gespeichert: Tanken 48,0 l à 1,79 € = 85,92 €, Reise Italien 2026“)
- [ ] [Abbrechen] discards the proposal; nothing is saved
- [ ] A proposal can be saved only once, also when the button is tapped twice or Telegram repeats the update
- [ ] A proposal expires after 24 hours; a tap after that says so and saves nothing
- [ ] A `ValidationError` on saving is shown with its German message and the proposal stays unsaved
- [ ] Proposals are stored in a new table `proposals` (Alembic migration) and survive a restart

### Depends on
- F7.3

### Notes
Changing single values of a proposal (e.g. a different trip) is done by a new sentence („nein, ohne Reise“), which creates a new proposal and discards the old one. Buttons for that are left out on purpose.

**After F7.4 the milestone is usable:** with typed text or keyboard dictation everything can be recorded.

---

## F7.5 Voice messages

### Story
As a camper I want to send a voice message instead of typing, so that I can record things with one hand or while the phone lies in the holder.

### Acceptance criteria
- [ ] A voice message from the owner is downloaded from Telegram (`getFile`), transcribed via `services/speech.py` and handled like a typed message
- [ ] Before handling, the bot shows the transcript: `Verstanden: „…“`
- [ ] Voice messages longer than 60 seconds are rejected with a note
- [ ] Transcription unavailable or no API key: one sentence that only text works right now
- [ ] The audio is not stored, neither in the database nor on disk beyond the request
- [ ] Tests use a fake transcriber; no test calls the provider

### Depends on
- F7.3 (F7.4 for writing actions)

### Notes
Provider per [ADR 0008](adr/0008-speech-to-text-via-cloud-api.md). The language of the transcription is set to German.

---

## F7.6 Shared location becomes a stop

### Story
As a camper I want to share my location in Telegram on arrival, so that the stop gets the exact coordinates without typing a place.

### Acceptance criteria
- [ ] A location shared by the owner leads to a proposal „Stopp heute in <Ort>, Reise <Name>“ with the coordinates
- [ ] The place name is looked up from the coordinates (reverse lookup via Nominatim); if that fails, the proposal shows the coordinates only and the stop is saved without a place name
- [ ] If a bookmarked or visited campsite lies within 200 m, the proposal offers it: [Mit Stellplatz <Name>] [Ohne Stellplatz]
- [ ] Without a trip that includes today, the bot says so and creates no proposal
- [ ] Live locations are ignored with a note to share a single location

### Depends on
- F7.4

### Notes
The reverse lookup extends `services/geocoding.py` and follows the same usage policy (User-Agent, one request per second, cache). [ADR 0006](adr/0006-coordinate-lookup-via-nominatim-on-the-server.md) is amended: the coordinates of a shared location leave the app as well.

---

## F7.7 Answer questions about my data

### Story
As a camper I want to ask the bot about my trips and costs, so that I get an answer on the road without opening the dashboard.

### Acceptance criteria
- [ ] „Was hat die Reise bisher gekostet?“ answers the same total and breakdown by category as the web for the current trip
- [ ] Questions about a past period or place („Wo waren wir letzten Sommer?“, „Wann waren wir in Meran?“) list the matching trips and stops
- [ ] „Wie war der Verbrauch auf der letzten Reise?“ answers with the value of the existing consumption calculation
- [ ] If there is no matching data, the bot says so instead of guessing
- [ ] Amounts are written in German format (`1.234,56 €`), dates as `31.10.2026`
- [ ] Only the data a question needs is sent to the model, not the whole database

### Depends on
- F7.3

### Notes
Each answer should be one to three short sentences; long lists are cut after five entries with a link to the matching web page.
