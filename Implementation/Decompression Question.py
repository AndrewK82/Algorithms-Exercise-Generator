import random
import math
import csv
import os
from collections import Counter
 
# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------
 
SYMBOLS   = ['A', 'C', 'G', 'T']
INIT_BITS = 2
INIT_DICT = {ch: idx for idx, ch in enumerate(SYMBOLS)}
 
SCALING_FACTORS = {
    'low_entropy':  0.4,
    'high_entropy': 0.7
}
 
STEP_FACTORS = {
    'high_entropy': 0.65,
    'low_entropy':  0.65
}
 
TOLERANCES = {
    'high_entropy': 1,
    'low_entropy':  3
}
 
ANSWERS_FOLDER   = "Answers"
QUESTIONS_FOLDER = "Questions"
 
# ------------------------------------------------------------------
# FOLDER MANAGEMENT
# ------------------------------------------------------------------
 
def clear_output_folders():
    for folder in [ANSWERS_FOLDER, QUESTIONS_FOLDER]:
        if os.path.exists(folder):
            for f in os.listdir(folder):
                fp = os.path.join(folder, f)
                if os.path.isfile(fp):
                    os.remove(fp)
        else:
            os.makedirs(folder)
 
# ------------------------------------------------------------------
# BIT-WIDTH HELPER
# ------------------------------------------------------------------
 
def bit_width(dict_size):
    return max(INIT_BITS, math.ceil(math.log2(max(dict_size, 2))))
 
# ------------------------------------------------------------------
# DIFFICULTY METRICS
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
 
 
def calculate_execution_step_variance(matches):
    if len(matches) < 2:
        return 0.0
    distinct_pairs = set(
        (matches[i], matches[i + 1])
        for i in range(len(matches) - 1)
    )
    return len(distinct_pairs) / (len(matches) ** 2)
 
# ------------------------------------------------------------------
# LZW COMPRESSION -> produces the binary stream and step trace
# ------------------------------------------------------------------
 
def compress_trace(text):
    dictionary = dict(INIT_DICT)
    dict_size  = len(dictionary)
 
    w = ""
    steps           = []
    bitstream_parts = []
    matches         = []
    bit_pos         = 1
    step_num        = 0
 
    for c in text:
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            code_int  = dictionary[w]
            bw        = bit_width(dict_size)
            code_bin  = format(code_int, f'0{bw}b')
            new_entry = wc
            new_code  = dict_size
 
            steps.append({
                'step':        step_num,
                'position':    bit_pos,
                'old_string':  w if step_num > 0 else '-',
                'code_bits':   code_bin,
                'string':      w,
                'add_to_dict': new_entry,
                'code_num':    new_code,
            })
 
            bitstream_parts.append(code_bin)
            matches.append(w)
            bit_pos  += bw
            dictionary[new_entry] = new_code
            dict_size += 1
            w = c
            step_num += 1
 
    # Final symbol
    code_int = dictionary[w]
    bw       = bit_width(dict_size)
    code_bin = format(code_int, f'0{bw}b')
    steps.append({
        'step':        step_num,
        'position':    bit_pos,
        'old_string':  w if step_num > 0 else '-',
        'code_bits':   code_bin,
        'string':      w,
        'add_to_dict': '-',
        'code_num':    '-',
    })
    bitstream_parts.append(code_bin)
    matches.append(w)
 
    bitstream       = ''.join(bitstream_parts)
    total_bits      = len(bitstream)
    final_dict_size = dict_size
    return bitstream, total_bits, steps, matches, final_dict_size
 
# ------------------------------------------------------------------
# STRING GENERATION
# ------------------------------------------------------------------
 
def generate_sequence(target_length=14, entropy_type='high_entropy', seen=None):
    target_dict_size = calculate_target_dict_size(target_length, entropy_type)
    target_steps     = calculate_target_steps(target_length, entropy_type)
    tolerance        = TOLERANCES[entropy_type]
    max_streak       = 2 if entropy_type == 'high_entropy' else 3
 
    if entropy_type == 'high_entropy':
        weights = [0.25, 0.25, 0.25, 0.25]
    else:
        weights = [0.65, 0.18, 0.10, 0.07]
 
    for _ in range(100000):
        # Seed with one of each symbol to guarantee full alphabet coverage
        text_list  = random.sample(SYMBOLS, len(SYMBOLS))
        text_list += random.choices(SYMBOLS, weights=weights, k=target_length - len(SYMBOLS))
        random.shuffle(text_list)
        text = "".join(text_list)
 
        # Skip duplicates
        if seen is not None and text in seen:
            continue
 
        # Reject sequences with long identical-character runs
        has_streak = any(
            text[i:i+max_streak+1] == text[i]*(max_streak+1)
            for i in range(len(text) - max_streak)
        )
        if has_streak:
            continue
 
        bitstream, total_bits, steps, matches, final_dict_size = compress_trace(text)
        entropy_value = calculate_shannon_entropy(text)
        exec_variance = calculate_execution_step_variance(matches)
        num_steps     = len(steps)
 
        if (abs(final_dict_size - target_dict_size) <= tolerance
                and abs(num_steps - target_steps) <= tolerance
                and len(bitstream) // 8 < target_length):
            return text, bitstream, total_bits, steps, entropy_value, exec_variance, final_dict_size
 
    return text, bitstream, total_bits, steps, calculate_shannon_entropy(text), calculate_execution_step_variance(matches), final_dict_size
 
# ------------------------------------------------------------------
# LaTeX GENERATION
# ------------------------------------------------------------------
 
def build_latex(text, bitstream, total_bits, steps, filename, include_solution=True):
    init_dict_str = ", ".join(
        f"{ch} = {format(i, f'0{INIT_BITS}b')}" for i, ch in enumerate(SYMBOLS)
    )
    spaced_bits = ' '.join(s['code_bits'] for s in steps)
    spaced_text = ' '.join(list(text))
 
    L = []
    L.append(r"\documentclass[11pt]{article}")
    L.append(r"\usepackage{amsmath}")
    L.append(r"\usepackage[utf8]{inputenc}")
    L.append(r"\usepackage[margin=1in]{geometry}")
    L.append(r"\usepackage{helvet}")
    L.append(r"\renewcommand{\familydefault}{\sfdefault}")
    L.append(r"\usepackage[table]{xcolor}")
    L.append(r"\usepackage{array}")
    L.append(r"\begin{document}")
 
    L.append(r"\begin{center}")
    L.append(r"{\Large \textbf{LZW Decompression Question}}")
    L.append(r"\end{center}")
    L.append(r"\vspace{1em}")
 
    L.append(r"\noindent \textit{\textbf{Compressed Bitstream:}}")
    L.append(r"\begin{center}")
    L.append(r"\texttt{" + spaced_bits + r"} \\")
    L.append(r"\vspace{0.5em}")
    L.append(r"File Size: \textbf{" + str(total_bits) + r"} bits")
    L.append(r"\end{center}")
    L.append(r"\vspace{1em}")
 
    if include_solution:
        L.append(r"\noindent \textit{\textbf{Uncompressed Text (Solution):}}")
        L.append(r"\begin{center}")
        L.append(r"\textbf{" + spaced_text + r"}")
        L.append(r"\end{center}")
        L.append(r"\vspace{1em}")
 
    L.append(r"\noindent Parse the bitstream left-to-right to decompress the sequence. \\[1.5em]")
    L.append(r"Start with the initial dictionary: " + init_dict_str + r" (indices 0--3). \\[1.5em]")
    L.append(r"At each step, read enough bits to look up the current code, output the matching string, then add the new dictionary entry. Remember that the bit-width = $\lceil\log_2(\text{dict size})\rceil$ at the time each code is read. Complete the table provided below.")
    L.append(r"\vspace{3em}")
    L.append(r"\par")
 
    if include_solution:
        L.append(r"\noindent {\Large \textbf{Examiner Solution Key}}")
        L.append(r"\vspace{1em}")
 
    L.append(r"\begin{center}")
    L.append(r"\small")
    L.append(r"\renewcommand{\arraystretch}{1.4}")
    L.append(r"\arrayrulecolor{gray}")
    L.append(r"\begin{tabular}{|c|c|c|c|c|c|c|}")
    L.append(r"\hline")
    L.append(r"\rowcolor{lightgray} Step & \shortstack{Position\\in File} & \shortstack{Old\\String} & \shortstack{Code from\\Dictionary} & String & \shortstack{Add to\\Dictionary} & Code \\")
    L.append(r"\hline")
 
    def latex_row(s, blank=False):
        add  = '--' if s['add_to_dict'] == '-' else s['add_to_dict']
        code = '--' if s['code_num']    == '-' else str(s['code_num'])
        if blank:
            return f" {s['step']} & & & & & & \\\\ \\hline"
        return (f" {s['step']} & {s['position']} & {s['old_string'].replace('-', '--')} & "
                f"\\texttt{{{s['code_bits']}}} & {s['string']} & {add} & {code} \\\\ \\hline")
 
    # Step 0 always given as a worked example
    L.append(r"\rowcolor{white!92!black} " + latex_row(steps[0]).lstrip())
 
    for s in steps[1:]:
        L.append(latex_row(s, blank=(not include_solution)))
 
    # Extra blank rows to conceal true step count from students
    if not include_solution:
        for _ in range(4):
            L.append(r" & & & & & & \\ \hline")
 
    L.append(r"\end{tabular}")
    L.append(r"\arrayrulecolor{black}")
    L.append(r"\end{center}")
    L.append(r"\vspace{1em}")
    L.append(r"\end{document}")
 
    with open(filename, "w") as f:
        f.write("\n".join(L))
 
    return filename
 
# ------------------------------------------------------------------
# CSV LOGGING
# ------------------------------------------------------------------
 
def log_metrics(filename, row):
    exists = os.path.exists(filename)
    with open(filename, 'a', newline='') as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow([
                "Q", "Text", "BitStream_Bits", "Num_Steps",
                "Multi_Char_Steps", "Final_Dict_Size",
                "Entropy", "Execution_Step_Variance"
            ])
        writer.writerow(row)
 
# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
 
def main():
    clear_output_folders()
    print("--- LZW Decompression Question Generator ---")
    try:
        print("Select Complexity Profile:\n1. High Entropy\n2. Low Entropy")
        choice = input("Choice (1 or 2): ").strip()
        entropy_type = 'high_entropy' if choice != '2' else 'low_entropy'
 
        length = int(input("Enter string length (8-30): "))
        length = max(8, min(length, 30))
 
        num_questions = int(input("How many questions to generate? "))
        num_questions = max(1, num_questions)
    except ValueError:
        entropy_type, length, num_questions = 'high_entropy', 14, 3
 
    seen = set()
    i = 1
    while i <= num_questions:
        print(f"\n--- Generating Question {i} ---")
        text, bitstream, total_bits, steps, entropy_value, exec_variance, final_dict_size = generate_sequence(
            length, entropy_type, seen=seen
        )
 
        # Skip duplicates
        if text in seen:
            continue
        seen.add(text)
 
        multi = sum(1 for s in steps if len(s['string']) > 1)
 
        answer_tex   = os.path.join(ANSWERS_FOLDER,   f"lzw_decomp_answer_{i}.tex")
        question_tex = os.path.join(QUESTIONS_FOLDER, f"lzw_decomp_question_{i}.tex")
 
        build_latex(text, bitstream, total_bits, steps,
                    filename=answer_tex, include_solution=True)
        build_latex(text, bitstream, total_bits, steps,
                    filename=question_tex, include_solution=False)
 
        log_metrics("decompression_metrics.csv", [
            i, text, total_bits, len(steps), multi, final_dict_size,
            round(entropy_value, 3), round(exec_variance, 3)
        ])
 
        print(f"  String:             {text}")
        print(f"  Entropy:            {entropy_value:.3f} bits")
        print(f"  Execution Step Variance: {exec_variance:.3f}")
        print(f"  Steps:              {len(steps)}")
        print(f"  Dict size:          {final_dict_size}")
        print(f"  Answer File:        {answer_tex}")
        print(f"  Question File:      {question_tex}")
 
        i += 1
 
 
if __name__ == "__main__":
    main()