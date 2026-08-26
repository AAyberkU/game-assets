import sys; sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import os
import json
from PIL import Image

ASSETS_ROOT = "D:/Claude/Games/assets"
KENNEY_ROOT = ASSETS_ROOT + "/kenney"
SLICED_ROOT = ASSETS_ROOT + "/sliced"

JOBS = [
    {"tile": 16, "margin": 1, "path": "2D assets/Roguelike Base Pack/Spritesheet/roguelikeSheet_transparent.png"},
    {"tile": 16, "margin": 1, "path": "2D assets/Roguelike Characters Pack/Spritesheet/roguelikeChar_transparent.png"},
    {"tile": 16, "margin": 1, "path": "2D assets/Roguelike Dungeon Pack/Spritesheet/roguelikeDungeon_transparent.png"},
    {"tile": 16, "margin": 1, "path": "2D assets/Roguelike Interior Pack/Tilesheets/roguelikeIndoor_transparent.png"},
    {"tile": 16, "margin": 1, "path": "2D assets/Topdown Shooter (Pixel)/Tilesheet/tilesheet_transparent.png"},
    {"tile": 16, "margin": 1, "path": "2D assets/1-Bit Pack/Tilesheet/colored-transparent.png"},
    {"tile": 16, "margin": 1, "path": "2D assets/1-Bit Pack/Tilesheet/monochrome-transparent.png"},
    {"tile": 16, "margin": 2, "path": "UI assets/UI Pixel Pack/Spritesheet/UIpackSheet_transparent.png"},
]


def pack_name_from_rel(rel_path):
    # rel_path like "2D assets/Roguelike Base Pack/Spritesheet/roguelikeSheet_transparent.png"
    parts = rel_path.split("/")
    return parts[1]


def process_job(job):
    tile = job["tile"]
    margin = job["margin"]
    rel_path = job["path"]
    src_path = KENNEY_ROOT + "/" + rel_path

    pack = pack_name_from_rel(rel_path)
    sheet_filename = rel_path.split("/")[-1]
    sheet_name = os.path.splitext(sheet_filename)[0]

    img = Image.open(src_path).convert("RGBA")
    width, height = img.size

    step = tile + margin
    cols = (width + margin) // step
    rows = (height + margin) // step

    assert (cols - 1) * step + tile <= width, "cols do not fit within sheet width"
    assert (rows - 1) * step + tile <= height, "rows do not fit within sheet height"

    out_dir = SLICED_ROOT + "/" + pack + "/" + sheet_name
    os.makedirs(out_dir, exist_ok=True)

    # Remove any pre-existing tile PNGs in out_dir for idempotency
    for existing in os.listdir(out_dir):
        if existing.startswith("tile_") and existing.endswith(".png"):
            os.remove(os.path.join(out_dir, existing))

    tiles_total = cols * rows
    tiles_written = 0
    tiles_blank_skipped = 0

    index = 0
    for r in range(rows):
        for c in range(cols):
            left = c * step
            top = r * step
            right = left + tile
            bottom = top + tile
            crop = img.crop((left, top, right, bottom))

            alpha = crop.split()[3]
            if alpha.getextrema()[1] == 0:
                tiles_blank_skipped += 1
            else:
                out_path = out_dir + "/tile_" + str(index).zfill(4) + ".png"
                crop.save(out_path)
                tiles_written += 1
            index += 1

    rel_out_dir = out_dir[len(ASSETS_ROOT) + 1:].replace("\\", "/")
    rel_source = ("kenney/" + rel_path).replace("\\", "/")

    return {
        "source": rel_source,
        "pack": pack,
        "sheet": sheet_name,
        "tile": tile,
        "margin": margin,
        "sheet_width": width,
        "sheet_height": height,
        "cols": cols,
        "rows": rows,
        "tiles_total": tiles_total,
        "tiles_written": tiles_written,
        "tiles_blank_skipped": tiles_blank_skipped,
        "out_dir": rel_out_dir,
    }


def main():
    os.makedirs(SLICED_ROOT, exist_ok=True)

    manifest = []
    failures = []

    for job in JOBS:
        try:
            result = process_job(job)
            manifest.append(result)
            print("OK: " + job["path"])
        except Exception as e:
            failures.append((job["path"], str(e)))
            print("FAILED: " + job["path"] + " -- " + str(e))

    manifest_path = SLICED_ROOT + "/sliced_manifest.json"
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=True)

    print("")
    print("=== Per-sheet table ===")
    header = "{:<30} {:>6}x{:<4} {:>8} {:>8} {:>8}".format(
        "sheet", "cols", "rows", "total", "written", "blank")
    print(header)
    consistency_ok = True
    for m in manifest:
        line = "{:<30} {:>6}x{:<4} {:>8} {:>8} {:>8}".format(
            m["sheet"], m["cols"], m["rows"], m["tiles_total"],
            m["tiles_written"], m["tiles_blank_skipped"])
        print(line)
        if m["tiles_written"] + m["tiles_blank_skipped"] != m["tiles_total"]:
            consistency_ok = False
            print("  !! CONSISTENCY VIOLATION for " + m["sheet"])

    print("")
    if consistency_ok:
        print("Consistency check PASSED for all sheets: tiles_written + tiles_blank_skipped == tiles_total")
    else:
        print("Consistency check FAILED for one or more sheets (see above)")

    # Sanity check known case
    print("")
    print("=== Sanity check: 1-Bit Pack colored-transparent.png ===")
    sanity = None
    for m in manifest:
        if m["pack"] == "1-Bit Pack" and m["sheet"] == "colored-transparent":
            sanity = m
            break
    if sanity is None:
        print("SANITY CHECK FAILED: sheet not found in manifest")
    else:
        expected_w, expected_h = 832, 373
        expected_cols, expected_rows, expected_total = 49, 22, 1078
        ok = (sanity["sheet_width"] == expected_w and sanity["sheet_height"] == expected_h and
              sanity["cols"] == expected_cols and sanity["rows"] == expected_rows and
              sanity["tiles_total"] == expected_total)
        print("sheet_width={} sheet_height={} cols={} rows={} tiles_total={}".format(
            sanity["sheet_width"], sanity["sheet_height"], sanity["cols"], sanity["rows"], sanity["tiles_total"]))
        if ok:
            print("SANITY CHECK PASSED")
        else:
            print("SANITY CHECK FAILED: expected width={} height={} cols={} rows={} total={}".format(
                expected_w, expected_h, expected_cols, expected_rows, expected_total))

    print("")
    print("=== Failures ===")
    if failures:
        for path, err in failures:
            print("FAILED: " + path + " -- " + err)
    else:
        print("None")

    # Count files on disk
    disk_count = 0
    for root, dirs, files in os.walk(SLICED_ROOT):
        for fn in files:
            if fn.startswith("tile_") and fn.endswith(".png"):
                disk_count += 1

    total_written = sum(m["tiles_written"] for m in manifest)
    print("")
    print("=== Disk count check ===")
    print("Files on disk under sliced/: " + str(disk_count))
    print("Sum of tiles_written from manifest: " + str(total_written))
    if disk_count == total_written:
        print("DISK COUNT MATCHES manifest sum")
    else:
        print("DISK COUNT MISMATCH")


if __name__ == "__main__":
    main()
