import random
import math
import csv
import os
from collections import Counter

# ------------------------------------------------------------------
# CONFIGURATION & DIFFICULTY CONSTANTS
# ------------------------------------------------------------------

SYMBOLS = ['A', 'C', 'G', 'T']

SCALING_FACTORS = {
    'low_entropy': 0.4,
    'high_entropy': 0.7
}

STEP_FACTORS = {
    'high_entropy': 0.65,
    'low_entropy':  0.50
}

# Acceptance tolerance — low entropy needs more slack as skewed
# distributions make simultaneous targets harder to hit
TOLERANCES = {
    'high_entropy': 1,
    'low_entropy':  3
}

ANSWERS_FOLDER = "Answers"
QUESTIONS_FOLDER = "Questions"

# ------------------------------------------------------------------
# CLEAR OUTPUT FOLDERS
# ------------------------------------------------------------------

def clear_output_folders():
    for folder in [ANSWERS_FOLDER, QUESTIONS_FOLDER]:
        if os.path.exists(folder):
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        else:
            os.makedirs(folder)

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


def calculate_target_dict_size(length, entropy_type):
    base_size = len(SYMBOLS)
    growth = int(length * SCALING_FACTORS[entropy_type])
    return base_size + max(3, growth)


def calculate_target_steps(length, entropy_type):
    return max(4, int(length * STEP_FACTORS[entropy_type]))

# ------------------------------------------------------------------
# LZW SIMULATION
# ------------------------------------------------------------------

def simulate_lzw(text):
    """Simulate LZW compression, returning dict size, output codes, and match sequence."""
    dictionary = {ch: idx for idx, ch in enumerate(SYMBOLS)}
    dict_size = len(dictionary)
    w = ""
    output = []
    matches = []
    for c in text:
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            if w:
                output.append(dictionary[w])
                matches.append(w)
            dictionary[wc] = dict_size
            dict_size += 1
            w = c
    if w:
        output.append(dictionary[w])
        matches.append(w)
    return dict_size, output, matches


def calculate_execution_step_variance(matches):
    """
    Measures how varied the dictionary matches are across execution steps.
    Counts distinct adjacent match pairs normalised by total possible pairs.
    Higher score = more varied execution = more interesting question.
    Logged as a diagnostic metric alongside each generated exercise.
    """
    if len(matches) < 2:
        return 0.0
    distinct_pairs = set(
        (matches[i], matches[i + 1])
        for i in range(len(matches) - 1)
    )
    return len(distinct_pairs) / (len(matches) ** 2)

# ------------------------------------------------------------------
# STRING GENERATION
# ------------------------------------------------------------------

def generate_smart_lzw_string(length, entropy_type, seen=None):
    target_dict_size = calculate_target_dict_size(length, entropy_type)
    target_steps = calculate_target_steps(length, entropy_type)
    tolerance = TOLERANCES[entropy_type]

    # Max allowed consecutive characters to keep it looking "clean"
    max_streak = 2 if entropy_type == 'high_entropy' else 3

    # Character weights by profile:
    # High entropy: uniform distribution — targets maximum Shannon entropy
    # Low entropy: skewed but not extreme — keeps variety across a batch
    if entropy_type == 'high_entropy':
        weights = [0.25, 0.25, 0.25, 0.25]
    else:
        weights = [0.65, 0.18, 0.10, 0.07]

    for _ in range(100000):
        # Seed with one of each symbol to guarantee full alphabet coverage
        text_list = random.sample(SYMBOLS, len(SYMBOLS))
        text_list += random.choices(SYMBOLS, weights=weights, k=length - 4)
        random.shuffle(text_list)
        text = "".join(text_list)

        # Skip if this string has already been generated in this batch
        if seen is not None and text in seen:
            continue

        # Reject sequences with long identical-character runs
        has_streak = any(
            text[i:i+max_streak+1] == text[i]*(max_streak+1)
            for i in range(len(text)-max_streak)
        )
        if has_streak:
            continue

        d_size, compressed, matches = simulate_lzw(text)
        entropy_value = calculate_shannon_entropy(text)
        exec_variance = calculate_execution_step_variance(matches)
        steps = len(compressed)

        if (abs(d_size - target_dict_size) <= tolerance
                and abs(steps - target_steps) <= tolerance
                and len(compressed) < len(text)):
            return text, d_size, compressed, entropy_value, exec_variance

    return text, d_size, compressed, calculate_shannon_entropy(text), calculate_execution_step_variance(matches)


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
                "Question", "Sequence", "Entropy", "Final_Dict_Size",
                "Compressed_Length", "Original_Length", "Steps",
                "Execution_Step_Variance"
            ])
        writer.writerow(row)

# ------------------------------------------------------------------
# LATEX GENERATION
# ------------------------------------------------------------------

def generate_latex_report(text, compressed_out, final_dict_size, filename="lzw_compression.tex", include_solution=True):
    dictionary = {ch: idx for idx, ch in enumerate(SYMBOLS)}
    dict_size = len(dictionary)
    w = ""
    history = []
    step_counter = 1
    w_start_pos = 1
    total_compressed_bits = 0
    original_bits = len(text) * 8
    output = []

    for i, c in enumerate(text):
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            if w:
                current_bit_width = max(1, math.ceil(math.log2(dict_size)))
                binary_code = format(dictionary[w], f'0{current_bit_width}b')
                total_compressed_bits += current_bit_width
                history.append([str(step_counter), str(w_start_pos), w, str(current_bit_width), binary_code, wc, str(dict_size)])
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
        history.append([str(step_counter), str(w_start_pos), w, str(current_bit_width), binary_code, "-", "-"])
        output.append(dictionary[w])

    latex = []
    latex.append(r"\documentclass[11pt]{article}")
    latex.append(r"\usepackage[utf8]{inputenc}")
    latex.append(r"\usepackage[margin=1in]{geometry}")
    latex.append(r"\usepackage{helvet}")
    latex.append(r"\renewcommand{\familydefault}{\sfdefault}")
    latex.append(r"\usepackage[table]{xcolor}")
    latex.append(r"\usepackage{array}")
    latex.append(r"\begin{document}")
    latex.append(r"\begin{center}")
    latex.append(r"{\Large \textbf{LZW Compression Question}}")
    latex.append(r"\end{center}")
    latex.append(r"\vspace{1em}")
    latex.append(r"\noindent \textit{\textbf{Input Sequence:}}")
    latex.append(r"\begin{center}")
    latex.append(r"\renewcommand{\arraystretch}{1.5}")
    col_format = "|" + "c|" * len(text)
    latex.append(r"\begin{tabular}{" + col_format + "}")
    latex.append(r"\hline")
    latex.append(r"\rowcolor{white!95!black} " + " & ".join(list(text)) + r" \\")
    latex.append(r"\hline")
    latex.append(r"\end{tabular}")
    latex.append(r"\end{center}")
    latex.append(r"\vspace{1em}")
    latex.append(r"\noindent Using the LZW algorithm, compress the sequence from left to right. \\[1.5em]")
    latex.append(r"Start with the initial dictionary: A = 00, C = 01, G = 10, and T = 11 (Indices 0--3). \\[1.5em]")
    latex.append(r"At each step, identify the longest matching string in the dictionary and output its binary code. Form a new dictionary entry by appending the next symbol in the sequence to the current match, assigning it the next available integer index. Complete the table provided below.")
    latex.append(r"\vspace{3em}")
    latex.append(r"\par")

    if include_solution:
        latex.append(r"\noindent {\Large \textbf{Examiner Solution Key}}")
        latex.append(r"\vspace{1em}")

    latex.append(r"\begin{center}")
    latex.append(r"\small")
    latex.append(r"\renewcommand{\arraystretch}{1.4}")
    latex.append(r"\arrayrulecolor{gray}")
    latex.append(r"\begin{tabular}{|c|c|c|c|c|c|c|}")
    latex.append(r"\hline")
    latex.append(r"\rowcolor{lightgray} Step & Position in String & Longest String in Dictionary & k & Binary Encoding & String Added & Code Created \\")
    latex.append(r"\hline")

    if include_solution:
        for row in history:
            latex.append(" & ".join(row) + r" \\ \hline")
    else:
        if history:
            latex.append(r"\rowcolor{white!92!black} " + " & ".join(history[0]) + r" \\ \hline")
        for _ in range(len(history) + 4):
            latex.append(r" & & & & & & \\ \hline")

    latex.append(r"\end{tabular}")
    latex.append(r"\arrayrulecolor{black}")
    latex.append(r"\end{center}")
    latex.append(r"\vspace{1em}")
    latex.append(r"\end{document}")

    with open(filename, "w") as f:
        f.write("\n".join(latex))

    return filename


def main():
    clear_output_folders()
    print("--- LZW LaTeX Question Generator ---")
    try:
        length = int(input("Enter string length (8-30): "))
        length = max(8, min(length, 30))
        print("Select Complexity Profile:\n1. High Entropy\n2. Low Entropy")
        choice = input("Choice (1 or 2): ").strip()
        entropy = 'high_entropy' if choice == '1' else 'low_entropy'
        num_questions = int(input("How many questions to generate? "))
        num_questions = max(1, num_questions)
    except ValueError:
        length, entropy, num_questions = 15, 'high_entropy', 5

    seen = set()
    i = 1
    while i <= num_questions:
        print(f"\n--- Generating Question {i} ---")
        text, d_size, out, entropy_value, exec_variance = generate_smart_lzw_string(
            length, entropy, seen=seen
        )

        # Skip duplicates — can happen when sample space is small
        if text in seen:
            print(f"  Duplicate detected, retrying...")
            continue
        seen.add(text)

        answer_tex = os.path.join(ANSWERS_FOLDER, f"lzw_answer_{i}.tex")
        question_tex = os.path.join(QUESTIONS_FOLDER, f"lzw_question_{i}.tex")

        generate_latex_report(text, out, d_size, filename=answer_tex, include_solution=True)
        generate_latex_report(text, out, d_size, filename=question_tex, include_solution=False)

        log_question_data("question_metrics.csv", [
            i, text, round(entropy_value, 3), d_size,
            len(out), len(text), len(out), round(exec_variance, 3)
        ])

        print(f"  String:             {text}")
        print(f"  Entropy:            {entropy_value:.3f} bits")
        print(f"  Execution Step Variance: {exec_variance:.3f}")
        print(f"  Steps:              {len(out)}")
        print(f"  Dict size:          {d_size}")
        print(f"  Answer File:        {answer_tex}")
        print(f"  Question File:      {question_tex}")

        i += 1


if __name__ == "__main__":
    main()
