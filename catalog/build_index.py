import sys; sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import json
import os
import re

CATALOG_DIR = os.path.dirname(os.path.abspath(__file__))
LIBRARY_JSON = os.path.join(CATALOG_DIR, 'library.json')
OUTPUT_HTML = os.path.join(CATALOG_DIR, 'index.html')
PREVIEWS_DIR = os.path.join(CATALOG_DIR, 'previews')


def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def build_records(packs):
    records = []
    for p in packs:
        section_slug = slugify(p.get('section') or '')
        pack_slug = slugify(p.get('pack') or '')
        rel_thumb = f'previews/{section_slug}/{pack_slug}.png'
        abs_thumb = os.path.join(PREVIEWS_DIR, section_slug, pack_slug + '.png')
        thumb = rel_thumb if os.path.isfile(abs_thumb) else None

        sprite_sizes = p.get('sprite_sizes') or []
        main_sprite_size = None
        if sprite_sizes:
            main_sprite_size = max(sprite_sizes, key=lambda s: s[1])[0]

        sheet_dims = []
        seen_dims = set()
        for sheet in (p.get('sheets') or []):
            dim = f"{sheet.get('width')}x{sheet.get('height')}"
            if dim not in seen_dims:
                seen_dims.add(dim)
                sheet_dims.append(dim)

        records.append({
            'id': p.get('id'),
            'pack': p.get('pack'),
            'section': p.get('section'),
            'library': p.get('library'),
            'path': p.get('path'),
            'thumb': thumb,
            'files': p.get('files'),
            'bytes': p.get('bytes'),
            'kinds': p.get('kinds') or {},
            'formats': p.get('formats') or [],
            'subfolders': p.get('subfolders') or [],
            'sprite_sizes': sprite_sizes,
            'main_sprite_size': main_sprite_size,
            'sheet_dims': sheet_dims,
            'description': p.get('description') or '',
            'best_for': p.get('best_for') or '',
            'perspective': p.get('perspective') or '',
            'style': p.get('style') or '',
            'color': p.get('color') or '',
            'genres': p.get('genres') or [],
            'subjects': p.get('subjects') or [],
            'tags': p.get('tags') or [],
            'usefulness': p.get('usefulness'),
            'tagged_by': p.get('tagged_by'),
            'license_name': p.get('license_name'),
            'redistributable': p.get('redistributable'),
            'credit_required': p.get('credit_required'),
        })
    return records


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Game Art Asset Catalog</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  :root {
    --bg: #1c1d20;
    --panel: #26282c;
    --panel-2: #2f3136;
    --border: #3a3d42;
    --text: #e6e6e8;
    --text-dim: #9a9da3;
    --accent: #6fa8ff;
    --cc0: #4caf7d;
    --warn-bg: #3a1414;
    --warn-border: #d9453f;
    --warn-text: #ff9b95;
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0;
    background: var(--bg);
    color: var(--text);
    font-family: Segoe UI, Tahoma, Arial, sans-serif;
    font-size: 14px;
  }
  header {
    padding: 16px 20px 12px 20px;
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    background: var(--bg);
    z-index: 20;
  }
  h1 {
    margin: 0 0 4px 0;
    font-size: 20px;
    font-weight: 600;
  }
  .subtitle {
    color: var(--text-dim);
    font-size: 12px;
    margin-bottom: 12px;
  }
  .controls {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }
  .controls input[type="text"],
  .controls select {
    background: var(--panel);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 13px;
  }
  .controls input[type="text"] {
    min-width: 220px;
    flex-grow: 1;
  }
  .controls select[multiple] {
    height: 32px;
    min-width: 130px;
  }
  .controls label {
    display: flex;
    flex-direction: column;
    gap: 2px;
    font-size: 11px;
    color: var(--text-dim);
  }
  #resetBtn {
    background: var(--panel-2);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 7px 12px;
    font-size: 13px;
    cursor: pointer;
    align-self: flex-end;
  }
  #resetBtn:hover { background: var(--border); }
  #count {
    color: var(--text-dim);
    font-size: 12px;
    margin-left: auto;
    align-self: flex-end;
    white-space: nowrap;
  }
  main {
    padding: 16px 20px 40px 20px;
  }
  #grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
    gap: 14px;
  }
  .card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
    cursor: pointer;
    display: flex;
    flex-direction: column;
  }
  .card:hover { border-color: var(--accent); }
  .card.non-redist {
    border: 2px solid var(--warn-border);
  }
  .thumb {
    position: relative;
    width: 100%;
    aspect-ratio: 4 / 3;
    background-color: #2a2a2a;
    background-image:
      linear-gradient(45deg, #333 25%, transparent 25%),
      linear-gradient(-45deg, #333 25%, transparent 25%),
      linear-gradient(45deg, transparent 75%, #333 75%),
      linear-gradient(-45deg, transparent 75%, #333 75%);
    background-size: 16px 16px;
    background-position: 0 0, 0 8px, 8px -8px, -8px 0px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }
  .thumb img {
    max-width: 100%;
    max-height: 100%;
    image-rendering: pixelated;
  }
  .thumb .placeholder {
    color: var(--text-dim);
    font-size: 11px;
    text-align: center;
    padding: 8px;
  }
  .ribbon {
    position: absolute;
    top: 0; left: 0; right: 0;
    background: var(--warn-bg);
    color: var(--warn-text);
    font-size: 10px;
    font-weight: 700;
    text-align: center;
    padding: 3px 4px;
    letter-spacing: 0.3px;
    border-bottom: 1px solid var(--warn-border);
  }
  .badge-cc0 {
    position: absolute;
    bottom: 4px;
    right: 4px;
    background: rgba(76, 175, 125, 0.85);
    color: #0c1f14;
    font-size: 10px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 3px;
  }
  .card-body {
    padding: 8px 10px 10px 10px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex-grow: 1;
  }
  .card-title {
    font-weight: 600;
    font-size: 13.5px;
    line-height: 1.3;
  }
  .card-meta {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: var(--text-dim);
  }
  .pill {
    display: inline-block;
    background: var(--panel-2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1px 7px;
    font-size: 10.5px;
    color: var(--text-dim);
  }
  .useful-dots { letter-spacing: 1px; color: var(--accent); font-size: 12px; }
  .useful-dots .off { color: var(--border); }
  .card-desc {
    font-size: 11.5px;
    color: var(--text-dim);
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .card-footer {
    margin-top: auto;
    display: flex;
    justify-content: space-between;
    font-size: 10.5px;
    color: var(--text-dim);
    border-top: 1px solid var(--border);
    padding-top: 6px;
  }

  #overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.6);
    z-index: 100;
    align-items: flex-start;
    justify-content: center;
    overflow-y: auto;
    padding: 40px 16px;
  }
  #overlay.open { display: flex; }
  #modal {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    max-width: 720px;
    width: 100%;
    padding: 20px 24px 24px 24px;
    position: relative;
  }
  #modal.non-redist {
    border: 2px solid var(--warn-border);
  }
  #modalClose {
    position: absolute;
    top: 10px; right: 12px;
    background: none;
    border: none;
    color: var(--text-dim);
    font-size: 20px;
    cursor: pointer;
    line-height: 1;
  }
  #modalClose:hover { color: var(--text); }
  .modal-warning {
    background: var(--warn-bg);
    border: 1px solid var(--warn-border);
    color: var(--warn-text);
    border-radius: 4px;
    padding: 8px 10px;
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 12px;
  }
  .modal-cc0 {
    display: inline-block;
    background: rgba(76, 175, 125, 0.18);
    border: 1px solid var(--cc0);
    color: var(--cc0);
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 700;
    margin-bottom: 12px;
  }
  #modalThumb {
    width: 100%;
    max-height: 260px;
    aspect-ratio: 16 / 9;
    background-color: #2a2a2a;
    background-image:
      linear-gradient(45deg, #333 25%, transparent 25%),
      linear-gradient(-45deg, #333 25%, transparent 25%),
      linear-gradient(45deg, transparent 75%, #333 75%),
      linear-gradient(-45deg, transparent 75%, #333 75%);
    background-size: 16px 16px;
    background-position: 0 0, 0 8px, 8px -8px, -8px 0px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    border-radius: 4px;
    margin-bottom: 14px;
  }
  #modalThumb img { max-width: 100%; max-height: 260px; image-rendering: pixelated; }
  #modalTitle { font-size: 18px; font-weight: 700; margin: 0 0 2px 0; }
  #modalSub { color: var(--text-dim); font-size: 12px; margin-bottom: 14px; }
  .detail-grid {
    display: grid;
    grid-template-columns: 140px 1fr;
    gap: 6px 12px;
    font-size: 12.5px;
  }
  .detail-grid dt { color: var(--text-dim); }
  .detail-grid dd { margin: 0; word-break: break-word; }
  .tag-list { display: flex; flex-wrap: wrap; gap: 5px; }
</style>
</head>
<body>
<header>
  <h1>Game Art Asset Catalog</h1>
  <div class="subtitle" id="subtitle">__TOTAL__ packs</div>
  <div class="controls">
    <label>Search
      <input type="text" id="searchBox" placeholder="name, description, tags...">
    </label>
    <label>Library
      <select id="libraryFilter"><option value="">All</option></select>
    </label>
    <label>Section
      <select id="sectionFilter"><option value="">All</option></select>
    </label>
    <label>Perspective
      <select id="perspectiveFilter"><option value="">All</option></select>
    </label>
    <label>Style
      <select id="styleFilter"><option value="">All</option></select>
    </label>
    <label>Usefulness
      <select id="usefulnessFilter"><option value="">All</option></select>
    </label>
    <label>Genre
      <select id="genreFilter" multiple></select>
    </label>
    <label>Subject
      <select id="subjectFilter" multiple></select>
    </label>
    <label>Sort
      <select id="sortFilter">
        <option value="usefulness_desc">Usefulness (high to low)</option>
        <option value="name_asc">Pack name (A-Z)</option>
        <option value="files_desc">File count (high to low)</option>
      </select>
    </label>
    <button id="resetBtn">Reset filters</button>
    <div id="count"></div>
  </div>
</header>
<main>
  <div id="grid"></div>
</main>

<div id="overlay">
  <div id="modal">
    <button id="modalClose" aria-label="Close">&times;</button>
    <div id="modalBody"></div>
  </div>
</div>

<script type="application/json" id="catalog-data">__DATA_JSON__</script>
<script>
(function () {
  "use strict";

  var DATA = JSON.parse(document.getElementById('catalog-data').textContent);
  var TOTAL = DATA.length;

  function escapeHtml(s) {
    if (s === null || s === undefined) return '';
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function uniqueSorted(values) {
    var seen = {};
    var out = [];
    values.forEach(function (v) {
      if (v === null || v === undefined || v === '') return;
      if (!seen[v]) { seen[v] = true; out.push(v); }
    });
    out.sort();
    return out;
  }

  function fillSelect(select, values, isMultiple) {
    values.forEach(function (v) {
      var opt = document.createElement('option');
      opt.value = v;
      opt.textContent = v;
      select.appendChild(opt);
    });
  }

  var libraryFilter = document.getElementById('libraryFilter');
  var sectionFilter = document.getElementById('sectionFilter');
  var perspectiveFilter = document.getElementById('perspectiveFilter');
  var styleFilter = document.getElementById('styleFilter');
  var usefulnessFilter = document.getElementById('usefulnessFilter');
  var genreFilter = document.getElementById('genreFilter');
  var subjectFilter = document.getElementById('subjectFilter');
  var sortFilter = document.getElementById('sortFilter');
  var searchBox = document.getElementById('searchBox');
  var resetBtn = document.getElementById('resetBtn');
  var countEl = document.getElementById('count');
  var grid = document.getElementById('grid');

  fillSelect(libraryFilter, uniqueSorted(DATA.map(function (d) { return d.library; })));
  fillSelect(sectionFilter, uniqueSorted(DATA.map(function (d) { return d.section; })));
  fillSelect(perspectiveFilter, uniqueSorted(DATA.map(function (d) { return d.perspective; })));
  fillSelect(styleFilter, uniqueSorted(DATA.map(function (d) { return d.style; })));
  fillSelect(usefulnessFilter, uniqueSorted(DATA.map(function (d) { return d.usefulness; })).sort(function(a,b){return b-a;}));

  var genreValues = [];
  DATA.forEach(function (d) { genreValues = genreValues.concat(d.genres || []); });
  fillSelect(genreFilter, uniqueSorted(genreValues));

  var subjectValues = [];
  DATA.forEach(function (d) { subjectValues = subjectValues.concat(d.subjects || []); });
  fillSelect(subjectFilter, uniqueSorted(subjectValues));

  function selectedValues(select) {
    var out = [];
    for (var i = 0; i < select.options.length; i++) {
      if (select.options[i].selected) out.push(select.options[i].value);
    }
    return out;
  }

  function usefulnessDots(n) {
    var v = n || 0;
    var out = '';
    for (var i = 1; i <= 5; i++) {
      out += i <= v ? '●' : '<span class="off">●</span>';
    }
    return out;
  }

  function cardHtml(d) {
    var isBad = d.redistributable === false;
    var isCC0 = (d.license_name || '').indexOf('CC0') !== -1;
    var thumbInner;
    if (d.thumb) {
      thumbInner = '<img src="' + escapeHtml(d.thumb) + '" alt="' + escapeHtml(d.pack) + '" loading="lazy" decoding="async">';
    } else {
      thumbInner = '<div class="placeholder">no preview</div>';
    }
    var ribbon = isBad ? '<div class="ribbon">NOT REDISTRIBUTABLE</div>' : '';
    var cc0badge = (!isBad && isCC0) ? '<div class="badge-cc0">CC0</div>' : '';
    var spriteInfo = d.main_sprite_size ? ('<span class="pill">' + escapeHtml(d.main_sprite_size) + '</span>') : '';

    return (
      '<div class="card' + (isBad ? ' non-redist' : '') + '" data-id="' + escapeHtml(d.id) + '">' +
        '<div class="thumb">' + ribbon + thumbInner + cc0badge + '</div>' +
        '<div class="card-body">' +
          '<div class="card-title">' + escapeHtml(d.pack) + '</div>' +
          '<div class="card-meta"><span class="pill">' + escapeHtml(d.section) + '</span>' +
            '<span class="useful-dots">' + usefulnessDots(d.usefulness) + '</span></div>' +
          '<div class="card-desc">' + escapeHtml(d.description) + '</div>' +
          '<div class="card-footer"><span>' + (d.files || 0) + ' files</span>' + spriteInfo + '</div>' +
        '</div>' +
      '</div>'
    );
  }

  function pillList(values) {
    if (!values || !values.length) return '<em>none</em>';
    return '<div class="tag-list">' + values.map(function (v) {
      return '<span class="pill">' + escapeHtml(v) + '</span>';
    }).join('') + '</div>';
  }

  function modalHtml(d) {
    var isBad = d.redistributable === false;
    var isCC0 = (d.license_name || '').indexOf('CC0') !== -1;
    var warning = isBad
      ? '<div class="modal-warning">NOT REDISTRIBUTABLE &mdash; do not commit this art. Credit required: ' + escapeHtml(d.credit_required || 'see license') + '</div>'
      : (isCC0 ? '<div class="modal-cc0">CC0 &mdash; free to use, credit not required</div>' : '');
    var thumbInner = d.thumb
      ? '<img src="' + escapeHtml(d.thumb) + '" alt="' + escapeHtml(d.pack) + '">'
      : '<div class="placeholder">no preview</div>';

    var sheetDims = (d.sheet_dims && d.sheet_dims.length) ? d.sheet_dims.join(', ') : 'none';
    var spriteSizes = (d.sprite_sizes && d.sprite_sizes.length)
      ? d.sprite_sizes.map(function (s) { return s[0] + ' (' + s[1] + ')'; }).join(', ')
      : 'none';

    return (
      warning +
      '<div id="modalThumb">' + thumbInner + '</div>' +
      '<h2 id="modalTitle">' + escapeHtml(d.pack) + '</h2>' +
      '<div id="modalSub">' + escapeHtml(d.section) + ' &middot; ' + escapeHtml(d.library) + ' &middot; ' +
        usefulnessDots(d.usefulness) + '</div>' +
      '<dl class="detail-grid">' +
        '<dt>Description</dt><dd>' + escapeHtml(d.description) + '</dd>' +
        '<dt>Best for</dt><dd>' + escapeHtml(d.best_for) + '</dd>' +
        '<dt>Perspective</dt><dd>' + escapeHtml(d.perspective) + '</dd>' +
        '<dt>Style</dt><dd>' + escapeHtml(d.style) + '</dd>' +
        '<dt>Color</dt><dd>' + escapeHtml(d.color) + '</dd>' +
        '<dt>Genres</dt><dd>' + pillList(d.genres) + '</dd>' +
        '<dt>Subjects</dt><dd>' + pillList(d.subjects) + '</dd>' +
        '<dt>Tags</dt><dd>' + pillList(d.tags) + '</dd>' +
        '<dt>Formats</dt><dd>' + pillList(d.formats) + '</dd>' +
        '<dt>Subfolders</dt><dd>' + pillList(d.subfolders) + '</dd>' +
        '<dt>Sprite sizes</dt><dd>' + escapeHtml(spriteSizes) + '</dd>' +
        '<dt>Sheet dimensions</dt><dd>' + escapeHtml(sheetDims) + '</dd>' +
        '<dt>Files / bytes</dt><dd>' + (d.files || 0) + ' files, ' + Math.round((d.bytes || 0) / 1024) + ' KB</dd>' +
        '<dt>On-disk path</dt><dd>' + escapeHtml(d.path) + '</dd>' +
        '<dt>Licence</dt><dd>' + escapeHtml(d.license_name) + '</dd>' +
      '</dl>'
    );
  }

  var overlay = document.getElementById('overlay');
  var modal = document.getElementById('modal');
  var modalBody = document.getElementById('modalBody');
  var modalClose = document.getElementById('modalClose');

  function openModal(d) {
    modalBody.innerHTML = modalHtml(d);
    modal.className = d.redistributable === false ? 'non-redist' : '';
    overlay.className = 'open';
  }
  function closeModal() {
    overlay.className = '';
  }
  modalClose.addEventListener('click', closeModal);
  overlay.addEventListener('click', function (e) {
    if (e.target === overlay) closeModal();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeModal();
  });

  var byId = {};
  DATA.forEach(function (d) { byId[d.id] = d; });

  grid.addEventListener('click', function (e) {
    var card = e.target.closest('.card');
    if (!card) return;
    var d = byId[card.getAttribute('data-id')];
    if (d) openModal(d);
  });

  function matches(d, f) {
    if (f.library && d.library !== f.library) return false;
    if (f.section && d.section !== f.section) return false;
    if (f.perspective && d.perspective !== f.perspective) return false;
    if (f.style && d.style !== f.style) return false;
    if (f.usefulness && String(d.usefulness) !== f.usefulness) return false;
    if (f.genres.length) {
      var g = d.genres || [];
      if (!f.genres.some(function (x) { return g.indexOf(x) !== -1; })) return false;
    }
    if (f.subjects.length) {
      var s = d.subjects || [];
      if (!f.subjects.some(function (x) { return s.indexOf(x) !== -1; })) return false;
    }
    if (f.q) {
      var haystack = (
        (d.pack || '') + ' ' +
        (d.description || '') + ' ' +
        (d.best_for || '') + ' ' +
        (d.tags || []).join(' ') + ' ' +
        (d.subjects || []).join(' ')
      ).toLowerCase();
      if (haystack.indexOf(f.q) === -1) return false;
    }
    return true;
  }

  function sortRecords(list, mode) {
    var out = list.slice();
    if (mode === 'name_asc') {
      out.sort(function (a, b) { return (a.pack || '').localeCompare(b.pack || ''); });
    } else if (mode === 'files_desc') {
      out.sort(function (a, b) { return (b.files || 0) - (a.files || 0); });
    } else {
      out.sort(function (a, b) { return (b.usefulness || 0) - (a.usefulness || 0); });
    }
    return out;
  }

  function render() {
    var f = {
      library: libraryFilter.value,
      section: sectionFilter.value,
      perspective: perspectiveFilter.value,
      style: styleFilter.value,
      usefulness: usefulnessFilter.value,
      genres: selectedValues(genreFilter),
      subjects: selectedValues(subjectFilter),
      q: searchBox.value.trim().toLowerCase()
    };
    var filtered = DATA.filter(function (d) { return matches(d, f); });
    filtered = sortRecords(filtered, sortFilter.value);
    grid.innerHTML = filtered.map(cardHtml).join('');
    countEl.textContent = 'Showing ' + filtered.length + ' of ' + TOTAL + ' packs';
  }

  [libraryFilter, sectionFilter, perspectiveFilter, styleFilter, usefulnessFilter, genreFilter, subjectFilter, sortFilter]
    .forEach(function (el) { el.addEventListener('change', render); });
  searchBox.addEventListener('input', render);

  resetBtn.addEventListener('click', function () {
    libraryFilter.value = '';
    sectionFilter.value = '';
    perspectiveFilter.value = '';
    styleFilter.value = '';
    usefulnessFilter.value = '';
    searchBox.value = '';
    Array.prototype.forEach.call(genreFilter.options, function (o) { o.selected = false; });
    Array.prototype.forEach.call(subjectFilter.options, function (o) { o.selected = false; });
    sortFilter.value = 'usefulness_desc';
    render();
  });

  render();
})();
</script>
</body>
</html>
"""


def main():
    with open(LIBRARY_JSON, encoding='utf-8') as f:
        packs = json.load(f)

    records = build_records(packs)

    data_json = json.dumps(records, ensure_ascii=True)
    data_json = data_json.replace('</', '<\\/')

    html = PAGE_TEMPLATE.replace('__DATA_JSON__', data_json)
    html = html.replace('__TOTAL__', str(len(records)))

    with open(OUTPUT_HTML, 'w', encoding='utf-8', newline='\n') as f:
        f.write(html)

    print('Wrote', OUTPUT_HTML)
    print('Records embedded:', len(records))
    print('Output bytes:', os.path.getsize(OUTPUT_HTML))


if __name__ == '__main__':
    main()
