"""Markdown -> HTML rendering for AI-generated ESG analysis.

The DeepSeek API returns markdown formatted text (headings, bold, lists).
We render it server-side to HTML so the same string can be displayed
both on the report page (innerHTML) and inside the WeasyPrint PDF
(via Jinja's `| safe` filter).

Raw HTML in the markdown source is HTML-escaped first to neutralise any
accidental script/style tags from the upstream LLM, while preserving all
markdown syntax characters (`*`, `#`, `-`, `|`, etc.).
"""
import html as _html

try:
    import markdown as _md
except ImportError:  # pragma: no cover — handled by requirements.txt
    _md = None


def render_markdown(text: str) -> str:
    """Convert a markdown string to a safe HTML fragment.

    Returns an empty string for falsy input. Falls back to a simple
    `<pre>` wrapping if the markdown library is not installed, so the
    page still renders the raw text legibly.
    """
    if not text:
        return ''

    escaped = _html.escape(text)

    if _md is None:
        return f'<pre style="white-space:pre-wrap; margin:0;">{escaped}</pre>'

    return _md.markdown(
        escaped,
        extensions=['extra', 'sane_lists'],
        output_format='html5',
    )
