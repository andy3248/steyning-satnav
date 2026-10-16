# Delivery round sat nav: notes for coding agents

A phone-first training sat nav for postal delivery rounds, hosted on GitHub Pages.
Live pages: `/steyning-satnav/` (Annington Round), `/steyning-satnav/ashurst/` (Ashurst Round) and `/steyning-satnav/wiston/` (Wiston Round).

## How it is built
- **Edit `src/template.html`.** It is the whole app: HTML, CSS and JS in one file.
- **Run `python3 build.py`** to regenerate `index.html`, `ashurst/index.html` and `wiston/index.html`. Never hand-edit those two files; they are build output with the round data baked in.
- `src/annington/`, `src/ashurst/` and `src/wiston/` hold each round's data (house positions, frame order, basemap). Leave them alone unless asked; they took a lot of work to assemble.
- `src/head.html` is the page wrapper (meta viewport, `[hidden]` rule). `ashurst/sw.js` and `wiston/sw.js` are the offline service workers; bump their `CACHE` name whenever that page changes.

## Things that must keep working
- **Offline:** everything is in the page. No new runtime network requests, CDNs or map tiles. One exception: the parcel label scanner loads tesseract.js (jsDelivr) and its English data the first time it is opened; the browser keeps them for offline use after that.
- **Two modes:** "Learn the round" (every house, frame order) and "Parcels today" (only ticked houses, still frame order). Start screen -> pick mode -> pick round.
- **Sat nav:** GPS follow, voice directions (`speechSynthesis`, en-GB), next-house pings, auto-advance when the driver parks then pulls away (`onParked`, `autoNext`, `AUTO` settings), Practice drive simulation.
- **Numbered roads:** a run of numbered houses on one road is a single stop (start and finish number, Finished road button, no auto-advance inside it). See `RUNS`/`runAt`.
- **Scan labels** in the Parcels picker: camera + on-phone text reading, matched to houses with `scMatch`. Never store label text.
- **Find a house** search bar, **Fix this house** tool, Rounds list.
- **Per-round storage keys** in `localStorage` (both rounds share one origin). Don't rename existing keys or people lose their progress and fixes.
- Phone-first: test at 375x812. Big touch targets (44px+), readable at a glance in a van, light and dark themes via the CSS variables in `:root`.
- Attribution lines for OpenStreetMap and Ordnance Survey must stay visible.
- No real company branding (no Royal Mail logos, names or colours used as branding).

## Checking your work
- `python3 build.py`, then open the built pages through a local server (`python3 -m http.server`) at phone size.
- Use Practice drive to check directions and voice still run end to end.
- Commit `src/template.html` and the rebuilt pages together.
