# Free sentences are understood by the Claude API with tool use over a shared tool layer, and every write is confirmed

The bot should understand sentences like „48 Liter für 1,79, Kilometerstand 84.200“ or „Was hat die Reise bisher gekostet?“. Fixed command syntax (`/tanken 48 1,79 84200`) is no fun to speak. We use the Claude API with tool use: the bot sends the text together with today's date and the current trip, and the model picks a tool and fills its arguments.

The tools are defined once in a layer of their own, `assistant/tools.py`: each tool has a name, a German description, a JSON schema for its arguments and a function that calls the services. The layer knows neither Telegram nor the language model, so it can be tested directly and can later serve an MCP connector unchanged ([ADR 0007](0007-telegram-bot-as-voice-channel.md)).

Tools are either **reading** (answers to questions; run at once) or **writing** (create something; never run directly). A writing tool call becomes a **proposal**: the bot shows the values and the trip and waits for [Speichern] or [Abbrechen]. Only the tap runs the service function, with exactly the values shown. The model therefore never writes to the database itself, and a wrong understanding costs one tap on [Abbrechen].

## Considered Options

- **Fixed commands with a parser** — rejected as the only way: hard to speak, and every new phrasing needs code. Commands like `/abbrechen` remain as plain Telegram commands.
- **Own parser with rules and regular expressions** — rejected: brittle for numbers spoken in words, units and German decimal commas.
- **Running writing tools directly, with an undo button** — rejected: an undo after the fact is easy to miss on the road; the user decided that every write is confirmed.

## Consequences

- Message texts, the current date and the data a question needs (e.g. the expenses of a trip) go to Anthropic. This is stated in the docs.
- New environment variable `ANTHROPIC_API_KEY`. Without it, the bot answers that it cannot understand messages right now.
- A small, fast model is enough; the exact model is chosen during implementation and set in one place.
- Proposals are stored in the database (table `proposals`: payload, state, created at), so a restart on Railway does not lose them. A proposal expires after 24 hours and can be saved only once.
- Business rule violations raised by the services on [Speichern] (`ValidationError`) are shown with their German message, as on the web.
- Tests of the bot replace the model with a fake that returns given tool calls; no test calls the API.
