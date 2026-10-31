# Server-gerenderte Jinja-Seiten statt Single-Page-App

Das Web-Frontend wächst von einem Dashboard auf mehrere Bereiche (Trips, Stellplätze, Karte, Ausgaben, Login, Share-Seiten). Wir bleiben bei server-gerenderten Jinja-Seiten mit gemeinsamem Basis-Template und wenig Inline-JavaScript, das per `fetch()` die JSON-API anspricht. Bibliotheken wie Chart.js und Leaflet kommen per CDN. Es gibt keinen Build-Schritt und keine zweite Toolchain neben Python. Für einen einzelnen Nutzer mit Formularen und einer Karte reicht das, und das Projekt bleibt so einfach zu betreiben wie heute.

## Considered Options

- SPA mit React/Vite — verworfen, weil das eine Node-Toolchain, einen Build-Schritt im Deployment und doppelte Routing-/State-Logik bringt, ohne dass die Anforderungen das brauchen.
- htmx — nicht gewählt, weil es gegenüber dem bestehenden `fetch()`-Muster wenig gewinnt und eine weitere Arbeitsweise einführen würde. Bleibt eine Option, falls die Inline-Skripte unübersichtlich werden.
