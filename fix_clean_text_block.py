from pathlib import Path

path = Path('utils.py')
text = path.read_text(encoding='utf-8')
start = 'def clean_text(text: str, allow_unicode: bool = True) -> str:\n'
end = '\ndef _set_pdf_font(pdf, font_name: str, font_size: int = 11) -> None:\n'
if start not in text or end not in text:
    raise SystemExit('Markers not found')
body = '''def clean_text(text: str, allow_unicode: bool = True) -> str:
    """Nettoie le texte Markdown/plain text pour l'export PDF sans crash."""
    if text is None:
        return ""
    text = text.replace("\\r\\n", "\\n").replace("\\r", "\\n")
    for source, replacement in REPLACEMENT_MAP.items():
        text = text.replace(source, replacement)
    text = text.replace("\\t", "    ")
    text = text.replace("•", "-")
    text = text.replace("“", '\"').replace("”", '\"')
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("…", "...").replace("–", "-").replace("—", "-")
    text = "".join(ch for ch in text if ch == "\\n" or ch == "\\t" or ord(ch) >= 32)
    if not allow_unicode:
        text = text.encode("latin-1", "replace").decode("latin-1")
    return text
'''
head, rest = text.split(start, 1)
_, tail = rest.split(end, 1)
path.write_text(head + body + end + tail, encoding='utf-8')
print('fixed')
