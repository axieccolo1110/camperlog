# Trip becomes a container with several stops instead of a single drive

Until now `Trip` was a single drive (origin, destination, km, one date). Since multi-week journeys with several visited places must be fully loggable (core requirement of the realignment), `Trip` becomes a container over a period (start/end date) with an ordered list of stops. Each stop has its own date and optionally references a campsite; free-standing stops without a campsite reference remain allowed so that not every overnight stay has to be catalogued.

## Considered Options

- Leave `Trip` unchanged and only loosely assign campsites (no stop concept) — rejected, it does not cover total trip costs across several visited places, which was the central requirement.
