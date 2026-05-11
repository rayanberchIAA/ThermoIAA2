from pathlib import Path

path = Path('utils.py')
text = path.read_text(encoding='utf-8')
start = '# ─────────────────────────────────────────────────────────────────────────────\n# 5.  Export PDF via fpdf2\n# ─────────────────────────────────────────────────────────────────────────────\n'
end = '# ─────────────────────────────────────────────────────────────────────────────\n# 6.  Formatage des nombres pour l\'affichage\n'
new_block = '''# ─────────────────────────────────────────────────────────────────────────────
# 5.  Export PDF via fpdf2
# ─────────────────────────────────────────────────────────────────────────────

UNICODE_FONT_CANDIDATES = [
    "DejaVuSans.ttf",
    "NotoSans-Regular.ttf",
    "NotoSans.ttf",
]
DEFAULT_PDF_FONT = "Helvetica"
MAX_TABLE_WIDTH = 190

REPLACEMENT_MAP = {
    "à": "",
    "6": "",
    ": "",
    "àA0
    "": " ",
    "": " ",
    "You are an expert Python engineer specializing in Streamlit, PDF generation, and Unicode-safe text rendering.

I have a Streamlit project using `fpdf2` that crashes with:

`FPDFUnicodeEncodingException: Character "—" is outside the range of characters supported by the font used: "courier"`.

Your task is to fully refactor the PDF export system so it NEVER fails on Unicode characters.

Requirements:

1. Replace the current PDF export implementation with a robust Unicode-safe solution.
2. Use a real Unicode font such as:

   * DejaVuSans.ttf
   * NotoSans.ttf
3. Automatically load and register the font using:

   ```python
   pdf.add_font(..., uni=True)
   ```
4. Ensure support for:

   * French accents
   * Unicode punctuation
   * smart quotes
   * em dashes
   * Arabic text if possible
5. Create a reusable function:

   ```python
   def clean_text(text): ...
   ```

   that sanitizes problematic characters safely.
6. Replace every:

   ```python
   pdf.cell(...)
   ```

   with safer alternatives when appropriate:

   ```python
   pdf.multi_cell(...)
   ```
7. Preserve line breaks and formatting from Markdown/plain text reports.
8. Prevent ALL encoding crashes gracefully.
9. If the font file is missing:

   * automatically detect it,
   * show a clear error,
   * and fallback safely instead of crashing.
10. Refactor the entire exporter cleanly and professionally.

Important:

* Do NOT give explanations only.
* Directly modify and output the COMPLETE corrected code.
* Keep compatibility with Streamlit.
* Do not break existing functionality.
* Use production-quality Python code.
* Add comments explaining critical sections.
* Ensure the final implementation is stable and scalable.

Current failing line:

```python
pdf.cell(0, 6, ligne, ln=True)
```

The project structure already contains:

* app.py
* utils.py
* Streamlit environment
* virtual environment

Return:

1. the corrected imports,
2. the fully rewritten exporter function,
3. helper utilities,
4. and any required dependency installation ": " ",
    "": " ",
    "": " ",
    ": " ",
    "": " ",
    "*": " ",
    "$": " ",
    "9": " ",
    "6": " ",
    "“": '"',
    "”": '"',
    "‘": "'",
    "’": "'",
    "–": '-',
    "—": '-',
    "…": '...',
    "•": '-',
    "\u00A0": ' ',
}


def find_unicode_font() -> tuple[str, Path | None]:
    """Cherche un fichier de police Unicode disponible localement."""
    env_path = __import__('os').environ.get('PDF_UNICODE_FONT')
    if env_path:
        custom_path = Path(env_path.strip())
        if custom_path.exists():
            return custom_path.stem, custom_path
        __import__('warnings').warn(
            f"Police Unicode non trouvée à {custom_path}. Utilisez DejaVuSans.ttf ou NotoSans.ttf."
        )

    search_dirs = [
        Path(__file__).resolve().parent,
        Path.cwd(),
        Path(__file__).resolve().parent / "fonts",
        Path.cwd() / "fonts",
    ]
    for directory in search_dirs:
        for candidate in UNICODE_FONT_CANDIDATES:
            font_path = directory / candidate
            if font_path.exists():
                return font_path.stem, font_path
    return DEFAULT_PDF_FONT, None


def clean_text(text: str, allow_unicode: bool = True) -> str:
    """Nettoie le texte Markdown/plain text pour l'export PDF sans crash."""
    if text is None:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    for source, replacement in REPLACEMENT_MAP.items():
        text = text.replace(source, replacement)
    text = text.replace("•", "-")
    text = text.replace("\t", "    ")
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    if not allow_unicode:
        text = text.encode("latin-1", "replace").decode("latin-1")
    return text


def _set_pdf_font(pdf, font_name: str, font_size: int = 11) -> None:
    """Positionne la police PDF de manière stable."""
    try:
        pdf.set_font(font_name, size=font_size)
    except Exception:
        pdf.set_font(DEFAULT_PDF_FONT, size=font_size)


def _safe_multi_cell(pdf, text: str) -> None:
    """Utilise multi_cell pour toutes les lignes et revient à cell en dernier recours."""
    try:
        pdf.multi_cell(0, 6, text)
    except Exception:
        try:
            pdf.cell(0, 6, text, ln=True)
        except Exception:
            safe_text = text.encode("latin-1", "replace").decode("latin-1")
            pdf.cell(0, 6, safe_text, ln=True)


def exporter_pdf(rapport_md: str) -> bytes:
    """Convertit un rapport Markdown en PDF sans jamais planter sur Unicode."""
    try:
        from fpdf import FPDF
    except ImportError:
        __import__('warnings').warn(
            "fpdf2 n'est pas installé. Installez-le avec `pip install fpdf2`."
        )
        return b""

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    font_name, font_path = find_unicode_font()
    unicode_font_available = False
    if font_path is not None:
        try:
            pdf.add_font(font_name, "", str(font_path), uni=True)
            _set_pdf_font(pdf, font_name, font_size=11)
            unicode_font_available = True
        except Exception as exc:
            __import__('warnings').warn(
                f"Impossible de charger la police Unicode {font_path}: {exc}. Retour à {DEFAULT_PDF_FONT}."
            )
            _set_pdf_font(pdf, DEFAULT_PDF_FONT, font_size=11)
    else:
        __import__('warnings').warn(
            "Aucune police Unicode trouvée. Installez DejaVuSans.ttf ou NotoSans.ttf "
            "dans le dossier du projet ou fonts/. Le rendu sera limité."
        )
        _set_pdf_font(pdf, DEFAULT_PDF_FONT, font_size=11)

    for raw_line in rapport_md.splitlines():
        ligne = clean_text(raw_line, allow_unicode=unicode_font_available)
        if ligne.startswith("# "):
            _set_pdf_font(pdf, font_name if unicode_font_available else DEFAULT_PDF_FONT, font_size=16)
            _safe_multi_cell(pdf, ligne[2:].strip())
            _set_pdf_font(pdf, font_name if unicode_font_available else DEFAULT_PDF_FONT, font_size=11)
        elif ligne.startswith("## "):
            _set_pdf_font(pdf, font_name if unicode_font_available else DEFAULT_PDF_FONT, font_size=13)
            _safe_multi_cell(pdf, ligne[3:].strip())
            _set_pdf_font(pdf, font_name if unicode_font_available else DEFAULT_PDF_FONT, font_size=11)
        elif ligne.startswith("### "):
            _set_pdf_font(pdf, font_name if unicode_font_available else DEFAULT_PDF_FONT, font_size=11)
            _safe_multi_cell(pdf, ligne[4:].strip())
            _set_pdf_font(pdf, font_name if unicode_font_available else DEFAULT_PDF_FONT, font_size=11)
        elif ligne.startswith("|"):
            _set_pdf_font(pdf, font_name if unicode_font_available else DEFAULT_PDF_FONT, font_size=9)
            _safe_multi_cell(pdf, ligne)
            _set_pdf_font(pdf, font_name if unicode_font_available else DEFAULT_PDF_FONT, font_size=11)
        elif __import__('re').match(r"^[-*+]\s+", ligne):
            bullet = "• " if unicode_font_available else "- "
            _safe_multi_cell(pdf, f"{bullet}{ligne[2:].strip()}")
        elif ligne == "---":
            pdf.ln(2)
            pdf.set_draw_color(180, 180, 180)
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + MAX_TABLE_WIDTH, pdf.get_y())
            pdf.ln(2)
        elif not ligne.strip():
            pdf.ln(3)
        else:
            if "**" in ligne:
                ligne = ligne.replace("**", "")
            _safe_multi_cell(pdf, ligne)

    try:
        pdf_bytes = pdf.output(dest="S").encode("latin-1")
    except Exception:
        pdf_bytes = pdf.output(dest="S").encode("latin-1", "replace")
    return pdf_bytes


# ─────────────────────────────────────────────────────────────────────────────
# 6.  Formatage des nombres pour l'affichage
# ─────────────────────────────────────────────────────────────────────────────
'''
if start not in text or end not in text:
    raise SystemExit('Markers not found in utils.py')
head, tail = text.split(start, 1)
_, tail = tail.split(end, 1)
path.write_text(head + new_block + end + tail, encoding='utf-8')
print('updated')
