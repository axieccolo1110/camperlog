# PRD: CamperLog realignment — a private travel journal with a map

As of 2026-10-31 · Terms: see [CONTEXT.md](../CONTEXT.md) · Decisions: see [docs/adr/](adr/)

## Problem

Today CamperLog only records single drives (from/to, km, date) and refuelings. That can neither represent a multi-week journey with several places, nor answer what a journey cost in total. Places where you have been or that you bookmark for later have no home at all. Users therefore maintain spreadsheets, note apps and favorite lists in Park4Night in parallel.

In addition, the web dashboard and its API are currently publicly reachable without a login.

## Goal

CamperLog becomes a **private travel journal**: log complete journeys with all their stops, see your own campsites (visited and bookmarked) on a map, and know in the end what a journey really cost.

## Positioning and non-goals

CamperLog complements the specialist apps instead of replacing them ([ADR 0001](adr/0001-campsite-complements-crowd-databases.md)). You keep finding places via Park4Night, iOverlander & co. and enter them into CamperLog with a link. The added value none of these apps offers: your own places, journeys and costs in one place, linked to each other.

Explicitly **not** part of this realignment:

- Own campsite search, crowd database or ratings
- Route planning or navigation (the map only shows straight lines between stops)
- Multiple users or accounts. CamperLog has exactly one user.
- A full finance or maintenance tool in the style of Fuelio

## Target audience

The basis is two simulated personas plus the ideas of the product owner:

- **Jörg**, 52, travels solo with his dog in a self-converted Sprinter, 3–4 long trips a year to southern Europe. Wants an honest cost total per journey, does not need a map, wants to share individual things with acquaintances.
- **Sabine**, 41, family with two children, weekend and holiday trips, plans campsites months in advance. For her the map and the bookmark list are the core ("playground available" is her most important field), plus the cost total per holiday.
- **Product owner:** the map with your own campsites is priority 1. Expenses and maintenance stay in scope, but with lower priority.

Sabine's wish for shared access for several people is deliberately not implemented (see non-goals).

## Milestones

The order follows the dependencies: each milestone builds on the previous one.

### M1 — Login for the web

- The dashboard and all `/api/*` routes are only reachable after a login. Exceptions: `/health` and, later, the share link pages.
- A single password, set via an environment variable. No accounts, no registration.
- The CLI accesses the database directly and is not affected.

**Done when:** a request to the dashboard or the API without a login is rejected and `/health` still answers, so the Railway health check stays green.

### M2 — Trip with stops

([ADR 0002](adr/0002-trip-with-multiple-stops.md))

- A **trip** has a start and an end date, optionally a distance in km entered by hand, and an ordered list of **stops**.
- A **stop** has a date and either references a campsite (and takes over its location) or is free-standing with an optional place name and optional coordinates.
- **Migration:** every existing trip becomes a trip whose start and end date equal the old date, with two free-standing stops (place name = old origin and old destination respectively). The old km value is kept as the distance.
- The date of a stop must lie within the period of its trip. Stops are sorted by date; stops with the same date keep the order in which they were entered.
- Trips and stops can be edited and deleted. A changed trip period must include all existing stops. If a trip is deleted, its stops disappear as well.
- CLI: create and list trips, add stops to a trip (`trip stop …`).

**Done when:** a three-week journey with six stops (two of them free-standing) can be entered via web and via CLI, and all old trips are migrated without data loss.

### M3 — Campsite and map (priority 1)

- A **campsite** can be created independently of trips and has: name, coordinates, status (visited/bookmarked), free-text notes, fixed flags (playground available, pets allowed) and an optional external link (e.g. Park4Night).
- The status is set by hand. As soon as a stop with a date in the past references a campsite, it automatically becomes "visited". Visits from before CamperLog can thus be entered without a trip.
- A campsite can be referenced by any number of stops, e.g. a favorite place on several journeys.
- Campsites can be edited and deleted. A campsite that a stop references cannot be deleted.
- **Map** in the web dashboard with two clearly separated views:
  - **Retrospective:** visited campsites and free-standing stops with coordinates as pins. Per trip a straight line connecting the stops in order can be shown.
  - **Bookmark list:** bookmarked campsites.
- The map exists on the web only. The CLI can create and list campsites (`campsite …`).
- **Coordinate lookup:** when a place name is entered for a stop (later also for a campsite), the coordinates are looked up in the background and filled in if the place is known. With several matches the user picks one. If the lookup finds nothing or fails, entering coordinates by hand still works ([ADR 0006](adr/0006-coordinate-lookup-via-nominatim-on-the-server.md)).

**Done when:** you can bookmark a place in February, assign it to a trip as a stop in August, and it then appears in the retrospective instead of the bookmark list.

### M4 — Expenses and trip total

([ADR 0003](adr/0003-refueling-is-an-expense.md))

- An **expense** has a date, an amount, a category, optionally a note and optionally a trip.
- **Categories:** predefined are Fuel, Campsite fee, Ferry/Toll, Repair/Maintenance, Groceries, Leisure and Other. You can add and rename your own categories. Fuel can be neither renamed nor deleted. A category can only be deleted if no expense uses it any more.
- **Refueling** = expense of the category Fuel with liters, price per liter and odometer reading. The consumption (L/100km) is calculated from these as before. Existing fuel entries are migrated.
- **Assignment to a trip:** if the date lies within a trip's period, that trip is suggested. You can change or remove it (a ferry booked in advance belongs to the trip, the insurance debited during the trip does not).
- **Trip total:** per trip the total costs, broken down by category.
- CLI: `expense …` to record and list. `fuel add` stays as a shorthand for a fuel expense.

**Done when:** for a trip with fuel, campsite and ferry expenses the total with its breakdown is shown, and the previous consumption values are unchanged after the migration.

### M5 — Share links

- The user can create a share link for a single **trip** (map and stops) or a single **campsite**.
- Through a share link the content is visible read-only and without a login. **Expenses and costs are never visible.**
- A share link can be deactivated at any time and does not expire on its own.

**Done when:** a shared trip can be opened without a login, shows no amounts, and is no longer reachable after deactivation.

### M6 — Maintenance (placeholder)

Reminders for maintenance by odometer reading or time (e.g. oil change) are wanted but have low priority. Structure and scope will only be defined when the milestone comes up.

## Open points

No open product decisions. Technical details (e.g. map library and map tiles, migration strategy for PostgreSQL in production) are settled per milestone during implementation.
