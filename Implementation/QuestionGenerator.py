import random
import math
import re

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

    # Entropy-based symbol distributions (Shannon 1948) ---
    if entropy_level == "low":
        # Strongly skewed → predictable → low entropy (< 1 bit)
        probabilities = [0.80, 0.10, 0.05, 0.05]
    else:
        # Uniform → maximally unpredictable → high entropy (= 2 bits)
        probabilities = [0.25, 0.25, 0.25, 0.25]

    # --- Generate valid text ---
    while True:
        # sample symbols using Shannon-inspired probabilities
        text = ''.join(random.choices(symbols, probabilities) for _ in range(text_length))

        # (a) ensure minimal appearance of each symbol
        if not all(text.count(ch) >= 2 for ch in symbols):
            continue
        
        # (b) ensure enough repeating substrings
        repeats = {text[i:i+2] for i in range(len(text)-1) if text.count(text[i:i+2]) > 1}
        if len(repeats) < repeats_required:
            continue

        # (c) avoid very long runs (makes it TOO low entropy)
        if re.search(r'(.)\1{3,}', text):
            continue

        break

    # Step 3 — Simulate LZW compression (max dict size = 11)
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
