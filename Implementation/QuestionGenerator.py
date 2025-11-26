import random
import math
import re
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

def generate_lzw_question():
    # Step 1 — Define fixed alphabet
    symbols = ['A', 'C', 'T', 'G']
    alphabet = set(symbols)

    # --- User inputs ---
    try:
        text_length = int(input("Enter desired input length (min 8, max 30): "))
        repeats_required = int(input("Enter minimum number of repeating substrings (>= 2): "))
        entropy_level = input("Entropy level? (high / low): ").strip().lower()
    except ValueError:
        print("Invalid input. Please enter numeric values.")
        return

    text_length = max(8, min(text_length, 30))
    repeats_required = max(2, repeats_required)

    # Entropy-based symbol distributions (Shannon 1948)
    if entropy_level == "low":
        probabilities = [0.80, 0.10, 0.05, 0.05]
    else:
        probabilities = [0.25, 0.25, 0.25, 0.25]

    # --- Generate valid text ---
    while True:
    # generate string according to probabilities
        text = ''.join(random.choices(symbols, probabilities, k=text_length))

        if not all(text.count(ch) >= 2 for ch in symbols):
            continue

        repeats = {text[i:i+2] for i in range(len(text)-1) if text.count(text[i:i+2]) > 1}
        if len(repeats) < repeats_required:
            continue

        if re.search(r'(.)\1{3,}', text):
            continue

        break

    # Testing Generatinh PDF of table showing text ---
    pdf_filename = "lzw_question_table.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)

    # Table content: one row, each symbol in its own cell
    table_data = [list(text)]

    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 14),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))

    doc.build([table])

    print(f"\nPDF successfully created: {pdf_filename}\n")

    # Step 3 — LZW Compression (max dict size = 11)
    dictionary = {ch: idx for idx, ch in enumerate(symbols)}
    dict_size = len(dictionary)
    w = ""
    compressed_output = []

    for c in text:
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            compressed_output.append(dictionary[w])
            if dict_size < 11:
                dictionary[wc] = dict_size
                dict_size += 1
            w = c
    if w:
        compressed_output.append(dictionary[w])

    # Step 4 — Bits calculation
    original_bits = len(text) * 8
    code_bits = math.ceil(math.log2(len(dictionary)))
    compressed_bits = len(compressed_output) * code_bits

    # Step 5 — Output question prompt
    question = f"""
LZW Compression Question
------------------------
Alphabet: {alphabet}
Entropy Setting: {entropy_level.upper()}
Symbol Probabilities: {probabilities}
Input Text: {text}
(PDF table version saved as: {pdf_filename})

Tasks:
1. Apply LZW compression to the input text.
2. Show each dictionary expansion step until 11 entries exist.
3. Identify at least two repeating substrings.
4. Provide the final encoded output sequence.
5. Calculate:
   - Original size in bits (8 bits per symbol)
   - Compressed size based on final dictionary size

---
Example Data (for verification):
Initial Dictionary: { {k:v for k,v in list(dictionary.items())[:4]} }
Final Dictionary Size: {len(dictionary)}
Original Bits: {original_bits} bits
Compressed Bits: {compressed_bits} bits
Encoded Output (indices): {compressed_output}
"""
    print(question)


# Run the script
if __name__ == "__main__":
    generate_lzw_question()
