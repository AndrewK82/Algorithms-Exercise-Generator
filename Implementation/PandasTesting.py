import random
import math
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

SYMBOLS = ['A', 'C', 'T', 'G']
SCALING_FACTORS = {'low_entropy': 0.4, 'high_entropy': 0.7}

def simulate_lzw(text):
    dictionary = {ch: idx for idx, ch in enumerate(SYMBOLS)}
    dict_size = len(dictionary)
    w, output = "", []
    for c in text:
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            output.append(dictionary[w])
            dictionary[wc] = dict_size
            dict_size += 1
            w = c
    if w: output.append(dictionary[w])
    return dict_size, output

def generate_smart_lzw_string(length, entropy_type):
    # 1. Define the Strict Formula
    # We use int() to floor the value, creating a deterministic "step" 
    # for every length.
    target_dict_size = len(SYMBOLS) + int(length * SCALING_FACTORS[entropy_type])
    
    # Weights to bias generation towards the likely complexity
    weights = [0.6, 0.2, 0.1, 0.1] if entropy_type == 'low_entropy' else [0.25]*4
    
    while True:
        text = "".join(random.choices(SYMBOLS, weights=weights, k=length))
        d_size, compressed = simulate_lzw(text)
        
        # 2. Strict Check: Accept ONLY if it matches the formula exactly.
        # This ensures the output is "unique" for this length (no variance).
        if d_size == target_dict_size:
            return text, d_size, compressed

def run_lzw_study(min_len=8, max_len=50):
    results = []
    
    for length in range(min_len, max_len + 1):
        # Generate independently for this length
        text, d_size, compressed_out = generate_smart_lzw_string(length, 'low_entropy')
        
        orig_bits = length * 8
        bit_width = math.ceil(math.log2(d_size))
        comp_bits = len(compressed_out) * bit_width
        savings = (1 - (comp_bits / orig_bits)) * 100
        
        results.append({
            "Length": length,
            "Dict Size": d_size,
            "Compression %": savings,
            "Efficiency": orig_bits / comp_bits 
        })
    return pd.DataFrame(results)

# Generate Data
df = run_lzw_study(8, 50)

# Create Visualizations
plt.figure(figsize=(12, 5))

# Plot 1: Compression Scaling
plt.subplot(1, 2, 1)
sns.lineplot(data=df, x="Length", y="Compression %", marker='o', color='teal')
plt.axhline(0, color='red', linestyle='--')
plt.title("Compression Savings vs String Length")
plt.grid(True, alpha=0.3)

# Plot 2: Dictionary Growth
plt.subplot(1, 2, 2)
sns.regplot(data=df, x="Length", y="Dict Size", color='purple', ci=None)
plt.title("Dictionary Growth (Strict Formula Compliance)")
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

print(df.head(10))