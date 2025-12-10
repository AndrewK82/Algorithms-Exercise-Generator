import random
import math
import re
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

def generate_lzw_question():
    # Step 1 — Define fixed alphabet
    symbols = ['A', 'C', 'T', 'G']
    pdf_filename="lzw_question.pdf"
    alphabet = set(symbols)
    TARGET_DICT_SIZE = 11  # desired final dictionary size

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

    # --- Generate valid text until dictionary naturally reaches target size ---
    while True:
        text = ''.join(random.choices(symbols, probabilities, k=text_length))

        if not all(text.count(ch) >= 2 for ch in symbols):
            continue

        repeats = {text[i:i+2] for i in range(len(text)-1) if text.count(text[i:i+2]) > 1}
        if len(repeats) < repeats_required:
            continue

        if re.search(r'(.)\1{3,}', text):
            continue

        # Run full LZW naturally to check dictionary size
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
                dictionary[wc] = dict_size
                dict_size += 1
                w = c
        if w:
            compressed_output.append(dictionary[w])

        if dict_size == TARGET_DICT_SIZE:
            break  # valid text found

    # Step 4 — Bits calculation
    original_bits = len(text) * 8
    code_bits = math.ceil(math.log2(len(dictionary)))
    compressed_bits = len(compressed_output) * code_bits

    # ---- PDF GENERATION ----

    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("<b>LZW Compression Question</b>", styles['Title']))
    elements.append(Spacer(1, 12))

    # Text table
    table_data = [list(text)]
    text_table = Table(table_data)
    text_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 12),
    ]))

    elements.append(Paragraph("Input Text:", styles['Heading3']))
    elements.append(text_table)
    elements.append(Spacer(1, 16))

    # Question text
    question_text = f"""
<b>Tasks</b><br/><br/>
1. Apply LZW compression to the input text shown above.<br/>
2. Show each dictionary expansion step until the dictionary reaches {TARGET_DICT_SIZE} entries.<br/>
3. Identify at least two repeating substrings in the input.<br/>
4. Provide the final LZW encoded output sequence.<br/>
5. Calculate:<br/>
&nbsp;&nbsp;• Original size in bits (8 bits per symbol)<br/>
&nbsp;&nbsp;• Compressed size in bits using the final dictionary size<br/><br/>

<b>Examiner Information (not shown to students):</b><br/>
Initial Dictionary: { {ch: idx for idx, ch in enumerate(symbols)} }<br/>
Final Dictionary Size: {len(dictionary)}<br/>
Original Bits: {original_bits} bits<br/>
Compressed Bits: {compressed_bits} bits<br/>
Encoded Output: {compressed_output}<br/>
"""

    elements.append(Paragraph(question_text, styles['BodyText']))

    # --------------------------------------------------------
    # STEP-BY-STEP LZW SOLUTION
    # --------------------------------------------------------
    elements.append(Spacer(1, 25))
    elements.append(Paragraph("<b>Step-by-Step LZW Compression Solution</b>", styles['Heading2']))
    elements.append(Spacer(1, 12))

    # Re-run LZW with logging
    dictionary = {ch: idx for idx, ch in enumerate(symbols)}
    dict_size = len(dictionary)
    w = ""
    steps = []

    for c in text:
        wc = w + c
        if wc in dictionary:
            steps.append((w, c, wc, "", ""))  # no output yet
            w = wc
        else:
            steps.append((w, c, wc, dictionary[w], f"{wc} → {dict_size}"))
            dictionary[wc] = dict_size
            dict_size += 1
            w = c

    steps.append((w, "", w, dictionary[w], ""))  # final output

    # Build table
    table_data = [["w", "c", "wc", "Output Code", "New Dictionary Entry"]]

    for w_val, c_val, wc_val, out_val, add_val in steps:
        table_data.append([w_val, c_val, wc_val,
                           "" if out_val == "" else str(out_val),
                           add_val])

    step_table = Table(table_data, colWidths=[60, 60, 70, 80, 150])
    step_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ]))

    elements.append(step_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("<b>Final Encoded Output:</b>", styles['Heading3']))
    elements.append(Paragraph(str(compressed_output), styles['BodyText']))

    # Build PDF
    doc.build(elements)

    return {
        "text": text,
        "compressed_output": compressed_output,
        "dictionary_size": len(dictionary),
        "pdf": pdf_filename
    }

# Run the script
if __name__ == "__main__":
    result = generate_lzw_question()
    print("PDF generated:", result["pdf"])
    print("Input text:", result["text"])
    print("Encoded output:", result["compressed_output"])
