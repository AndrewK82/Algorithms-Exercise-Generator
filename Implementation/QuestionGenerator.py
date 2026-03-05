import random
import math
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
# STEP CONTROL
# ------------------------------------------------------------------

def calculate_target_steps(length):
    return max(4, int(length * 0.65))


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
            if w:
                output.append(dictionary[w])
            dictionary[wc] = dict_size
            dict_size += 1
            w = c
    if w:
        output.append(dictionary[w])
    return dict_size, output


# ------------------------------------------------------------------
# SMART STRING GENERATION
# ------------------------------------------------------------------

def generate_smart_lzw_string(length, entropy_type):
    target_dict_size = calculate_target_dict_size(length, entropy_type)
    target_steps = calculate_target_steps(length)

    for _ in range(100000):

        if entropy_type == 'low_entropy':
            weights = [0.6, 0.2, 0.1, 0.1]
        else:
            weights = [0.25, 0.25, 0.25, 0.25]

        # ensure A,C,T,G all appear
        text_list = random.sample(SYMBOLS, len(SYMBOLS))
        text_list += random.choices(SYMBOLS, weights=weights, k=length-4)

        random.shuffle(text_list)

        text = "".join(text_list)

        d_size, compressed = simulate_lzw(text)
        entropy_value = calculate_shannon_entropy(text)

        steps = len(compressed)

        if (
            abs(d_size - target_dict_size) <= 1
            and abs(steps - target_steps) <= 1
            and len(compressed) < len(text)
        ):
            return text, d_size, compressed, entropy_value

    return text, d_size, compressed, entropy_value


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
                "Original_Length",
                "Steps"
            ])
        writer.writerow(row)


# ------------------------------------------------------------------
# PDF GENERATION
# ------------------------------------------------------------------

def generate_pdf_report(text, compressed_out, final_dict_size, filename="lzw_compression.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph("<b>LZW Compression Challenge</b>", styles['Title']))
    elements.append(Spacer(1, 12))
    original_bits = len(text) * 8
    dictionary = {ch: idx for idx, ch in enumerate(SYMBOLS)}
    dict_size = len(dictionary)

    w = ""
    output = []
    history = [["Step", "Position", "Longest String", "Binary Encoding", "String Added", "Code Given"]]

    step_counter = 1
    w_start_pos = 1
    total_compressed_bits = 0
    for i, c in enumerate(text):
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            if w:
                current_bit_width = max(1, math.ceil(math.log2(dict_size)))
                binary_code = format(dictionary[w], f'0{current_bit_width}b')

                total_compressed_bits += current_bit_width

                history.append([
                    str(step_counter),
                    str(w_start_pos),
                    w,
                    binary_code,
                    wc,
                    str(dict_size)
                ])
                output.append(dictionary[w])
                step_counter += 1
            dictionary[wc] = dict_size
            dict_size += 1
            w = c
            w_start_pos = i + 1

    if w:
        current_bit_width = max(1, math.ceil(math.log2(dict_size)))
        binary_code = format(dictionary[w], f'0{current_bit_width}b')
        total_compressed_bits += current_bit_width
        history.append([
            str(step_counter),
            str(w_start_pos),
            w,
            binary_code,
            "-",
            "-"
        ])
        output.append(dictionary[w])
    ratio = (1 - total_compressed_bits / original_bits) * 100
    elements.append(Paragraph(f"<b>Input Sequence (Length {len(text)}):</b>", styles['Heading3']))

    t = Table([list(text)], colWidths=[20]*len(text))

    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))

    elements.append(t)
    elements.append(Spacer(1, 15))

    question_text = """
    <b>Task Requirements:</b><br/><br/>
    1. Show the step and position in the string.<br/>
    2. Identify the longest matching string in the dictionary.<br/>
    3. Provide the binary encoding using the minimum number of bits required for the <i>current</i> dictionary size.<br/>
    4. Record the new string added to the dictionary and its integer code.
    """

    elements.append(Paragraph(question_text, styles['BodyText']))
    elements.append(Spacer(1, 25))
    elements.append(Paragraph("<b>Examiner Solution Key</b>", styles['Heading2']))

    t_steps = Table(history)

    t_steps.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 9)
    ]))

    elements.append(t_steps)
    elements.append(Spacer(1, 15))

    stats = f"""
    <b>Final Statistics:</b><br/>
    Dictionary Size: {len(dictionary)}<br/>
    Encoded Output: {output}<br/>
    Original Size: {original_bits} bits<br/>
    Compressed Size: {total_compressed_bits} bits<br/>
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
        print(f"LZW Steps: {len(out)}")

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
                len(text),
                len(out)
            ]
        )
        print(f"PDF generated: {pdf_name}")

if __name__ == "__main__":
    main()