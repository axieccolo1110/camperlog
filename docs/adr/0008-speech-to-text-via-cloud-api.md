# Voice messages are transcribed by a cloud speech-to-text API

Telegram delivers voice messages as audio files (OGG/Opus) without text. Before the bot can understand them, they have to be transcribed. We send the audio to a cloud speech-to-text API (for example OpenAI's Whisper API), from the server, behind `services/speech.py`. Its quality for German is very good, a short clip costs a fraction of a cent and nothing has to run on Railway. Like the coordinate lookup ([ADR 0006](0006-coordinate-lookup-via-nominatim-on-the-server.md)) it is a convenience with a fallback: if transcription fails, the bot says so and the user can type or use the web form.

The bot always shows the transcript (`Verstanden: „…“`) before it acts, so recognition errors are visible early. Together with the confirmation of every writing action ([ADR 0009](0009-language-understanding-via-claude-api-with-shared-tools.md)) a misheard number cannot reach the database unnoticed.

## Considered Options

- **Self-hosted Whisper model on Railway** — rejected: it needs a lot of memory, is slow on CPU and costs more in operation than the API for a single user. The audio would stay with us, though.
- **Sending the audio straight to the language model** — not possible with the Claude API, which takes no audio input.
- **Dictation of the phone keyboard only** — works without any of this (Telegram receives text) and stays possible, but a voice message is faster with one hand and works while the phone lies in the holder.

## Consequences

- The audio of a voice message leaves the app and goes to the provider. CamperLog does not store it; only the transcript is used. This is stated in the docs.
- New environment variable for the provider's API key. Without it, voice messages are answered with a note that only text works.
- Voice messages longer than 60 seconds are rejected with a note, to bound cost and latency.
- The provider can be swapped behind `services/speech.py`, because nothing else knows about it. Tests replace it with a fake, never the network.
