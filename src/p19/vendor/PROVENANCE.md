# Vendored third-party assets

## axe.min.js

- **Library:** axe-core (accessibility rules engine, Deque Systems).
- **Version:** 4.4.3 (banner: `axe v4.4.3`, Copyright (c) 2022 Deque Systems, Inc.).
- **License:** Mozilla Public License 2.0 (MPL-2.0). Full text: https://www.mozilla.org/MPL/2.0/.
  MPL-2.0 permits redistribution of the unmodified file; this file is unmodified.
- **SHA-256:** `697ea6c7edff0fe289b7bbecf1ff7b9015249bc834b409a348cd060df80aeba0`
- **Bytes:** 436082

### Why vendored

The renderer (`src/p19/rendering.py`, PLAN §III.8) injects axe-core into the page to compute
accessibility violation counts by impact (metric family V/A). Rendering runs with **network
blocked** (hermeticity gate, PLAN §VI.5), so axe-core must be available locally at render time —
no CDN fetch is permitted inside the render context.

### How obtained (this environment)

The official CDN distributions (`cdn.jsdelivr.net`, `cdnjs.cloudflare.com`) are blocked by the
session egress policy. The identical minified file was obtained from the PyPI package
`axe-core-python==0.1.0` (allow-listed host `files.pythonhosted.org`), which vendors the
upstream `axe.min.js` verbatim, and copied here unchanged. The banner and byte content are the
canonical Deque release of axe-core 4.4.3.

### Upstream refresh instructions

To update to a newer axe-core on a network-enabled machine:

```
curl -sSL https://cdn.jsdelivr.net/npm/axe-core@<VERSION>/axe.min.js -o src/p19/vendor/axe.min.js
```

Then record the new version, SHA-256, and byte count above, and re-run the renderer smoke test
(`tests/test_rendering.py`).
