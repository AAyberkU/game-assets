import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import struct
import time

ASSETS_ROOT = r"D:\Claude\Games\assets"
LIBRARY = "kenney"
LIB_ROOT = os.path.join(ASSETS_ROOT, LIBRARY)
CATALOG_DIR = os.path.join(ASSETS_ROOT, "catalog")
FILES_JSONL = os.path.join(CATALOG_DIR, "files.jsonl")
PACKS_JSON = os.path.join(CATALOG_DIR, "packs.json")
SUMMARY_MD = os.path.join(CATALOG_DIR, "summary.md")
ASSETS_JSON = os.path.join(LIB_ROOT, "assets.json")

REQUIRED_SECTIONS_TO_WAIT_FOR = ["Audio", "Archive"]
WAIT_INTERVAL_SEC = 60
WAIT_MAX_SEC = 15 * 60

MODEL_EXTS = {"fbx", "obj", "mtl", "glb", "stl", "dae", "gltf", "bin", "blend", "mat"}
AUDIO_EXTS = {"ogg", "wav", "mp3", "flac"}
FONT_EXTS = {"ttf", "otf", "woff", "woff2"}
VECTOR_EXTS = {"svg", "ai", "eps"}
DATA_EXTS = {"xml", "json", "tmx", "tsx", "txt", "html", "capx", "swf", "zip"}
SHEET_MARKERS = ("spritesheet", "sheet", "tilesheet", "tilemap", "tileset", "packed")

SKIP_EXTS = {"url"}
SKIP_NAMES_LOWER = {"thumbs.db"}


def wait_for_complete_tree():
    """Verify the tree looks complete before scanning; wait+recheck if section
    folders are missing, up to WAIT_MAX_SEC. Returns True if complete, False if
    still incomplete after the max wait (caller should label result PARTIAL)."""
    waited = 0
    while True:
        missing = [s for s in REQUIRED_SECTIONS_TO_WAIT_FOR
                   if not os.path.isdir(os.path.join(LIB_ROOT, s))]
        if not missing:
            return True
        if waited >= WAIT_MAX_SEC:
            print("WARNING: after {}s, still missing sections: {}".format(waited, missing))
            print("Proceeding with PARTIAL scan.")
            return False
        print("Waiting for extraction to complete; missing sections: {}. "
              "Rechecking in {}s (waited {}s so far)".format(missing, WAIT_INTERVAL_SEC, waited))
        time.sleep(WAIT_INTERVAL_SEC)
        waited += WAIT_INTERVAL_SEC


def load_kenney_metadata():
    """Returns (preview_by_pack_key, showcase_files_set) where pack_key is
    (section, pack_name) and showcase_files_set holds relative-to-LIB_ROOT
    forward-slash paths that Kenney's own metadata lists as pack files
    (used only for preview resolution; per spec we don't need a broader
    showcase flag on files.jsonl, only pack preview resolution)."""
    preview_by_pack = {}
    if not os.path.isfile(ASSETS_JSON):
        print("NOTE: assets.json not found at {}; proceeding without it.".format(ASSETS_JSON))
        return preview_by_pack
    try:
        with open(ASSETS_JSON, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except Exception as e:
        print("WARNING: failed to load assets.json ({}); proceeding without it.".format(e))
        return preview_by_pack

    categories = data.get("categories", [])
    for cat in categories:
        section_name = cat.get("name")
        for pack in cat.get("packs", []):
            pack_name = pack.get("name")
            preview = pack.get("preview")
            if section_name and pack_name and preview:
                preview_by_pack[(section_name, pack_name)] = preview.replace("\\", "/")
    return preview_by_pack


def classify_kind(rel_path_lower, name_lower, ext, sub_lower="", width=None, height=None):
    if ext in MODEL_EXTS:
        return "model"
    if ext in AUDIO_EXTS:
        return "audio"
    if ext in FONT_EXTS:
        return "font"
    if ext in VECTOR_EXTS:
        return "vector"
    if ext in DATA_EXTS:
        return "data"
    if ext == "png":
        if "preview" in rel_path_lower or name_lower == "preview" or name_lower == "sample":
            return "preview"
        # A sheet marker only counts if it appears in the FILE name or the
        # immediately-enclosing folder -- not anywhere in the path. Matching the
        # whole path made every file in a pack merely *named* "... Tileset"
        # (e.g. "Monochrome RPG Tileset") look like a spritesheet.
        leaf_dir = sub_lower.rsplit("/", 1)[-1] if sub_lower else ""
        marker_hit = any(m in name_lower for m in SHEET_MARKERS) or any(
            m in leaf_dir for m in SHEET_MARKERS
        )
        # An atlas is by definition bigger than a single tile. This keeps the
        # individual tile_0000.png files inside a "Tileset" pack as sprites.
        big_enough = width is None or width > 96 or height > 96
        if marker_hit and big_enough:
            return "sheet"
        return "sprite"
    return "other"


def read_png_dimensions(full_path):
    try:
        with open(full_path, "rb") as f:
            data = f.read(24)
        if len(data) < 24:
            return None, None
        if data[0:8] != b"\x89PNG\r\n\x1a\n":
            return None, None
        if data[12:16] != b"IHDR":
            return None, None
        width, height = struct.unpack(">II", data[16:24])
        return width, height
    except Exception:
        return None, None


def scan_files(read_failures):
    """Walk LIB_ROOT and yield file records (as dicts). Also populates
    read_failures list with (path, reason) for files that could not be
    processed (e.g. os.stat errors)."""
    records = []
    for section in sorted(os.listdir(LIB_ROOT)):
        section_path = os.path.join(LIB_ROOT, section)
        if not os.path.isdir(section_path):
            continue
        for dirpath, dirnames, filenames in os.walk(section_path):
            for fname in filenames:
                if fname.lower() in SKIP_NAMES_LOWER:
                    continue
                if fname.startswith("."):
                    continue
                _, dotext = os.path.splitext(fname)
                ext = dotext[1:].lower() if dotext else ""
                if ext in SKIP_EXTS:
                    continue

                full_path = os.path.join(dirpath, fname)
                try:
                    rel_to_lib = os.path.relpath(full_path, LIB_ROOT)
                    rel_to_lib_fwd = rel_to_lib.replace("\\", "/")
                    parts = rel_to_lib_fwd.split("/")
                    # parts[0] = section, parts[1] = pack, rest = sub-path (incl filename)
                    section_name = parts[0]
                    if len(parts) == 2:
                        # file sits directly under the section, with no pack folder
                        # (observed for a handful of loose files, e.g. Goodies/Thanks.txt,
                        # Archive/Readme.txt, Early access/Readme.txt). Use a synthetic
                        # pack bucket so these are still cataloged rather than dropped.
                        pack_name = "_loose"
                        sub = ""
                    else:
                        pack_name = parts[1]
                        remainder = parts[2:]  # includes filename as last element
                        sub_dirs = remainder[:-1]
                        sub = "/".join(sub_dirs)

                    name_no_ext = fname[:-(len(dotext))] if dotext else fname
                    rel_to_assets = os.path.relpath(full_path, ASSETS_ROOT).replace("\\", "/")

                    size_bytes = os.path.getsize(full_path)

                    rel_lower = rel_to_lib_fwd.lower()
                    name_lower = name_no_ext.lower()

                    width = None
                    height = None
                    if ext == "png":
                        width, height = read_png_dimensions(full_path)

                    # Classified AFTER dimensions are known -- the sheet-vs-sprite
                    # rule needs the image size to be reliable.
                    kind = classify_kind(
                        rel_lower, name_lower, ext, sub.lower(), width, height
                    )

                    records.append({
                        "path": rel_to_assets,
                        "library": LIBRARY,
                        "section": section_name,
                        "pack": pack_name,
                        "sub": sub,
                        "name": name_no_ext,
                        "ext": ext,
                        "bytes": size_bytes,
                        "kind": kind,
                        "width": width,
                        "height": height,
                    })
                except Exception as e:
                    read_failures.append((full_path, str(e)))
    return records


def build_packs(records, preview_by_pack, license_read_failures):
    packs = {}
    for rec in records:
        key = (rec["section"], rec["pack"])
        if key not in packs:
            packs[key] = {
                "id": "{}/{}".format(rec["section"], rec["pack"]),
                "pack": rec["pack"],
                "section": rec["section"],
                "library": LIBRARY,
                "path": "{}/{}/{}".format(LIBRARY, rec["section"], rec["pack"]),
                "preview": None,
                "files": 0,
                "bytes": 0,
                "kinds": {},
                "formats": set(),
                "subfolders": set(),
                "sprite_sizes_counter": {},
                "sheets": [],
                "license": None,
                "_first_preview_file": None,
            }
        p = packs[key]
        p["files"] += 1
        p["bytes"] += rec["bytes"]
        p["kinds"][rec["kind"]] = p["kinds"].get(rec["kind"], 0) + 1
        p["formats"].add(rec["ext"])
        if rec["sub"]:
            top_sub = rec["sub"].split("/")[0]
            p["subfolders"].add(top_sub)

        if rec["kind"] == "sprite" and rec["width"] is not None and rec["height"] is not None:
            size_key = "{}x{}".format(rec["width"], rec["height"])
            p["sprite_sizes_counter"][size_key] = p["sprite_sizes_counter"].get(size_key, 0) + 1

        if rec["kind"] == "sheet":
            p["sheets"].append({
                "path": rec["path"],
                "width": rec["width"],
                "height": rec["height"],
            })

        if rec["kind"] == "preview" and p["_first_preview_file"] is None:
            p["_first_preview_file"] = rec["path"]

    # finalize each pack
    pack_list = []
    for (section, pack_name), p in packs.items():
        # preview resolution: prefer assets.json, else first kind==preview file, else null
        preview_rel = preview_by_pack.get((section, pack_name))
        if preview_rel:
            p["preview"] = "{}/{}".format(LIBRARY, preview_rel)
        elif p["_first_preview_file"]:
            p["preview"] = p["_first_preview_file"]
        else:
            p["preview"] = None

        # sprite_sizes: top 6 most common, most common first
        sizes_sorted = sorted(p["sprite_sizes_counter"].items(), key=lambda kv: (-kv[1], kv[0]))
        p["sprite_sizes"] = [[k, v] for k, v in sizes_sorted[:6]]

        # sheets: up to 20, smallest-path-first (alphabetical sort of path)
        p["sheets"].sort(key=lambda s: s["path"])
        p["sheets"] = p["sheets"][:20]

        p["formats"] = sorted(p["formats"])
        p["subfolders"] = sorted(p["subfolders"])

        # license
        pack_dir = os.path.join(LIB_ROOT, section, pack_name)
        license_text = None
        try:
            for candidate in ("License.txt", "license.txt"):
                candidate_path = os.path.join(pack_dir, candidate)
                if os.path.isfile(candidate_path):
                    with open(candidate_path, "r", encoding="utf-8", errors="replace") as f:
                        license_text = f.read()
                    break
        except Exception as e:
            license_read_failures.append((os.path.join(pack_dir, "License.txt"), str(e)))
            license_text = None
        p["license"] = license_text

        del p["sprite_sizes_counter"]
        del p["_first_preview_file"]

        pack_list.append(p)

    pack_list.sort(key=lambda p: (p["section"], p["pack"]))
    return pack_list


def write_files_jsonl(records):
    with open(FILES_JSONL, "w", encoding="utf-8", newline="\n") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=True))
            f.write("\n")


def write_packs_json(pack_list):
    with open(PACKS_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(pack_list, f, indent=1, ensure_ascii=True)


def write_summary_md(records, pack_list, partial, read_failures, unreadable_png_count):
    total_packs = len(pack_list)
    total_files = len(records)
    total_bytes = sum(r["bytes"] for r in records)
    total_mb = total_bytes / (1024 * 1024)

    section_stats = {}
    for rec in records:
        s = section_stats.setdefault(rec["section"], {"packs": set(), "files": 0, "bytes": 0})
        s["packs"].add(rec["pack"])
        s["files"] += 1
        s["bytes"] += rec["bytes"]

    kind_stats = {}
    for rec in records:
        k = kind_stats.setdefault(rec["kind"], {"count": 0, "bytes": 0})
        k["count"] += 1
        k["bytes"] += rec["bytes"]

    lines = []
    lines.append("# Kenney Asset Library Catalog Summary")
    lines.append("")
    if partial:
        lines.append("**STATUS: PARTIAL** — required section folders were still missing after the max wait; "
                      "this summary reflects only what was present at scan time.")
        lines.append("")
    lines.append("- Total packs: {}".format(total_packs))
    lines.append("- Total files: {}".format(total_files))
    lines.append("- Total size: {:.2f} MB".format(total_mb))
    lines.append("- Read failures: {}".format(len(read_failures)))
    lines.append("- PNGs with unreadable dimensions: {}".format(unreadable_png_count))
    lines.append("")

    lines.append("## By Section")
    lines.append("")
    lines.append("| Section | Packs | Files | MB |")
    lines.append("|---|---|---|---|")
    for section in sorted(section_stats.keys()):
        s = section_stats[section]
        lines.append("| {} | {} | {} | {:.2f} |".format(
            section, len(s["packs"]), s["files"], s["bytes"] / (1024 * 1024)))
    lines.append("")

    lines.append("## By Kind")
    lines.append("")
    lines.append("| Kind | Count | MB |")
    lines.append("|---|---|---|")
    for kind in sorted(kind_stats.keys()):
        k = kind_stats[kind]
        lines.append("| {} | {} | {:.2f} |".format(kind, k["count"], k["bytes"] / (1024 * 1024)))
    lines.append("")

    with open(SUMMARY_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
        f.write("\n")


def main():
    os.makedirs(CATALOG_DIR, exist_ok=True)

    complete = wait_for_complete_tree()
    partial = not complete

    preview_by_pack = load_kenney_metadata()

    read_failures = []
    records = scan_files(read_failures)

    license_read_failures = []
    pack_list = build_packs(records, preview_by_pack, license_read_failures)

    write_files_jsonl(records)
    write_packs_json(pack_list)

    unreadable_png_count = sum(
        1 for r in records if r["ext"] == "png" and (r["width"] is None or r["height"] is None)
    )

    all_failures = read_failures + license_read_failures
    write_summary_md(records, pack_list, partial, all_failures, unreadable_png_count)

    print("Scan {}complete.".format("PARTIALLY " if partial else ""))
    print("Total files: {}".format(len(records)))
    print("Total packs: {}".format(len(pack_list)))
    print("Read failures: {}".format(len(all_failures)))
    if all_failures:
        print("First 10 failing paths:")
        for path, reason in all_failures[:10]:
            print("  {} -- {}".format(path, reason))
    print("Unreadable PNG dimensions: {}".format(unreadable_png_count))
    print("Wrote: {}".format(FILES_JSONL))
    print("Wrote: {}".format(PACKS_JSON))
    print("Wrote: {}".format(SUMMARY_MD))


if __name__ == "__main__":
    main()
