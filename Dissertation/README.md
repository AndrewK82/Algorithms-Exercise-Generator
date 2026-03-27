# Automated Generation of LZW Compression and Decompression Exercises for Class Tests

Andrew King — L4 Computing Science Dissertation, University of Glasgow, 2026

## Compiling the dissertation

This dissertation uses the standard University of Glasgow L4 project LaTeX template (`l4proj.cls`). Compile with pdflatex:

pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex


Two passes after bibtex are needed to resolve all cross-references and citations correctly.

## Structure

- `main.tex` — the dissertation source file
- `l4proj.bib` — bibliography
- `l4proj.cls` — University of Glasgow L4 project class file
- `images/` — figures, screenshots, and architecture diagrams used in the dissertation
- `appendices/` — ethics approval and questionnaire PDFs included in the appendices

## Page limit

This is a 20-credit project. The page limit is 30 pages of Arabic-numbered content, excluding front matter, appendices, and bibliography. Font, text size, margins, and spacing must not be altered.
