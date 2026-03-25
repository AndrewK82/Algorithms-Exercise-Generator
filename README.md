# LZW Exercise Generator

Automatically generates LZW compression and decompression exercise sheets for class tests, producing ready-to-compile LaTeX question and answer files.

## What you need

- Python 3.8 or later
- A LaTeX distribution (e.g. MiKTeX on Windows, MacTeX on Mac) to compile the generated .tex files
- No additional Python packages required

## How to run

All scripts should be run from inside the `Implementation/` folder.

### Compression questions

python LZW_Compression_Generator.py

You will be asked for:
- String length (8–30) — how long the input sequence is
- Profile (1 = High Entropy, 2 = Low Entropy) — high entropy strings look more random, low entropy strings have one dominant character
- Number of questions to generate

### Decompression questions

python LZW_Decompression_Generator.py

Same prompts as above, plus:
- Special case (y/n) — whether to include the LZW edge case where a code is encountered before its dictionary entry is fully defined

### Figures (dissertation use only)

python LZW_Figure_Generator.py


Generates all evaluation figures into `dissertation_figures_v3/`. Takes a few minutes to run.

## Output

After running either generator you will find:
- `Questions/` — student-facing question sheets with only the first row completed
- `Answers/` — full examiner answer keys

Compile any `.tex` file with pdflatex to get a PDF:

pdflatex lzw_answer_1.tex
