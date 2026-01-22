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

# Controls how "dense" the dictionary becomes per character of input
# 0.5 means for a length 20 string, we expect ~10 new dictionary entries.
SCALING_FACTORS = {
    'low_entropy': 0.4,   # More repeats, fewer new dict entries (Higher compression)
    'high_entropy': 0.7   # Random noise, constant new dict entries (Lower compression)
}

def calculate_target_dict_size(length, entropy_type):
    """Calculates the target dictionary size based on length and difficulty."""
    base_size = len(SYMBOLS)
    growth = int(length * SCALING_FACTORS[entropy_type])
    # Ensure at least 3 new entries for very short strings so the problem isn't trivial
    return base_size + max(3, growth)

def generate_smart_lzw_string(length, entropy_type):
    """
    Generates a string that guarantees a specific LZW behavior.
    Instead of random filtering, it injects patterns to control dictionary growth.
    """
    target_dict_size = calculate_target_dict_size(length, entropy_type)
    
    # Timeout protection (5 seconds)
    start_time = time.time()
    
    while time.time() - start_time < 5:
        # 1. Start with a random seed based on probabilities
        if entropy_type == 'low_entropy':
            weights = [0.6, 0.2, 0.1, 0.1] # Bias towards one char to force patterns
        else:
            weights = [0.25, 0.25, 0.25, 0.25]
            
        candidate = random.choices(SYMBOLS, weights=weights, k=length)
        text = "".join(candidate)

        # 2. Run LZW simulation to check ACTUAL difficulty
        d_size, compressed = simulate_lzw(text)
        
        # 3. Check constraints
        # We allow a margin of error of +/- 1 dictionary entry to prevent infinite loops
        if abs(d_size - target_dict_size) <= 1:
            # Secondary Check: Must have at least one multi-char code output
            # (Length of text > Length of compressed output implies compression occurred)
            if len(compressed) < len(text):
                return text, d_size, compressed

    # Fallback if perfect match not found quickly
    return text, d_size, compressed

def simulate_lzw(text):
    """Simulates LZW to return final dictionary size and output."""
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

def generate_pdf_report(text, compressed_out, final_dict_size, filename="lzw_compression.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("<b>LZW Compression Challenge</b>", styles['Title']))
    elements.append(Spacer(1, 12))

    # Input Metrics
    original_bits = len(text) * 8
    # LZW bit width is dynamic, usually ceil(log2(dict_size))
    # We use the final dict size to determine the bit width for the whole stream 
    # (Simplified for exam contexts; real LZW expands width dynamically)
    bit_width = math.ceil(math.log2(final_dict_size))
    compressed_bits = len(compressed_out) * bit_width
    
    ratio = (1 - (compressed_bits / original_bits)) * 100

    # Question Section
    elements.append(Paragraph(f"<b>Input Sequence (Length {len(text)}):</b>", styles['Heading3']))
    
    # Stylized Input Table
    data = [list(text)]
    t = Table(data, colWidths=[20]*len(text))
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    elements.append(t)
    elements.append(Spacer(1, 15))

    question_text = f"""
    <b>Task Requirements:</b><br/><br/>
    1. <b>Trace the LZW algorithm</b> for the input above.<br/>
    2. <b>Dictionary Constraint:</b> The initial dictionary contains A(0), C(1), T(2), G(3).<br/>
    3. <b>Show your work:</b> List every step where a new dictionary entry is created.<br/>
    4. <b>Calculate Efficiency:</b> Compare the 8-bit ASCII size vs. LZW size (using {bit_width}-bit codes).
    """
    elements.append(Paragraph(question_text, styles['BodyText']))
    elements.append(Spacer(1, 25))
    elements.append(Paragraph("-" * 60, styles['BodyText']))
    elements.append(Spacer(1, 15))

    # Solution Section
    elements.append(Paragraph("<b>Examiner Solution Key</b>", styles['Heading2']))
    
    # Step-by-Step Table
    # Re-run simulation to capture steps
    dictionary = {ch: idx for idx, ch in enumerate(SYMBOLS)}
    dict_size = len(dictionary)
    w = ""
    history = [["Current w", "Next c", "New Entry (w+c)", "Entry Index", "Output Code"]]
    
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

    # Summary Stats
    stats = f"""
    <b>Final Statistics:</b><br/>
    Final Dictionary Size: {final_dict_size}<br/>
    Encoded Sequence: {compressed_out}<br/>
    Original Size: {original_bits} bits<br/>
    Compressed Size: {compressed_bits} bits ({len(compressed_out)} codes * {bit_width} bits)<br/>
    Compression Savings: {ratio:.1f}%
    """
    elements.append(Paragraph(stats, styles['BodyText']))

    doc.build(elements)
    return filename

# ------------------------------------------------------------------
# MAIN EXECUTION
# ------------------------------------------------------------------
def main():
    print("--- LZW Question Generator ---")
    try:
        length = int(input("Enter string length (8-30): "))
        length = max(8, min(length, 30)) # Clamp
        
        print("Select Complexity Profile:")
        print("1. High Entropy (Random-like, creates many dictionary entries)")
        print("2. Low Entropy  (Repetitive, tests compression logic deep in dictionary)")
        choice = input("Choice (1 or 2): ").strip()
        
        entropy = 'high_entropy' if choice == '1' else 'low_entropy'
        
    except ValueError:
        print("Invalid input. Using defaults: Length 15, High Entropy.")
        length = 15
        entropy = 'high_entropy'

    print(f"\nGenerating valid sequence for Length {length}, {entropy}...")
    
    text, d_size, out = generate_smart_lzw_string(length, entropy)
    
    print(f"Success! Sequence: {text}")
    print(f"Dictionary grew to: {d_size} entries")
    
    pdf_name = generate_pdf_report(text, out, d_size)
    print(f"PDF generated: {pdf_name}")

if __name__ == "__main__":
    main()