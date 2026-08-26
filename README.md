# Game Asset Library

Real artwork by real artists, catalogued so any Claude session can find the right
sprite instead of generating one.

**297 packs · 144,324 files · 1.15 GB** across two libraries.

> **Browse it on any device:** **https://eturner58.github.io/game-assets/**
>
> The art is committed here, not just catalogued: **78,121 files, 523 MB** of
> CC0 Kenney work — 2D, UI, Icons, Audio, 6,691 sliced tiles, and the 3D kits in
> glTF/GLB form. A clone, or the Pages site above, gives you the actual pixels
> and meshes, not only the index.
>
>
> **What is not here.** Kenney's Archive and Early access sections; the five
> redundant 3D formats (`.fbx`/`.obj`/`.dae`/`.stl`/`.mtl` — the same models
> again, 409 MB); and **all LimeZu art**, whose licence forbids redistribution,
> so only its metadata ships. See [Rehydrating the rest](#rehydrating-the-rest).

---

## Start here

| I want to... | Do this |
|---|---|
| **Browse visually** | [eturner58.github.io/game-assets](https://eturner58.github.io/game-assets/) — or open `catalog/index.html` locally |
| **Find a pack programmatically** | Read `catalog/library.json` (297 entries, ~1 MB) |
| **Find an individual file** | Grep `catalog/files.jsonl` (90,789 rows) |
| **See the rollup** | `catalog/library_summary.md` |
| **Check what I'm allowed to ship** | **[LICENSES.md](LICENSES.md) — read this before publishing** |

---

## The two libraries

### Kenney Game Assets All-in-1 v3.7.0 — CC0

269 packs, 90,789 files, 984 MB. Public domain, no strings.

| Section | Packs | Files | Size | Worth it? |
|---|---|---|---|---|
| 2D assets | 156 | 42,879 | 255 MB | **The main event** |
| 3D assets | 54 | 28,457 | 606 MB | glTF/GLB published (Three.js-ready); other formats local |
| Icons | 8 | 9,744 | 12 MB | Input prompts, UI glyphs — excellent |
| UI assets | 10 | 6,566 | 8 MB | Buttons, panels, bars |
| Audio | 16 | 1,319 | 27 MB | SFX + music loops, .ogg |
| Archive | 16 | 1,308 | 53 MB | Superseded packs, mostly still zipped |
| Other / Goodies / Early access | 9 | 516 | 23 MB | Fonts, samples, wallpapers |

Kenney ships every 3D model in six formats. Only glTF/GLB loads in a web engine,
so that is what is published (4,975 `.glb` + 4,850 textures + 232 `.gltf`/`.bin`);
the other five formats are 409 MB of duplication and stay local.

**Note on `usefulness`:** the 1–5 score answers "how useful for a **2D browser**
prototype", so all 54 3D packs score 1. That is correct for the question asked and
misleading for Three.js work — filter 3D packs by `section`, not by `usefulness`.

### LimeZu "Modern Interiors" — PAID, metadata only

28 packs, 53,535 files, 166 MB. Contemporary top-down pixel art — interiors,
furniture, modern-dress characters at 16/32/48px.

Lives at `Games/Last Take/assets/`. **Its licence forbids redistribution**, so only
its metadata is catalogued here; no LimeZu pixels are in this repo and `.gitignore`
blocks its paths as a safety net. Fine to *use* in a build (credit
`limezu.itch.io`), never to *republish*. Details in [LICENSES.md](LICENSES.md).

---

## Finding art

Every pack in `catalog/library.json` carries vision-derived metadata — a subagent
looked at each pack's preview image before describing it:

```json
{
  "id": "2D assets/Pirate Pack",
  "path": "kenney/2D assets/Pirate Pack",
  "description": "...", "best_for": "...",
  "perspective": "top-down",        // top-down | side-view | isometric | hexagonal
                                    // | first-person | ui | none
  "style": "vector-flat",           // pixel-art | vector-flat | hand-drawn
                                    // | 3d-render | line-art | monochrome | photo
  "genres": ["..."], "subjects": ["..."], "tags": ["..."],
  "usefulness": 4,                  // 1-5, for a 2D browser prototype
  "sprite_sizes": [["64x64", 312]],
  "redistributable": true, "license_name": "CC0 1.0 (public domain)"
}
```

Useful queries:

```bash
# Top-down pixel-art packs good enough to build on
py -c "import json;print([p['id'] for p in json.load(open('catalog/library.json')) if p['perspective']=='top-down' and p['style']=='pixel-art' and p['usefulness']>=4])"

# Every file containing 'ship' in a 2D pack
grep '\"section\": \"2D assets\"' catalog/files.jsonl | grep -i ship

# All 16x16 sprites
grep '\"width\": 16, \"height\": 16' catalog/files.jsonl
```

`tagged_by` records how each entry was described: `vision` (previewed, 253 packs),
`name-inference` (no preview existed — all are zip-only Archive stubs), or
`structural` (LimeZu, described from folder layout). Treat `name-inference`
descriptions as weaker than the rest.

---

## Slicing

Kenney already ships **53,256 individual sprite PNGs** — for almost every pack, no
slicing is needed. Only seven packs shipped a packed sheet with no singles. Those
were sliced from each pack's own documented grid (never a guessed one) into
`sliced/`, 6,690 tiles:

| Pack | Grid | Tiles |
|---|---|---|
| Roguelike Base Pack | 16px, 1px margin | 1,704 |
| 1-Bit Pack (colored + monochrome) | 16px, 1px margin | 2,154 |
| UI Pixel Pack | 16px, **2px** margin | 760 |
| Topdown Shooter (Pixel) | 16px, 1px margin | 623 |
| Roguelike Dungeon / Interior / Characters | 16px, 1px margin | 1,449 |

Fully transparent tiles are dropped. `sliced/sliced_manifest.json` records the grid
and counts per sheet. The tiles are committed, and also regenerable from source.

---

## Rehydrating the rest

Most of the art is committed. These need restoring locally:

1. **Kenney Archive / Early access, and the non-glTF 3D formats** — everything else
   is already in this repo. Get *Game Assets All-in-1* (v3.7.0 is what this catalogue
   was built from) from [kenney.nl](https://kenney.nl/) or the Kenney itch.io page and
   extract over `Games/assets/kenney/` so paths match the catalogue's `path` field. CC0.
2. **LimeZu** — a paid pack from
   [limezu.itch.io/moderninteriors](https://limezu.itch.io/moderninteriors). Restore
   from your own purchase to `Games/Last Take/assets/`. Do not redistribute it.
3. Regenerate to confirm the trees match:

```bash
py catalog/build_catalog.py         # Kenney   -> packs.json, files.jsonl
py catalog/build_catalog_limezu.py  # LimeZu   -> packs_limezu.json, files_limezu.jsonl
py catalog/copy_previews.py         # preview thumbnails
py catalog/slice_sheets.py          # the 7 sheet-only packs
py catalog/merge_catalog.py         # -> library.json + library_summary.md
py catalog/build_index.py           # -> index.html
```

Each script is idempotent and reports read failures rather than silently skipping
files. An unreadable file is always reported, never counted as zero.

---

## Layout

```
Games/assets/
├── README.md
├── LICENSES.md              ← read before shipping
├── catalog/                 ← committed
│   ├── index.html           visual browser (open directly)
│   ├── library.json         master index, 297 packs
│   ├── library_summary.md   rollup
│   ├── packs.json           Kenney, mechanical scan
│   ├── files.jsonl          Kenney, 90,789 rows
│   ├── packs_limezu.json    LimeZu, metadata only
│   ├── files_limezu.jsonl   LimeZu, 53,535 rows
│   ├── previews/            253 pack thumbnails (CC0)
│   └── *.py                 the generators
├── kenney/                  ← 2D/UI/Icons/Audio + 3D as glTF/GLB committed
├── sliced/                  ← committed (6,691 tiles)
└── _source-zips/            ← NOT committed (800 MB of originals)
```

`_source-zips/` holds the three original downloads. Two of them —
*All-in-1 3.4.0 (Windows)* and *(Linux)* — are just installer binaries (a `.exe`
and an `.AppImage`) for an **older** version, not asset archives. Only
*All-in-1 3.7.0* carried the art. They are kept for provenance and can be deleted.
