"""Proof of concept: extract metadata and lyrics from MuseScore-exported PDFs.

MuseScore draws notation with a SMuFL music font (Leland, Bravura, ...) whose glyphs
live in the Unicode Private Use Area, and draws lyric hyphens / melisma extenders as
vector lines rather than text. Lyrics are rebuilt by taking the text spans in the
lyric style, grouping them into rows per system, and joining syllables that have a
hyphen line between them.

Usage: python extract_lyrics.py file.pdf [file2.pdf ...] [--json]
"""
import json
import sys
import unicodedata
from collections import Counter

import pymupdf


def is_music_glyphs(text):
    return any(0xE000 <= ord(ch) <= 0xF8FF for ch in text)


def _piece(chars, span, page):
    return {
        "text": unicodedata.normalize("NFKC", "".join(c["c"] for c in chars)),
        "font": span["font"],
        "size": round(span["size"], 1),
        "x0": chars[0]["bbox"][0],
        "x1": chars[-1]["bbox"][2],
        "y": round(span["origin"][1], 1),
        "page": page.number,
    }


def text_spans(page, split_words):
    """Yield non-music text spans; with split_words, split them at spaces into words/syllables,
    since PyMuPDF merges closely spaced syllables (e.g. "par take") into one span."""
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            for s in line["spans"]:
                chars = s["chars"]
                text = "".join(c["c"] for c in chars)
                if not text.strip() or is_music_glyphs(text):
                    continue
                if not split_words:
                    stripped = [c for c in chars if not c["c"].isspace()]
                    yield {**_piece(chars, s, page), "text": unicodedata.normalize("NFKC", text.strip()),
                           "x0": stripped[0]["bbox"][0], "x1": stripped[-1]["bbox"][2]}
                    continue
                cur = []
                for c in chars + [{"c": " "}]:
                    if c["c"].isspace():
                        if cur:
                            yield _piece(cur, s, page)
                        cur = []
                    else:
                        cur.append(c)


def horizontal_lines(page):
    """Thin horizontal vector segments (staff lines, hyphens, extenders)."""
    out = []
    for dr in page.get_drawings():
        r = dr["rect"]
        if r.height < 1.5 and r.width > 0.5:
            out.append((r.x0, r.x1, (r.y0 + r.y1) / 2))
    return out


def find_systems(page, hlines):
    ys = sorted({round(y, 1) for x0, x1, y in hlines if x1 - x0 > 150})
    staves, cur = [], []
    for y in ys:
        if cur and y - cur[-1] > 8:
            staves.append(cur)
            cur = []
        cur.append(y)
    if cur:
        staves.append(cur)
    staves = [(s[0], s[-1]) for s in staves if len(s) == 5]

    # A system barline/bracket is a tall vertical line spanning several staves.
    spans = []
    for dr in page.get_drawings():
        r = dr["rect"]
        if r.width < 3 and r.height > 30:
            spans.append((r.y0, r.y1))
    systems = []
    for top, bottom in staves:
        sys_span = next((s for s in spans if s[0] - 1 <= top and bottom <= s[1] + 1), None)
        if systems and sys_span and systems[-1]["span"] == sys_span:
            systems[-1]["bottom"] = bottom
        else:
            systems.append({"top": top, "bottom": bottom, "span": sys_span})
    return systems


def has_hyphen(hlines, y, x_from, x_to):
    # Hyphens are short dashes drawn a couple of points above the baseline;
    # extenders sit on the baseline and are ignored.
    return any(
        x1 - x0 < 8 and 1 < y - ly < 5 and x0 >= x_from - 1 and x1 <= x_to + 1
        for x0, x1, ly in hlines
    )


def extract(path):
    doc = pymupdf.open(path)
    meta = doc.metadata
    all_spans = []
    rows = []
    sys_offset = 0
    first_system_top = None
    for page in doc:
        spans = list(text_spans(page, split_words=True))
        all_spans.extend(text_spans(page, split_words=False))
        hlines = horizontal_lines(page)
        systems = find_systems(page, hlines)
        if page.number == 0 and systems:
            first_system_top = systems[0]["top"]
        page_rows = {}
        for s in spans:
            page_rows.setdefault((s["font"], s["size"], s["y"]), []).append(s)
        for (font, size, y), syl in page_rows.items():
            owner = [i for i, st in enumerate(systems) if st["top"] < y]
            if not owner or y > systems[owner[-1]]["bottom"] + 40:
                continue
            rows.append({"sys": sys_offset + owner[-1], "y": y, "font": font, "size": size,
                         "syl": sorted(syl, key=lambda s: s["x0"]), "hlines": hlines})
        sys_offset += len(systems)

    result = {
        "file": path,
        "isMuseScore": (meta.get("creator") or "").startswith("MuseScore"),
        "metadata": meta,
        "pageCount": doc.page_count,
        "pageSize": [doc[0].rect.width, doc[0].rect.height],
        "fonts": sorted({f[3] for p in doc for f in p.get_fonts()}),
    }
    if not rows:
        return {**result, "lyrics": []}

    # Lyrics are the dominant text style inside systems; this drops tempo marks, rit., etc.
    style = Counter((r["font"], r["size"]) for r in rows for _ in r["syl"]).most_common(1)[0][0]
    rows = [r for r in rows if (r["font"], r["size"]) == style]

    by_system = {}
    for r in rows:
        by_system.setdefault(r["sys"], []).append(r)
    lines = {}  # lyric line (verse) index -> words
    pending = {}  # verse index -> partial word carried across a system break
    for sys_idx in sorted(by_system):
        for verse, r in enumerate(sorted(by_system[sys_idx], key=lambda r: r["y"])):
            words = lines.setdefault(verse, [])
            word = pending.pop(verse, "")
            syl = r["syl"]
            for i, s in enumerate(syl):
                word += s["text"]
                nxt_x = syl[i + 1]["x0"] if i + 1 < len(syl) else 10_000
                if not has_hyphen(r["hlines"], r["y"], s["x1"], nxt_x):
                    words.append(word)
                    word = ""
            if word:
                pending[verse] = word
    for verse, word in pending.items():
        lines[verse].append(word)

    # Header: text above the first system on page 1; footer: text near the bottom of any page.
    header = [s for s in all_spans if s["page"] == 0 and s["y"] < (first_system_top or 150)]
    title = max(header, key=lambda s: s["size"], default=None)
    header = [s for s in header if s is not title]
    page_w, page_h = doc[0].rect.width, doc[0].rect.height
    return {
        **result,
        "title": title["text"] if title else None,
        "subtitle": [s["text"] for s in header if abs((s["x0"] + s["x1"]) / 2 - page_w / 2) < 30],
        "headerRight": [s["text"] for s in header if s["x1"] > page_w * 0.75],
        "headerLeft": [s["text"] for s in header if s["x0"] < page_w * 0.25],
        "footer": sorted({s["text"] for s in all_spans if s["y"] > page_h - 60 and not s["text"].isdigit()}),
        "lyrics": [" ".join(lines[v]) for v in sorted(lines)],
    }


if __name__ == "__main__":
    as_json = "--json" in sys.argv
    sys.stdout.reconfigure(encoding="utf-8")
    for f in [a for a in sys.argv[1:] if a != "--json"]:
        result = extract(f)
        if as_json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            continue
        print(f"=== {f}")
        for k, v in result.items():
            if k not in ("file", "lyrics"):
                print(f"{k}: {v}")
        for i, line in enumerate(result["lyrics"], 1):
            print(f"lyrics[{i}]: {line}")
        print()
