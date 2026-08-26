# Asset Licences — read this before shipping anything

Two libraries are catalogued here. **They have opposite redistribution terms.**
Getting this wrong is the one mistake in this repo that has consequences outside
your machine.

---

## 1. Kenney Game Assets All-in-1 (v3.7.0) — CC0

**Source:** https://kenney.nl · **Licence:** Creative Commons Zero (CC0 1.0)

> This content is free to use in personal, educational and commercial projects.
> Support us by crediting Kenney or www.kenney.nl (this is not mandatory)

| | |
|---|---|
| Use commercially | Yes |
| Modify / remix | Yes |
| Redistribute the raw art | Yes |
| Attribution | Optional, but do it anyway |

Every pack ships its own `License.txt`; the full text of each is captured in
`catalog/packs.json` under the `license` field. All of them are CC0.

**Credit line to use:** `Art by Kenney (kenney.nl) — CC0`

---

## 2. LimeZu "Modern Interiors" — PAID, NOT REDISTRIBUTABLE

**Source:** https://limezu.itch.io/moderninteriors
**Lives at:** `Games/Last Take/assets/` (local only — never in this repo)

Full-version licence, verbatim:

> **YOU CAN:**
> - Edit and use the asset in any commercial or non commercial project
> - Use the asset in any commercial or non commercial project
>
> **YOU CAN'T:**
> - Resell or distribute the asset to others
> - Edit and resell the asset to others
>
> - Credits required (limezu.itch.io)

| | |
|---|---|
| Use in your own game | Yes, including commercially |
| Modify | Yes |
| **Redistribute the raw art** | **NO — this includes committing it to a public repo** |
| Attribution | **Required** — `limezu.itch.io` |

Only LimeZu **metadata** (file names, sizes, dimensions, counts) is catalogued
here, in `catalog/packs_limezu.json` and `catalog/files_limezu.jsonl`. Those
entries carry `"redistributable": false`. No LimeZu pixels are in this repo, and
`.gitignore` blocks the known paths as a safety net.

Shipping the art inside a game build is fine — that is normal use. Publishing the
pack itself, or a repo containing it, is not.

### The trap inside the trap

`Modern_Interiors_Free_v2.2` is a **different licence** from the full version:

> YOU CAN'T USE THE ASSET IN COMMERCIAL PROJECTS

The free tiles are **non-commercial only**. They sit in the same folder tree as
the paid full version and look identical. If a build might ever be sold or
monetised, source from `moderninteriors-win` (full version), never from
`Modern_Interiors_Free_v2.2`. Catalogue entries from that tree are marked
`"license_name": "... Free Version (NON-COMMERCIAL ONLY)"`.

---

## Rule of thumb

| Want to... | Kenney | LimeZu full | LimeZu free |
|---|---|---|---|
| Prototype locally | Yes | Yes | Yes |
| Ship a free game | Yes | Yes + credit | Yes |
| Ship a paid game | Yes | Yes + credit | **No** |
| Commit the art to a public repo | Yes | **No** | **No** |

When in doubt, reach for Kenney. It is CC0, it is 53,000 sprites deep, and it
carries no obligations at all.
