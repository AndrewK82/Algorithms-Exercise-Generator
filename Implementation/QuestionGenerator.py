import random
import math
import time
import csv
from collections import Counter
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
# ENTROPY CALCULATION
# ------------------------------------------------------------------
def calculate_shannon_entropy(text):
    counts = Counter(text)
    length = len(text)
    entropy = 0
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy

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

    # attempt limit instead of time limit (more reproducible)
    for _ in range(2000):

        if entropy_type == 'low_entropy':
            weights = [0.6, 0.2, 0.1, 0.1]
        else:
            weights = [0.25, 0.25, 0.25, 0.25]

        text = "".join(random.choices(SYMBOLS, weights=weights, k=length))
        d_size, compressed = simulate_lzw(text)
        entropy_value = calculate_shannon_entropy(text)

        if (
            abs(d_size - target_dict_size) <= 1
            and len(compressed) < len(text)
            and len(set(text)) >= 2  # avoid trivial sequences
        ):
            return text, d_size, compressed, entropy_value

    # fallback return
    return text, d_size, compressed, entropy_value

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
# LOGGING (FOR DISSERTATION ANALYSIS)
# ------------------------------------------------------------------
def log_question_data(filename, row):
    file_exists = False
    try:
        with open(filename, 'r'):
            file_exists = True
    except FileNotFoundError:
        pass

    with open(filename, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "Question",
                "Sequence",
                "Entropy",
                "Final_Dict_Size",
                "Compressed_Length",
                "Original_Length"
            ])
        writer.writerow(row)

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
    1. Show the value of w and c at each step.<br/>
    2. Indicate when a new dictionary entry is added.<br/>
    3. Record the output code each time output occurs.<br/>
    4. Compare ASCII vs LZW using fixed-width {bit_width}-bit codes.
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
# MAIN
# ------------------------------------------------------------------

def main():
    print("--- LZW Question Generator ---")

    try:
        length = int(input("Enter string length (8–30): "))
        length = max(8, min(length, 30))

        print("Select Complexity Profile:")
        print("1. High Entropy")
        print("2. Low Entropy")
        choice = input("Choice (1 or 2): ").strip()
        entropy = 'high_entropy' if choice == '1' else 'low_entropy'

        num_questions = int(input("How many questions to generate? "))
        num_questions = max(1, num_questions)

    except ValueError:
        length = 15
        entropy = 'high_entropy'
        num_questions = 5

    for i in range(1, num_questions + 1):
        print(f"\n--- Generating Question {i} ---")

        text, d_size, out, entropy_value = generate_smart_lzw_string(length, entropy)

        print(f"Sequence: {text}")
        print(f"Final Dictionary Size: {d_size}")
        print(f"Shannon Entropy: {round(entropy_value,3)}")

        pdf_name = f"lzw_compression_{i}.pdf"

        generate_pdf_report(text, out, d_size, filename=pdf_name)

        log_question_data(
            "question_metrics.csv",
            [
                i,
                text,
                round(entropy_value, 3),
                d_size,
                len(out),
                len(text)
            ]
        )

        print(f"PDF generated: {pdf_name}")

if __name__ == "__main__":
    main()