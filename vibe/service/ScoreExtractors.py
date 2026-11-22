"""Notation-software-aware text extraction for score PDFs.

Notation programs draw music with symbol fonts whose glyphs come out of a plain
text extraction as garbage, and they split lyrics into syllables separated by
hyphens. Each extractor here recognises PDFs exported by one program and
rebuilds the title, credits and lyrics from the page geometry. Register new
extractors in ``SCORE_EXTRACTORS``; PDFs that no extractor claims fall back to
the generic text/OCR path in ``FileProcessing``.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

_VERSE_NUMBER = re.compile(r"^\d+[.)]\s*")
_HYPHENS = {"-", "\u2010", "\u2011", "\u2013"}


class ScoreTextExtractor:
    """Base class for extractors that read text from one notation program's PDFs."""

    source = ""

    def matches(self, document) -> bool:
        raise NotImplementedError

    def extract(self, document) -> dict[str, Any]:
        """Return ``title``, ``subtitle``, ``header_left``, ``header_right``,
        ``lyrics``, ``other_text`` and ``footer``."""
        raise NotImplementedError

    @staticmethod
    def _font_names(document) -> set[str]:
        return {
            font[3].split("+", 1)[-1]
            for page in document
            for font in page.get_fonts()
        }


class LyricLayoutExtractor(ScoreTextExtractor):
    """Shared geometry engine for programs that keep lyrics as positioned text.

    Staves are found from groups of five long horizontal lines and systems from
    tall vertical lines spanning several staves. Lyric rows are text rows inside
    a system or stacked just below it; the most common text style among them is
    the lyric style. Syllables are joined when a hyphen sits between them, either
    as a short vector dash just above the baseline (MuseScore) or as a ``-`` text
    span on the baseline (Sibelius). Extender lines on the baseline are ignored.
    """

    # Fonts whose glyphs are notation, not words. Matched by name prefix after
    # removing any subset tag; Private Use Area glyphs are always treated as music.
    music_font_prefixes: tuple[str, ...] = ()
    footer_height = 60
    max_row_gap = 40
    # Syllables closer than this fraction of the font size are one word even
    # without a hyphen (programs drop the hyphen when there is no room for it).
    tight_join_ratio = 0.0

    def extract(self, document) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        lines_below_music: list[dict[str, Any]] = []
        all_spans: list[dict[str, Any]] = []
        system_offset = 0
        first_system_top = None
        for page in document:
            page_height = page.rect.height
            spans = list(self._text_spans(page, split_words=False))
            all_spans.extend(spans)
            lines = self._horizontal_lines(page)
            systems = self._find_systems(page, lines)
            if page.number == 0 and systems:
                first_system_top = systems[0]["top"]

            words = [word for word in self._text_spans(page, split_words=True)]
            hyphens = [word for word in words if word["text"] in _HYPHENS]
            page_rows: dict[tuple[str, float, float], list[dict[str, Any]]] = {}
            for word in words:
                if word["text"] not in _HYPHENS:
                    page_rows.setdefault((word["font"], word["size"], word["y"]), []).append(word)
            owners = self._row_owners(sorted({key[2] for key in page_rows}), systems, page_height)
            for (font, size, y), syllables in page_rows.items():
                if y not in owners:
                    continue
                rows.append({
                    "system": system_offset + owners[y],
                    "page": page.number,
                    "y": y,
                    "style": (font, size),
                    "syllables": sorted(syllables, key=lambda word: word["x0"]),
                    "lines": lines,
                    "hyphens": hyphens,
                })
            if systems:
                music_bottom = systems[-1]["bottom"]
                lines_below_music.extend(span for span in spans if span["y"] > music_bottom)
            system_offset += len(systems)

        lyric_style = self._lyric_style(rows)
        lyric_rows = [row for row in rows if row["style"] == lyric_style]
        lyric_positions = {(row["page"], row["y"]) for row in lyric_rows}

        first_page = document[0].rect
        header = [
            span for span in all_spans
            if span["page"] == 0 and span["y"] < (first_system_top or 150)
        ]
        title_size = max((span["size"] for span in header), default=None)
        title_spans = sorted(
            (span for span in header if span["size"] == title_size),
            key=lambda span: (span["y"], span["x0"]),
        )
        header = [span for span in header if span["size"] != title_size]

        # Footers are optional and not tied to any program: on each page the lowest
        # block of text under the music is the footer, anything above it is other text.
        other_text: list[str] = []
        footer: list[str] = []
        for page_number in sorted({span["page"] for span in lines_below_music}):
            blocks = self._text_blocks(
                span for span in lines_below_music
                if span["page"] == page_number
                and (span["page"], span["y"]) not in lyric_positions
                and not span["text"].isdigit()
            )
            if blocks:
                other_text.extend(line for block in blocks[:-1] for line in block)
                footer.extend(blocks[-1])
        return {
            "title": " ".join(" ".join(span["text"] for span in title_spans).split()),
            "subtitle": [
                span["text"] for span in header
                if abs((span["x0"] + span["x1"]) / 2 - first_page.width / 2) < 30
            ],
            "header_left": [span["text"] for span in header if span["x0"] < first_page.width * 0.25],
            "header_right": [span["text"] for span in header if span["x1"] > first_page.width * 0.75],
            "lyrics": self._lyrics(lyric_rows),
            "other_text": other_text,
            "footer": list(dict.fromkeys(footer)),
        }

    @staticmethod
    def _text_blocks(spans) -> list[list[str]]:
        """Group spans into lines, then into blocks split where the gap between
        baselines is more than about two line heights."""
        by_line: dict[float, list[dict[str, Any]]] = {}
        for span in spans:
            by_line.setdefault(span["y"], []).append(span)
        blocks: list[list[str]] = []
        previous: tuple[float, float] | None = None
        for y in sorted(by_line):
            line_spans = sorted(by_line[y], key=lambda span: span["x0"])
            text = " ".join(" ".join(span["text"] for span in line_spans).split())
            if sum(character.isalnum() for character in text) < 2:
                continue
            size = max(span["size"] for span in line_spans)
            if previous is None or y - previous[0] > 2 * max(size, previous[1]):
                blocks.append([])
            blocks[-1].append(text)
            previous = (y, size)
        return blocks

    def _row_owners(self, row_ys: list[float], systems: list[dict[str, Any]], page_height: float) -> dict[float, int]:
        """Map each text row's baseline to the system it belongs to.

        Rows inside a system belong to it; rows below it belong to it while each is
        within ``max_row_gap`` of the one above, so stacked verses stay together but
        a separate text block or the next system's chord symbols do not.
        """
        owners: dict[float, int] = {}
        for index, system in enumerate(systems):
            limit = systems[index + 1]["top"] if index + 1 < len(systems) else page_height - self.footer_height
            previous = system["bottom"]
            for y in row_ys:
                if system["top"] < y <= system["bottom"]:
                    owners[y] = index
                elif system["bottom"] < y < limit and y - previous <= self.max_row_gap:
                    owners[y] = index
                    previous = y
        return owners

    @staticmethod
    def _lyric_style(rows: list[dict[str, Any]]) -> tuple[str, float] | None:
        # The first text row of each system is almost always lyrics; tempo, chord and
        # free text such as extra stanzas below the music come later or in other styles.
        # Several styles can share that baseline (e.g. a bold verse number), so count all.
        first_ys: dict[int, float] = {}
        for row in rows:
            first_ys[row["system"]] = min(row["y"], first_ys.get(row["system"], row["y"]))
        counts = Counter(
            row["style"] for row in rows if row["y"] == first_ys[row["system"]] for _ in row["syllables"]
        )
        return counts.most_common(1)[0][0] if counts else None

    @classmethod
    def _lyrics(cls, rows: list[dict[str, Any]]) -> list[str]:
        by_system: dict[int, list[dict[str, Any]]] = {}
        for row in rows:
            by_system.setdefault(row["system"], []).append(row)

        verses: dict[int, list[str]] = {}
        pending: dict[int, str] = {}
        for system in sorted(by_system):
            for verse, row in enumerate(sorted(by_system[system], key=lambda row: row["y"])):
                words = verses.setdefault(verse, [])
                word = pending.pop(verse, "")
                syllables = list(row["syllables"])
                if syllables and not word:
                    first = _VERSE_NUMBER.sub("", syllables[0]["text"])
                    syllables[0] = {**syllables[0], "text": first}
                for index, syllable in enumerate(syllables):
                    word += syllable["text"]
                    next_x = syllables[index + 1]["x0"] if index + 1 < len(syllables) else float("inf")
                    if not cls._has_hyphen(row, syllable["x1"], next_x):
                        if word:
                            words.append(word)
                        word = ""
                if word:
                    pending[verse] = word
        for verse, word in pending.items():
            verses[verse].append(word)
        return [" ".join(verses[verse]) for verse in sorted(verses) if verses[verse]]

    @classmethod
    def _has_hyphen(cls, row: dict[str, Any], x_from: float, x_to: float) -> bool:
        baseline = row["y"]
        if cls.tight_join_ratio and x_to - x_from < row["style"][1] * cls.tight_join_ratio:
            return True
        if any(
            abs(hyphen["y"] - baseline) < 1.5 and hyphen["x0"] >= x_from - 1 and hyphen["x1"] <= x_to + 1
            for hyphen in row["hyphens"]
        ):
            return True
        # Vector hyphens are short dashes a couple of points above the baseline;
        # extenders sit on the baseline.
        return any(
            x1 - x0 < 8 and 1 < baseline - y < 5 and x0 >= x_from - 1 and x1 <= x_to + 1
            for x0, x1, y in row["lines"]
        )

    def _is_music(self, font: str, text: str) -> bool:
        if any(0xE000 <= ord(character) <= 0xF8FF for character in text):
            return True
        return font.split("+", 1)[-1].startswith(self.music_font_prefixes) if self.music_font_prefixes else False

    def _text_spans(self, page, split_words: bool):
        """Yield non-music text spans, optionally split at spaces into words or syllables.

        PyMuPDF merges closely spaced syllables ("par take") into one span, so
        splitting uses per-character boxes from ``rawdict``.
        """
        for block in page.get_text("rawdict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    characters = span["chars"]
                    text = "".join(character["c"] for character in characters)
                    if not text.strip() or self._is_music(span["font"], text):
                        continue
                    if not split_words:
                        visible = [character for character in characters if not character["c"].isspace()]
                        yield self._piece(visible, span, page, text.strip())
                        continue
                    current: list[dict[str, Any]] = []
                    for character in [*characters, {"c": " "}]:
                        if character["c"].isspace():
                            if current:
                                yield self._piece(current, span, page)
                            current = []
                        else:
                            current.append(character)

    @staticmethod
    def _piece(characters, span, page, text: str | None = None) -> dict[str, Any]:
        return {
            "text": unicodedata.normalize("NFKC", text or "".join(character["c"] for character in characters)),
            "font": span["font"].split("+", 1)[-1],
            "size": round(span["size"], 1),
            "x0": characters[0]["bbox"][0],
            "x1": characters[-1]["bbox"][2],
            "y": round(span["origin"][1], 1),
            "page": page.number,
        }

    @staticmethod
    def _horizontal_lines(page) -> list[tuple[float, float, float]]:
        """Thin horizontal vector segments: staff lines, hyphens and extenders."""
        return [
            (drawing["rect"].x0, drawing["rect"].x1, (drawing["rect"].y0 + drawing["rect"].y1) / 2)
            for drawing in page.get_drawings()
            if drawing["rect"].height < 1.5 and drawing["rect"].width > 0.5
        ]

    @staticmethod
    def _find_systems(page, lines) -> list[dict[str, Any]]:
        staff_line_ys = sorted({round(y, 1) for x0, x1, y in lines if x1 - x0 > 150})
        staves: list[list[float]] = []
        for y in staff_line_ys:
            if staves and y - staves[-1][-1] <= 8:
                staves[-1].append(y)
            else:
                staves.append([y])
        staves = [staff for staff in staves if len(staff) == 5]

        # A system's barline or bracket is a tall vertical line spanning its staves.
        verticals = [
            (drawing["rect"].y0, drawing["rect"].y1)
            for drawing in page.get_drawings()
            if drawing["rect"].width < 3 and drawing["rect"].height > 30
        ]
        systems: list[dict[str, Any]] = []
        for staff in staves:
            top, bottom = staff[0], staff[-1]
            span = next((v for v in verticals if v[0] - 1 <= top and bottom <= v[1] + 1), None)
            if systems and span and systems[-1]["span"] == span:
                systems[-1]["bottom"] = bottom
            else:
                systems.append({"top": top, "bottom": bottom, "span": span})
        return systems


class MuseScoreExtractor(LyricLayoutExtractor):
    """Reads MuseScore PDF exports.

    MuseScore draws notation with a SMuFL font (Leland, Bravura, ...) whose glyphs
    are in the Unicode Private Use Area. Each lyric syllable is its own text span;
    hyphens are short vector dashes ~2pt above the baseline.
    """

    source = "musescore"
    music_font_prefixes = ("Leland", "Bravura", "MScore", "Petaluma", "MuseJazz")

    def matches(self, document) -> bool:
        metadata = document.metadata or {}
        if "musescore" in (metadata.get("creator") or "").casefold():
            return True
        try:
            xmp = document.get_xml_metadata() or ""
        except Exception:
            return False
        return "<xmp:CreatorTool>MuseScore" in xmp


class SibeliusExtractor(LyricLayoutExtractor):
    """Reads Sibelius PDF exports.

    Sibelius's Opus/Helsinki/Inkpen2/Reprise/Norfolk music fonts map glyphs to
    ordinary Latin codepoints ("&" is a treble clef, "œ" a notehead), so they are
    excluded by font name. Lyric hyphens are ``-`` text spans on the baseline,
    sometimes in a smaller size, and verse numbers prefix the first syllable ("1.Twin").
    """

    source = "sibelius"
    music_font_prefixes = ("Opus", "Helsinki", "Inkpen2", "Reprise", "Norfolk")

    def matches(self, document) -> bool:
        metadata = document.metadata or {}
        if "sibelius" in (metadata.get("creator") or "").casefold():
            return True
        # PDFs re-saved by another tool can lose the creator; Opus is unique to Sibelius.
        return any(name.startswith("Opus") for name in self._font_names(document))


class LilyPondExtractor(LyricLayoutExtractor):
    """Reads LilyPond PDFs (usually written through Ghostscript).

    Notation uses the Emmentaler/feta fonts; text uses Century Schoolbook. Each
    syllable is its own span, hyphens are short vector dashes above the baseline,
    and verse numbers ("1.") are separate bold spans beside the first syllable.
    """

    source = "lilypond"
    music_font_prefixes = ("Emmentaler", "feta", "parmesan", "LilyJAZZ")
    # Word spaces are at least ~0.19 em; LilyPond omits the hyphen between
    # syllables squeezed closer than that, leaving a ~0.05 em gap.
    tight_join_ratio = 0.1

    def matches(self, document) -> bool:
        metadata = document.metadata or {}
        if "lilypond" in (metadata.get("creator") or "").casefold():
            return True
        return any(name.startswith(("Emmentaler", "feta")) for name in self._font_names(document))


SCORE_EXTRACTORS: list[ScoreTextExtractor] = [MuseScoreExtractor(), SibeliusExtractor(), LilyPondExtractor()]


def extract_score_text(path: str | Path) -> dict[str, Any] | None:
    """Return an OCR-shaped result for a PDF claimed by a registered extractor, else ``None``."""
    try:
        import fitz
    except ImportError:
        return None
    try:
        with fitz.open(path) as document:
            extractor = next((candidate for candidate in SCORE_EXTRACTORS if candidate.matches(document)), None)
            if extractor is None:
                return None
            extracted = extractor.extract(document)
    except Exception:
        return None

    credits = list(dict.fromkeys(
        line for line in [*extracted["subtitle"], *extracted["header_left"], *extracted["header_right"]] if line
    ))
    sections = [
        [extracted["title"]],
        credits,
        extracted["lyrics"],
        extracted["other_text"],
        extracted["footer"],
    ]
    text = "\n\n".join("\n".join(line for line in section if line) for section in sections if any(section))
    if not text:
        return None
    return {
        "status": "success",
        "text": text,
        "message": "",
        "source": extractor.source,
        "title": extracted["title"],
        "lyrics": extracted["lyrics"],
    }
