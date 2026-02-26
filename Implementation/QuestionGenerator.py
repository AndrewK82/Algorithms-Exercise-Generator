import random
import math
import time
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

# ------------------------------------------------------------------
# CONFIGURATION & DIFFICULTY CONSTANTS
# ------------------------------------------------------------------
SYMBOLS = ['A', 'C', 'T', 'G']

SCALING_FACTORS = {
    'low_entropy': 0.4,
    'high_entropy': 0.7
}

# ------------------------------------------------------------------
# DIFFICULTY CONTROL
# ------------------------------------------------------------------
def calculate_target_dict_size(length, entropy_type):
    base_size = len(SYMBOLS)
    growth = int(length * SCALING_FACTORS[entropy_type])
    return base_size + max(3, growth)

# ------------------------------------------------------------------
# SMART STRING GENERATION
# ------------------------------------------------------------------
def generate_smart_lzw_string(length, entropy_type):
    target_dict_size = calculate_target_dict_size(length, entropy_type)
    start_time = time.time()

    while time.time() - start_time < 5:
        if entropy_type == 'low_entropy':
            weights = [0.6, 0.2, 0.1, 0.1]
        else:
            weights = [0.25, 0.25, 0.25, 0.25]

        text = "".join(random.choices(SYMBOLS, weights=weights, k=length))
        d_size, compressed = simulate_lzw(text)

        if abs(d_size - target_dict_size) <= 1 and len(compressed) < len(text):
            return text, d_size, compressed

    return text, d_size, compressed

# ------------------------------------------------------------------
# LZW SIMULATION
# ------------------------------------------------------------------
def simulate_lzw(text):
    dictionary = {ch: idx for idx, ch in enumerate(SYMBOLS)}
    dict_size = len(dictionary)
    w = ""
    output = []

    for c in text:
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            output.append(dictionary[w])
            dictionary[wc] = dict_size
            dict_size += 1
            w = c

    if w:
        output.append(dictionary[w])

    return dict_size, output

# ------------------------------------------------------------------
# PDF GENERATION (EXAM PAPER)
# ------------------------------------------------------------------
def generate_pdf_report(text, compressed_out, final_dict_size, filename="lzw_compression.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>LZW Compression Challenge</b>", styles['Title']))
    elements.append(Spacer(1, 12))

    original_bits = len(text) * 8
    bit_width = math.ceil(math.log2(final_dict_size))
    compressed_bits = len(compressed_out) * bit_width
    ratio = (1 - compressed_bits / original_bits) * 100

    elements.append(Paragraph(f"<b>Input Sequence (Length {len(text)}):</b>", styles['Heading3']))

    t = Table([list(text)], colWidths=[20]*len(text))
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    elements.append(t)
    elements.append(Spacer(1, 15))

    question_text = f"""
    <b>Task Requirements:</b><br/><br/>
    1. Trace the LZW algorithm.<br/>
    2. Initial dictionary: A(0), C(1), T(2), G(3).<br/>
    3. Show all dictionary insertions.<br/>
    4. Compare ASCII vs LZW using {bit_width}-bit codes.
    """
    elements.append(Paragraph(question_text, styles['BodyText']))
    elements.append(Spacer(1, 25))
    elements.append(Paragraph("-" * 60, styles['BodyText']))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("<b>Examiner Solution Key</b>", styles['Heading2']))

    dictionary = {ch: idx for idx, ch in enumerate(SYMBOLS)}
    dict_size = len(dictionary)
    w = ""
    history = [["Current w", "Next c", "New Entry", "Index", "Output"]]

    for c in text:
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            history.append([w, c, wc, str(dict_size), str(dictionary[w])])
            dictionary[wc] = dict_size
            dict_size += 1
            w = c

    history.append([w, "EOF", "-", "-", str(dictionary[w])])

    t_steps = Table(history)
    t_steps.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    elements.append(t_steps)
    elements.append(Spacer(1, 15))

    stats = f"""
    <b>Final Statistics:</b><br/>
    Dictionary Size: {final_dict_size}<br/>
    Encoded Output: {compressed_out}<br/>
    Original Size: {original_bits} bits<br/>
    Compressed Size: {compressed_bits} bits<br/>
    Compression Savings: {ratio:.1f}%
    """
    elements.append(Paragraph(stats, styles['BodyText']))

    doc.build(elements)
    return filename

# ------------------------------------------------------------------
# LaTeX GENERATION (EXAM PAPER)
# ------------------------------------------------------------------
def generate_latex_exam(text, compressed_out, final_dict_size, filename="lzw_exam.tex"):
    bit_width = math.ceil(math.log2(final_dict_size))
    original_bits = len(text) * 8
    compressed_bits = len(compressed_out) * bit_width
    ratio = (1 - compressed_bits / original_bits) * 100

    dictionary = {ch: idx for idx, ch in enumerate(SYMBOLS)}
    dict_size = len(dictionary)
    w = ""
    steps = []

    for c in text:
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            steps.append((w, c, wc, dict_size, dictionary[w]))
            dictionary[wc] = dict_size
            dict_size += 1
            w = c
    steps.append((w, "EOF", "-", "-", dictionary[w]))

    latex = r"""\documentclass{article}
\usepackage{geometry}
\usepackage{array}
\geometry{margin=1in}

\begin{document}

\section*{LZW Compression Challenge}

\textbf{Input Sequence (Length """ + str(len(text)) + r"""):}

\[
""" + " \; ".join(text) + r"""
\]

\textbf{Task Requirements}
\begin{enumerate}
\item Trace the LZW algorithm.
\item Initial dictionary: A(0), C(1), T(2), G(3).
\item Show all dictionary insertions.
\item Compare ASCII vs LZW using """ + str(bit_width) + r"""-bit codes.
\end{enumerate}

\section*{Examiner Solution Key}

\begin{center}
\begin{tabular}{|c|c|c|c|c|}
\hline
Current $w$ & Next $c$ & New Entry & Index & Output \\
\hline
"""

    for row in steps:
        latex += f"{row[0]} & {row[1]} & {row[2]} & {row[3]} & {row[4]} \\\\\n\\hline\n"

    latex += r"""
\end{tabular}
\end{center}

\section*{Final Statistics}
\begin{itemize}
\item Dictionary Size: """ + str(final_dict_size) + r"""
\item Encoded Output: """ + str(compressed_out) + r"""
\item Original Size: """ + str(original_bits) + r""" bits
\item Compressed Size: """ + str(compressed_bits) + r""" bits
\item Compression Savings: """ + f"{ratio:.1f}" + r"""\%
\end{itemize}

\end{document}
"""

    with open(filename, "w") as f:
        f.write(latex)

    return filename

# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------

def main():
    print("--- LZW Question Generator (25 Questions Mode) ---")

    try:
        length = int(input("Enter string length (8–30): "))
        length = max(8, min(length, 30))

        print("Select Complexity Profile:")
        print("1. High Entropy")
        print("2. Low Entropy")
        choice = input("Choice (1 or 2): ").strip()
        entropy = 'high_entropy' if choice == '1' else 'low_entropy'

    except ValueError:
        length = 15
        entropy = 'high_entropy'

    for i in range(1, 26):
        print(f"\n--- Generating Question {i} ---")

        text, d_size, out = generate_smart_lzw_string(length, entropy)

        print(f"Sequence: {text}")
        print(f"Final Dictionary Size: {d_size}")

        pdf_name = f"lzw_compression_{i}.pdf"
        tex_name = f"lzw_exam_{i}.tex"

        generate_pdf_report(text, out, d_size, filename=pdf_name)
        generate_latex_exam(text, out, d_size, filename=tex_name)

        print(f"PDF generated: {pdf_name}")
        print(f"LaTeX generated: {tex_name}")

if __name__ == "__main__":
    main()
