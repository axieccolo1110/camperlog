# Coordinate lookup through OpenStreetMap Nominatim, asked from the server

When a place name is typed for a stop (later also for a campsite), CamperLog looks up its coordinates and fills them in, so users do not have to search them by hand. This is the first dependency on an external service and the first time data leaves the app: the typed place name is sent to a third party. We use the free OpenStreetMap geocoder Nominatim, which also fits the map (OpenStreetMap tiles, [ADR 0005](0005-server-rendered-pages-instead-of-spa.md)), and we ask it from the server through `GET /api/geocode`, not from the browser. That keeps the route behind the login, lets the server meet the usage policy in one place (identifying `User-Agent`, at most one request per second, caching, debounced after the user pauses typing and never on every keystroke) and sends only the place name, not the user's browser details. The lookup is a convenience: if it finds nothing or fails, the form keeps working and coordinates are entered by hand.

## Considered Options

- Ask Nominatim directly from the browser — rejected, because rate limiting and caching would be impossible for us and the policy would be met by every browser separately. It is slightly less code, though.
- Commercial geocoder (Google, Mapbox) — rejected for now: it needs an account, an API key and a secret in the deployment, may cost money, and gains little for place names like "Meran".
- No lookup, coordinates by click on the map or by hand only — kept as the fallback, but too much work for the common case.

## Consequences

- The place name leaves the app. This is stated in the docs and limited to that one string.
- The usage policy of Nominatim has to be checked again before implementing and when it changes.
- A different geocoder can be swapped in later behind `services/geocoding.py`, because nothing else knows about Nominatim.
