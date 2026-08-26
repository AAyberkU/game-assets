"""Merge the mechanical pack scans with the vision-derived tags into one
master index: catalog/library.json

Inputs
  catalog/packs.json          - Kenney, mechanical (build_catalog.py)
  catalog/tags/batch_*.json   - Kenney, vision-derived tags (subagent pass)
  catalog/packs_limezu.json   - LimeZu, mechanical (build_catalog_limezu.py)

Output
  catalog/library.json        - one enriched entry per pack, both libraries
  catalog/library_summary.md  - human-readable rollup

Every join is checked. A pack that fails to pick up tags is REPORTED, never
silently emitted untagged.
"""
import glob
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = "D:/Claude/Games/assets"
CAT = ROOT + "/catalog"

TAG_FIELDS = (
    "description", "best_for", "perspective", "style", "color",
    "genres", "subjects", "tags", "usefulness",
)

# Controlled vocabularies the subagents were told to use. Anything outside these
# is a drift signal worth surfacing rather than quietly accepting.
VOCAB_PERSPECTIVE = {
    "top-down", "side-view", "isometric", "hexagonal", "first-person", "ui", "none",
}
VOCAB_STYLE = {
    "pixel-art", "vector-flat", "hand-drawn", "3d-render", "line-art",
    "monochrome", "photo",
}
VOCAB_GENRES = {
    "platformer", "shooter", "racing", "rpg", "roguelike", "tower-defense",
    "puzzle", "strategy", "survival", "sports", "board-game", "city-builder",
    "space", "horror", "sandbox", "card-game", "simulation", "arcade", "any",
}
VOCAB_SUBJECTS = {
    "characters", "enemies", "monsters", "animals", "vehicles", "ships",
    "aircraft", "buildings", "terrain", "tiles", "nature", "foliage", "items",
    "weapons", "food", "furniture", "ui", "icons", "effects", "particles",
    "fonts", "backgrounds", "props", "roads", "water", "space", "medieval",
    "sci-fi", "modern", "fantasy", "pirate", "western", "holiday", "abstract",
    "sound",
}

# LimeZu sub-packs are named structurally, not descriptively, so their entries are
# derived from the folder layout rather than from looking at art. Marked as such.
LIMEZU_SECTION_NOTES = {
    "1_Interiors": ("Interior floor, wall and furniture tiles plus room-builder sheets",
                    "Building modern indoor scenes room by room",
                    ["tiles", "furniture", "props", "buildings", "modern"]),
    "2_Characters": ("Modern-dress character sprites with walk cycles, plus a layered part generator",
                     "Populating a contemporary top-down scene with people",
                     ["characters", "modern"]),
    "3_Animated_objects": ("Looping animations for interactive props - doors, screens, appliances",
                           "Making an interior feel alive",
                           ["props", "effects", "modern"]),
    "4_User_Interface_Elements": ("Animated UI element spritesheets",
                                  "Diegetic interface bits in a pixel-art scene",
                                  ["ui", "modern"]),
    "6_Home_Designs": ("Pre-assembled example room and house layouts",
                       "Reference layouts, or drop-in prebuilt rooms",
                       ["buildings", "tiles", "modern"]),
    "Palettes": ("The pack's colour palette files",
                 "Matching new art to the pack's palette",
                 ["abstract"]),
    "RPG_Maker_Version": ("The same art repackaged to RPG Maker MV/MZ conventions",
                          "Only if targeting RPG Maker; redundant otherwise",
                          ["tiles", "characters", "modern"]),
    "Free_v2.2": ("Small free sample of the pack - NON-COMMERCIAL LICENCE ONLY",
                  "Nothing - prefer the full version, this one cannot ship commercially",
                  ["tiles", "modern"]),
    "_root": ("Licence and readme files", "Reference only", ["abstract"]),
}


def load_tags():
    """Load every tag batch, keyed by pack id. Reports duplicates and drift."""
    by_id = {}
    dupes = []
    drift = []
    paths = sorted(glob.glob(CAT + "/tags/batch_*.json"))
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            rows = json.load(fh)
        for row in rows:
            pid = row.get("id")
            if pid in by_id:
                dupes.append(pid)
                continue
            if row.get("perspective") not in VOCAB_PERSPECTIVE:
                drift.append((pid, "perspective", row.get("perspective")))
            if row.get("style") not in VOCAB_STYLE:
                drift.append((pid, "style", row.get("style")))
            for g in row.get("genres") or []:
                if g not in VOCAB_GENRES:
                    drift.append((pid, "genre", g))
            for s in row.get("subjects") or []:
                if s not in VOCAB_SUBJECTS:
                    drift.append((pid, "subject", s))
            by_id[pid] = row
    return by_id, paths, dupes, drift


def main():
    tags, tag_paths, dupes, drift = load_tags()
    print("tag batches loaded :", len(tag_paths), [os.path.basename(p) for p in tag_paths])
    print("tagged pack entries:", len(tags))
    if dupes:
        print("DUPLICATE tag ids  :", len(dupes), dupes[:10])
    if drift:
        print("VOCAB DRIFT        :", len(drift))
        for d in drift[:15]:
            print("   ", d)

    out = []

    # ---- Kenney ----
    kenney = json.load(open(CAT + "/packs.json", encoding="utf-8"))
    untagged = []
    for p in kenney:
        entry = dict(p)
        entry["library"] = "kenney"
        entry["license_name"] = "CC0 1.0 (public domain)"
        entry["redistributable"] = True
        entry["credit_required"] = None
        t = tags.get(p["id"])
        if t:
            for f in TAG_FIELDS:
                entry[f] = t.get(f)
            entry["tagged_by"] = "vision" if t.get("seen") else "name-inference"
        else:
            untagged.append(p["id"])
            for f in TAG_FIELDS:
                entry[f] = None
            entry["tagged_by"] = "none"
        out.append(entry)

    # ---- LimeZu (metadata only, structurally described) ----
    limezu_path = CAT + "/packs_limezu.json"
    limezu = []
    if os.path.isfile(limezu_path):
        limezu = json.load(open(limezu_path, encoding="utf-8"))
        for p in limezu:
            entry = dict(p)
            desc, best, subj = LIMEZU_SECTION_NOTES.get(
                p["section"],
                ("Modern Interiors pixel-art assets", "Contemporary top-down scenes", ["tiles", "modern"]),
            )
            size_hint = p["pack"] if p["pack"] in ("16x16", "32x32", "48x48") else ""
            entry["description"] = (desc + (" at " + size_hint if size_hint else ""))[:160]
            entry["best_for"] = best
            entry["perspective"] = "top-down"
            entry["style"] = "pixel-art"
            entry["color"] = "muted warm contemporary tones"
            entry["genres"] = ["rpg", "simulation"]
            entry["subjects"] = subj
            entry["tags"] = ["limezu", "modern-interiors", "cozy"]
            entry["usefulness"] = 2 if p["section"] == "Free_v2.2" else 4
            entry["tagged_by"] = "structural"
            out.append(entry)
    else:
        print("WARNING: packs_limezu.json not found - LimeZu library NOT merged")

    if untagged:
        print("UNTAGGED KENNEY PACKS:", len(untagged))
        for u in untagged[:20]:
            print("   ", u)
    else:
        print("untagged Kenney packs: 0")

    orphan_tags = sorted(set(tags) - {p["id"] for p in kenney})
    if orphan_tags:
        print("TAGS WITH NO MATCHING PACK:", len(orphan_tags), orphan_tags[:10])

    out.sort(key=lambda e: (e["library"], e["section"], e["pack"]))
    with open(CAT + "/library.json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=True)

    # ---- summary ----
    tot_files = sum(e["files"] for e in out)
    tot_bytes = sum(e["bytes"] for e in out)
    lines = []
    lines.append("# Asset library — master index\n")
    lines.append("Generated by `catalog/merge_catalog.py`. Do not hand-edit.\n")
    lines.append("| | count |")
    lines.append("|---|---|")
    lines.append("| packs | %d |" % len(out))
    lines.append("| files | %d |" % tot_files)
    lines.append("| size | %.1f MB |" % (tot_bytes / 1048576))
    lines.append("")
    lines.append("## By library\n")
    lines.append("| library | packs | files | MB | redistributable |")
    lines.append("|---|---|---|---|---|")
    for lib in sorted({e["library"] for e in out}):
        rows = [e for e in out if e["library"] == lib]
        lines.append("| %s | %d | %d | %.1f | %s |" % (
            lib, len(rows), sum(r["files"] for r in rows),
            sum(r["bytes"] for r in rows) / 1048576,
            "yes" if rows[0].get("redistributable") else "NO",
        ))
    lines.append("")
    lines.append("## By section\n")
    lines.append("| library | section | packs | files | MB |")
    lines.append("|---|---|---|---|---|")
    for lib in sorted({e["library"] for e in out}):
        for sec in sorted({e["section"] for e in out if e["library"] == lib}):
            rows = [e for e in out if e["library"] == lib and e["section"] == sec]
            lines.append("| %s | %s | %d | %d | %.1f |" % (
                lib, sec, len(rows), sum(r["files"] for r in rows),
                sum(r["bytes"] for r in rows) / 1048576))
    lines.append("")
    lines.append("## Most useful packs (usefulness 5)\n")
    top = [e for e in out if e.get("usefulness") == 5]
    top.sort(key=lambda e: -e["files"])
    lines.append("| pack | section | files | what it is |")
    lines.append("|---|---|---|---|")
    for e in top:
        lines.append("| %s | %s | %d | %s |" % (
            e["pack"], e["section"], e["files"], (e.get("description") or "")))
    lines.append("")

    with open(CAT + "/library_summary.md", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))

    print("")
    print("merged packs       :", len(out), "(kenney %d + limezu %d)" % (len(kenney), len(limezu)))
    print("total files        :", tot_files)
    print("total MB           : %.1f" % (tot_bytes / 1048576))
    print("usefulness==5 packs:", len(top))
    print("wrote              :", CAT + "/library.json")
    print("wrote              :", CAT + "/library_summary.md")


if __name__ == "__main__":
    main()
