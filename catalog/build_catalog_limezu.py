import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import struct

CATALOG_DIR = "D:/Claude/Games/assets/catalog"
FILES_JSONL = CATALOG_DIR + "/files_limezu.jsonl"
PACKS_JSON = CATALOG_DIR + "/packs_limezu.json"
SUMMARY_MD = CATALOG_DIR + "/summary_limezu.md"

LAST_TAKE_ASSETS_DIR = "D:/Claude/Games/Last Take/assets"
LIBRARY = "limezu-modern-interiors"

FULL_LICENSE_NAME = "LimeZu Modern Interiors - Full Version"
FREE_LICENSE_NAME = "LimeZu Modern Interiors - Free Version (NON-COMMERCIAL ONLY)"
CREDIT_REQUIRED = "limezu.itch.io"

# Each tree describes one of the three source trees to catalog.
#   tree_root      : the folder directly under LAST_TAKE_ASSETS_DIR for this tree
#   scan_root      : the folder actually walked (peels a redundant single-subfolder
#                     wrapper if the whole tree_root contains nothing but one directory)
#   section_mode   : "dynamic" -> top-level folder under scan_root is the section
#                     "fixed"   -> section is a fixed string for the whole tree
#   fixed_section  : used when section_mode == "fixed"
#   license_name / redistributable / credit_required : per spec, constant per tree
TREES = [
    {
        "tree_root": LAST_TAKE_ASSETS_DIR + "/moderninteriors-win",
        "section_mode": "dynamic",
        "fixed_section": None,
        "license_name": FULL_LICENSE_NAME,
    },
    {
        "tree_root": LAST_TAKE_ASSETS_DIR + "/Modern_Interiors_RPG_Maker_Version",
        "section_mode": "fixed",
        "fixed_section": "RPG_Maker_Version",
        "license_name": FULL_LICENSE_NAME,
    },
    {
        "tree_root": LAST_TAKE_ASSETS_DIR + "/Modern_Interiors_Free_v2.2",
        "section_mode": "fixed",
        "fixed_section": "Free_v2.2",
        "license_name": FREE_LICENSE_NAME,
    },
]

MODEL_EXTS = {"fbx", "obj", "mtl", "glb", "stl", "dae", "gltf", "bin", "blend", "mat"}
AUDIO_EXTS = {"ogg", "wav", "mp3", "flac"}
FONT_EXTS = {"ttf", "otf", "woff", "woff2"}
VECTOR_EXTS = {"svg", "ai", "eps"}
DATA_EXTS = {"xml", "json", "tmx", "tsx", "txt", "html", "capx", "swf", "zip"}
SHEET_MARKERS = ("spritesheet", "sheet", "tilesheet", "tilemap", "tileset", "packed")

SKIP_EXTS = {"url"}
SKIP_NAMES_LOWER = {"thumbs.db"}

LICENSE_FILENAMES_LOWER = {"license.txt"}


def resolve_scan_root(tree_root):
    """Peel a redundant single-directory wrapper (folder whose only content is
    one subfolder, itself holding the real content) so 'pack = next segment
    down' lines up with the meaningful pack folders rather than the wrapper."""
    current = tree_root
    for _ in range(5):
        try:
            entries = os.listdir(current)
        except Exception:
            break
        if len(entries) != 1:
            break
        only = entries[0]
        only_path = os.path.join(current, only)
        if not os.path.isdir(only_path):
            break
        current = only_path
    return current


def classify_kind(rel_path_lower, name_lower, ext):
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
        if any(marker in rel_path_lower for marker in SHEET_MARKERS):
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


def derive_section_pack_sub(parts, section_mode, fixed_section):
    """parts = rel-to-scan-root path segments (including filename) as a list."""
    if section_mode == "dynamic":
        if len(parts) == 1:
            section = "_root"
            remainder = []
        else:
            section = parts[0]
            remainder = parts[1:]
    else:
        section = fixed_section
        remainder = parts

    if len(remainder) <= 1:
        pack = "_loose"
        sub = ""
    else:
        pack = remainder[0]
        sub = "/".join(remainder[1:-1])
    return section, pack, sub


def pack_dir_for(scan_root, section_mode, section, pack):
    if section_mode == "dynamic":
        if section == "_root":
            base = scan_root
        else:
            base = os.path.join(scan_root, section)
    else:
        base = scan_root

    if pack == "_loose":
        return base
    return os.path.join(base, pack)


def scan_tree(tree, read_failures):
    tree_root = tree["tree_root"]
    section_mode = tree["section_mode"]
    fixed_section = tree["fixed_section"]

    if not os.path.isdir(tree_root):
        print("WARNING: tree root not found, skipping: {}".format(tree_root))
        return []

    scan_root = resolve_scan_root(tree_root)

    records = []
    for dirpath, dirnames, filenames in os.walk(scan_root):
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
                rel_to_scan = os.path.relpath(full_path, scan_root).replace("\\", "/")
                parts = rel_to_scan.split("/")

                section, pack, sub = derive_section_pack_sub(parts, section_mode, fixed_section)
                pdir = pack_dir_for(scan_root, section_mode, section, pack)

                name_no_ext = fname[:-(len(dotext))] if dotext else fname
                rel_to_assets = os.path.relpath(full_path, LAST_TAKE_ASSETS_DIR).replace("\\", "/")
                path_field = "last-take-assets/" + rel_to_assets

                size_bytes = os.path.getsize(full_path)

                rel_lower = rel_to_scan.lower()
                name_lower = name_no_ext.lower()
                kind = classify_kind(rel_lower, name_lower, ext)

                width = None
                height = None
                if ext == "png":
                    width, height = read_png_dimensions(full_path)

                records.append({
                    "path": path_field,
                    "library": LIBRARY,
                    "section": section,
                    "pack": pack,
                    "sub": sub,
                    "name": name_no_ext,
                    "ext": ext,
                    "bytes": size_bytes,
                    "kind": kind,
                    "width": width,
                    "height": height,
                    "_tree_root": tree_root,
                    "_pack_dir": pdir,
                    "_license_name": tree["license_name"],
                })
            except Exception as e:
                read_failures.append((full_path, str(e)))
    return records


PUBLIC_FILE_FIELDS = ("path", "library", "section", "pack", "sub", "name", "ext",
                       "bytes", "kind", "width", "height")


def find_license_text(pack_dir, tree_root, license_read_failures):
    current = pack_dir
    for _ in range(50):
        try:
            entries = os.listdir(current)
        except Exception as e:
            license_read_failures.append((current, str(e)))
            entries = []
        for entry in entries:
            if entry.lower() in LICENSE_FILENAMES_LOWER:
                candidate_path = os.path.join(current, entry)
                try:
                    with open(candidate_path, "r", encoding="utf-8", errors="replace") as f:
                        return f.read()
                except Exception as e:
                    license_read_failures.append((candidate_path, str(e)))
        if os.path.normcase(os.path.normpath(current)) == os.path.normcase(os.path.normpath(tree_root)):
            break
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def build_packs(records, license_read_failures):
    packs = {}
    for rec in records:
        key = (rec["section"], rec["pack"])
        if key not in packs:
            packs[key] = {
                "id": "{}/{}".format(rec["section"], rec["pack"]),
                "pack": rec["pack"],
                "section": rec["section"],
                "library": LIBRARY,
                "path": "last-take-assets/" + os.path.relpath(
                    rec["_pack_dir"], LAST_TAKE_ASSETS_DIR).replace("\\", "/"),
                "preview": None,
                "files": 0,
                "bytes": 0,
                "kinds": {},
                "formats": set(),
                "subfolders": set(),
                "sprite_sizes_counter": {},
                "sheets": [],
                "license": None,
                "redistributable": False,
                "license_name": rec["_license_name"],
                "credit_required": CREDIT_REQUIRED,
                "_first_preview_file": None,
                "_pack_dir": rec["_pack_dir"],
                "_tree_root": rec["_tree_root"],
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

    pack_list = []
    for (section, pack_name), p in packs.items():
        if p["_first_preview_file"]:
            p["preview"] = p["_first_preview_file"]
        else:
            p["preview"] = None

        sizes_sorted = sorted(p["sprite_sizes_counter"].items(), key=lambda kv: (-kv[1], kv[0]))
        p["sprite_sizes"] = [[k, v] for k, v in sizes_sorted[:6]]

        p["sheets"].sort(key=lambda s: s["path"])
        p["sheets"] = p["sheets"][:20]

        p["formats"] = sorted(p["formats"])
        p["subfolders"] = sorted(p["subfolders"])

        p["license"] = find_license_text(p["_pack_dir"], p["_tree_root"], license_read_failures)

        del p["sprite_sizes_counter"]
        del p["_first_preview_file"]
        del p["_pack_dir"]
        del p["_tree_root"]

        pack_list.append(p)

    pack_list.sort(key=lambda p: (p["section"], p["pack"]))
    return pack_list


def write_files_jsonl(records):
    with open(FILES_JSONL, "w", encoding="utf-8", newline="\n") as f:
        for rec in records:
            public_rec = {k: rec[k] for k in PUBLIC_FILE_FIELDS}
            f.write(json.dumps(public_rec, ensure_ascii=True))
            f.write("\n")


def write_packs_json(pack_list):
    with open(PACKS_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(pack_list, f, indent=1, ensure_ascii=True)


def write_summary_md(records, pack_list, read_failures, unreadable_png_count):
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
    lines.append("# LimeZu Modern Interiors Asset Library Catalog Summary")
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

    lines.append("## Licensing")
    lines.append("")
    lines.append("This library (LimeZu Modern Interiors) is a PAID, NON-REDISTRIBUTABLE asset. "
                  "Only metadata is cataloged here; no art files are copied or bundled.")
    lines.append("")
    lines.append("**WARNING: the `Free_v2.2` section (tree C, Modern_Interiors_Free_v2.2) is "
                  "NON-COMMERCIAL ONLY and must NOT ship in a commercial build.**")
    lines.append("")

    with open(SUMMARY_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
        f.write("\n")


def main():
    os.makedirs(CATALOG_DIR, exist_ok=True)

    read_failures = []
    all_records = []
    for tree in TREES:
        all_records.extend(scan_tree(tree, read_failures))

    license_read_failures = []
    pack_list = build_packs(all_records, license_read_failures)

    write_files_jsonl(all_records)
    write_packs_json(pack_list)

    unreadable_png_count = sum(
        1 for r in all_records if r["ext"] == "png" and (r["width"] is None or r["height"] is None)
    )

    all_failures = read_failures + license_read_failures
    write_summary_md(all_records, pack_list, all_failures, unreadable_png_count)

    print("Scan complete.")
    print("Total files: {}".format(len(all_records)))
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
