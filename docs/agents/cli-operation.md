# Operating CamperLog through the CLI from natural language

The user may ask in plain language (usually German) to record or look up data, e.g. "trag eine Tankfüllung ein: 45 Liter, 1,85 €, 12.500 km". The agent translates this into `camperlog` commands, runs them in the shell and reports the result. The CLI is the only interface used: its validation (German messages from `services/`) stays the single source of truth for what is allowed.

## Bootstrap

```bash
python3 -m venv .venv && source .venv/bin/activate   # if .venv does not exist yet
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .
camperlog db upgrade
```

Without `DATABASE_URL` the CLI uses the local SQLite file `data/camperlog.db` (git-ignored). In a cloud session that file is lost when the session ends, so data entered this way is scratch data unless the user says otherwise.

## Which database? (check before every write)

Before the first write of a session, and again whenever `DATABASE_URL` may have changed, state the target to the user: the SQLite file, or for anything else only the host and database name, never the password.

- No `DATABASE_URL` (local SQLite): proceed.
- `DATABASE_URL` points to anything but SQLite (e.g. the Railway PostgreSQL): **stop and ask.** Write only after the user explicitly confirms with the target named. A confirmation for one session or one target does not carry over.

Reads (`list`, `show`) are harmless on any target.

## Commands

| Area | Commands |
| --- | --- |
| Trips | `trip add --start --end [--km]`, `trip list`, `trip show ID`, `trip edit ID [--start --end --km --clear-km]`, `trip delete ID` |
| Stops | `trip stop add TRIP_ID --date [--place --lat --lon --campsite]`, `trip stop edit STOP_ID …`, `trip stop delete STOP_ID` |
| Refuelings | `fuel add --date --liters --price-per-liter --odometer`, `fuel list`, `fuel edit ID [--date --liters --price-per-liter --odometer]`, `fuel delete ID` |
| Campsites | `campsite add --name --lat --lon [--status --notes --playground --pets --url]`, `campsite list` |

Run `camperlog <group> <command> --help` for the exact options. Dates are `YYYY-MM-DD`; resolve relative dates ("nächsten Freitag") against today's date and show the resolved date in the command. Decimal commas in the user's text become points in the command.

## Rules

1. **Show the command and the result.** Print the exact `camperlog …` command next to the output, so the user sees misunderstandings before they matter.
2. **Ask only when really ambiguous.** If several readings are plausible (e.g. a stop without saying which of several trips), ask. If there is one obvious reading (e.g. only one trip exists), use it and name the assumption. Never invent missing values such as an odometer reading.
3. **Confirm before deleting.** `delete` commands ask interactively through `click.confirm`, which cannot be answered from the agent's shell. Ask the user in the chat first, then run the command with `--yes`. `edit` needs no extra confirmation beyond rule 1.
4. **Say what the CLI cannot do, and stop there.** Do not reach past the CLI to the service layer, the API or the database. Known gaps:
   - Campsites cannot be edited or deleted (issue #26).
   - `campsite list` does not show notes or link.
5. **Explain errors in context.** Validation errors are German messages from the services (e.g. a stop date outside the trip period); say in one sentence what to change, do not just repeat the text.
6. **Confirm what was recorded.** After a write, summarise in one line what was stored, with its number (`Nr.`), so the user can refer to it later.
