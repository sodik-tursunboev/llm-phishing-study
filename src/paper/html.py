"""Turn paper/manuscript_filled.md into a print-ready page, paper/manuscript.html.

python -m src.paper.html
Then print it to PDF with a browser, for example headless Edge on Windows:
  msedge --headless --no-pdf-header-footer --print-to-pdf=<full path to PDF> <full path to manuscript.html>

Both outputs are git-ignored: they contain the student IDs, which belong in the PDF only.
"""
import pathlib
import re

import markdown

SOURCE = pathlib.Path("paper/manuscript_filled.md")
OUTPUT = pathlib.Path("paper/manuscript.html")

CSS = """
@page { size: A4; margin: 20mm 18mm 18mm 18mm;
        @bottom-center { content: counter(page); font: 9pt Georgia, serif; color: #555; } }
body { font-family: Georgia, "Times New Roman", serif; font-size: 10.5pt; line-height: 1.45;
       color: #111; margin: 0; }
h1 { font-size: 17pt; line-height: 1.25; text-align: center; margin: 0 0 6pt; }
h1 + p, h1 + p + p { text-align: center; margin: 2pt 0; }
h1 + p + p { font-size: 9.5pt; color: #333; margin-bottom: 14pt; }
h2 { font-size: 12.5pt; margin: 16pt 0 5pt; border-bottom: 0.6pt solid #999; padding-bottom: 2pt; }
h3 { font-size: 11pt; margin: 11pt 0 4pt; }
h2, h3 { page-break-after: avoid; font-family: Helvetica, Arial, sans-serif; }
p, li { text-align: justify; hyphens: auto; }
p { margin: 0 0 6pt; }
ul { margin: 0 0 6pt 16pt; padding: 0; }
li { margin-bottom: 2pt; }
code { font-family: Consolas, "Courier New", monospace; font-size: 9pt; }
a { color: #1a4f8b; text-decoration: none; word-break: break-all; }
table { width: 100%; border-collapse: collapse; font-size: 8pt; margin: 4pt 0 10pt;
        page-break-inside: avoid; font-family: Helvetica, Arial, sans-serif; }
table { border-top: 1pt solid #111; border-bottom: 1pt solid #111; }
th, td { padding: 2pt 3pt; text-align: center; }
th { border-bottom: 0.6pt solid #111; }
td:first-child, td:nth-child(2) { text-align: left; }
h2#references ~ p { font-size: 9pt; text-align: left; margin-bottom: 4pt; }
p:has(+ table) { break-after: avoid; page-break-after: avoid; }
"""


def linkify(text):
    """Make bare URLs and DOIs clickable; lines with code spans (such as `<URL>`) are left as they are.
    Also put a blank line before a list that follows a paragraph line, which Markdown needs to see
    a list rather than running text."""
    out = []
    for line in text.splitlines():
        if "`" not in line:
            line = re.sub(r"(?<![<(\[])(https?://[^\s<>()]+[^\s<>().,;])", r"<\1>", line)
            line = re.sub(r"doi: (10\.\d{4,}/[^\s,]*[^\s,.])", r"doi: [\1](https://doi.org/\1)", line)
        if line.startswith("- ") and out and out[-1].strip() and not out[-1].startswith("- "):
            out.append("")
        out.append(line)
    return "\n".join(out)


def main():
    body = markdown.markdown(linkify(SOURCE.read_text(encoding="utf-8")), extensions=["tables", "toc"])
    title = re.search(r"<h1[^>]*>(.*?)</h1>", body).group(1)
    OUTPUT.write_text(f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><title>{title}</title>'
                      f"<style>{CSS}</style></head><body>\n{body}\n</body></html>\n", encoding="utf-8")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
