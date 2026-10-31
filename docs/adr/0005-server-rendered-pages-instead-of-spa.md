# Server-rendered Jinja pages instead of a single-page app

The web frontend grows from one dashboard to several areas (trips, campsites, map, expenses, login, share pages). We stay with server-rendered Jinja pages with a shared base template and little inline JavaScript that talks to the JSON API via `fetch()`. Libraries such as Chart.js and Leaflet come from a CDN. There is no build step and no second toolchain next to Python. For a single user with forms and a map that is enough, and the project stays as simple to operate as it is today.

## Considered Options

- SPA with React/Vite — rejected, because it brings a Node toolchain, a build step in the deployment and duplicated routing/state logic, without the requirements needing it.
- htmx — not chosen, because it gains little over the existing `fetch()` pattern and would introduce another way of working. Remains an option if the inline scripts become hard to follow.
