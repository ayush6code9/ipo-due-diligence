"""
Section-aware chunking for extracted DRHP page text (Phase 5).

Pure functions, no database or FAISS dependency, so this can be unit
tested in isolation from the embedding/vector-store machinery.

Strategy: walk through pages in order, splitting each page's (already
cleaned, per Phase 4) text into paragraphs on blank lines. A paragraph
that is a single short line and matches one of the known DRHP headings
exactly (after stripping leading numbering) is treated as a section
transition, not chunk content. Paragraphs accumulate into a chunk buffer
until it reaches ~TARGET_CHUNK_WORDS, at which point the chunk is flushed
and the next one starts with the last OVERLAP_WORDS words repeated for
context continuity. A small trailing remainder is merged into the previous
chunk instead of becoming a tiny chunk of its own.

Section names are only ever taken verbatim from KNOWN_SECTIONS — nothing
is invented.
"""

import re

TARGET_CHUNK_WORDS = 1000
OVERLAP_WORDS = 150
MIN_TRAILING_CHUNK_WORDS = 80

# DRHP headings this phase knows how to recognise. Matching is exact
# (case-insensitive, after stripping leading numbering) against a single
# short line — not a fuzzy/substring match — specifically to avoid
# mislabeling a section from an incidental phrase inside a paragraph.
KNOWN_SECTIONS = [
    "Risk Factors",
    "Business",
    "Industry Overview",
    "Our Promoters",
    "Promoter Group",
    "Financial Information",
    "Restated Financial Information",
    "Outstanding Litigation",
    "Material Developments",
    "Objects of the Issue",
    "Capital Structure",
    "Dividend",
    "Management",
    "Legal and Regulatory Information",
]

_KNOWN_SECTIONS_UPPER = {s.upper(): s for s in KNOWN_SECTIONS}
_LEADING_NUMBERING_RE = re.compile(r"^[\(\[]?[0-9ivxIVX]+[\)\].:-]?\s*")


def detect_section(line: str) -> str | None:
    """Returns a canonical section name from KNOWN_SECTIONS if `line` is
    (after stripping numbering/punctuation) an exact match, else None.
    Never returns a name that isn't in KNOWN_SECTIONS."""
    stripped = line.strip()
    if not stripped or len(stripped) > 80:
        return None
    candidate = _LEADING_NUMBERING_RE.sub("", stripped).strip()
    candidate = candidate.rstrip(":.").strip()
    return _KNOWN_SECTIONS_UPPER.get(candidate.upper())


def _take_last_words(paragraphs: list[tuple[int, str]], n: int) -> str:
    text = " ".join(p[1] for p in paragraphs)
    words = text.split()
    if len(words) <= n:
        return text
    return " ".join(words[-n:])


def chunk_pages(pages: list[dict], document_id: int) -> list[dict]:
    """pages: [{"page_number": int, "text": str}, ...] (already cleaned).
    Returns a list of chunk dicts:
        {chunk_id, document_id, page_start, page_end, section, text}

    Headings are detected line-by-line (not paragraph-by-paragraph):
    extracted PDF text commonly has a heading immediately followed by body
    text on the very next line with no blank line between them, so heading
    detection can't wait for an isolated single-line "paragraph" — it has
    to look at every line as it's read.
    """
    chunks: list[dict] = []
    buffer: list[tuple[int, str]] = []  # (page_number, paragraph_text)
    current_section: str | None = None
    chunk_index = 0

    # in-progress paragraph, accumulated line by line until a blank line,
    # a heading, or a page boundary closes it
    para_lines: list[str] = []
    para_page: int | None = None

    def close_paragraph():
        nonlocal para_lines, para_page
        if para_lines:
            text = " ".join(para_lines)
            buffer.append((para_page, text))
            para_lines = []
            para_page = None
            maybe_split_chunk()

    def maybe_split_chunk():
        nonlocal buffer
        word_count = sum(len(p[1].split()) for p in buffer)
        if word_count >= TARGET_CHUNK_WORDS:
            last_page = buffer[-1][0]
            overlap_text = _take_last_words(buffer, OVERLAP_WORDS)
            flush(is_final=False)
            if overlap_text:
                buffer.append((last_page, overlap_text))

    def flush(is_final: bool = False):
        nonlocal buffer, chunk_index
        if not buffer:
            return
        text = "\n\n".join(p[1] for p in buffer)
        word_count = len(text.split())

        if (
            is_final
            and chunks
            and word_count < MIN_TRAILING_CHUNK_WORDS
            and chunks[-1]["section"] == current_section
        ):
            # Merge a small trailing remainder into the previous chunk
            # rather than creating a near-empty final chunk — but only when
            # they're the same section. Merging across a real section
            # boundary would mislabel content under the wrong heading.
            previous = chunks[-1]
            previous["text"] = previous["text"] + "\n\n" + text
            previous["page_end"] = buffer[-1][0]
            buffer = []
            return

        chunk_index += 1
        chunks.append(
            {
                "chunk_id": f"{document_id}-{chunk_index:04d}",
                "document_id": document_id,
                "page_start": buffer[0][0],
                "page_end": buffer[-1][0],
                "section": current_section,
                "text": text,
            }
        )
        buffer = []

    for page in pages:
        page_number = page["page_number"]
        page_text = page.get("text") or ""
        if not page_text.strip():
            continue

        for line in page_text.split("\n"):
            stripped = line.strip()

            if not stripped:
                close_paragraph()
                continue

            section = detect_section(stripped)
            if section:
                close_paragraph()
                flush()  # close out the chunk under the OLD section
                current_section = section
                continue

            if para_page is None:
                para_page = page_number
            para_lines.append(stripped)

        close_paragraph()  # a paragraph doesn't silently span a page boundary

    flush(is_final=True)
    return chunks
