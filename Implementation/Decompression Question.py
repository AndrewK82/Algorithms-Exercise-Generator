import random
import time
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------
SYMBOLS = ['A', 'B', 'C'] # Smaller alphabet makes "Special Case" collisions more likely
INITIAL_DICT = {ch: idx for idx, ch in enumerate(SYMBOLS)}

def compress_for_validation(text):
    """Standard LZW compression to get codes."""
    dictionary = {ch: idx for idx, ch in enumerate(SYMBOLS)}
    dict_size = len(dictionary)
    w = ""
    result = []
    
    for c in text:
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            result.append(dictionary[w])
            dictionary[wc] = dict_size
            dict_size += 1
            w = c
    if w:
        result.append(dictionary[w])
    return result

def check_difficulty(codes):
    """
    Simulates decompression to detect if the 'Special Case' is triggered.
    Returns: (bool) True if Special Case occurred, False otherwise.
    """
    dictionary = {idx: ch for idx, ch in enumerate(SYMBOLS)}
    dict_size = len(dictionary)
    
    w = dictionary[codes[0]]
    # We don't need to store full output, just check logic
    special_case_triggered = False
    
    for k in codes[1:]:
        if k in dictionary:
            entry = dictionary[k]
        elif k == dict_size:
            # THIS IS THE SPECIAL CASE (Code == Next Empty Slot)
            entry = w + w[0]
            special_case_triggered = True
        else:
            raise ValueError("Invalid LZW Sequence")

        # Add new entry to dictionary
        dictionary[dict_size] = w + entry[0]
        dict_size += 1
        w = entry
        
    return special_case_triggered

def generate_decompression_problem(length, force_special_case=False):
    """Generates a list of codes that either DOES or DOES NOT trigger the special case."""
    
    start_time = time.time()
    
    while time.time() - start_time < 5:
        # 1. Generate random string
        # We bias repeats to increase chance of interesting dictionary interaction
        candidate = random.choices(SYMBOLS, weights=[0.4, 0.4, 0.2], k=length)
        text = "".join(candidate)
        
        # 2. Get the codes
        codes = compress_for_validation(text)
        
        # 3. Check if it meets difficulty criteria
        has_special = check_difficulty(codes)
        
        if force_special_case and has_special:
            return text, codes, "Hard (Special Case Triggered)"
        elif not force_special_case and not has_special:
            return text, codes, "Standard (No Edge Cases)"
            
    # Fallback
    return text, codes, "Fallback (Random)"

def generate_decompression_pdf(codes, solution_text, difficulty_label, filename="lzw_decompression.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    elements.append(Paragraph("<b>LZW Decompression Exam</b>", styles['Title']))
    elements.append(Paragraph(f"Difficulty: {difficulty_label}", styles['Heading4']))
    elements.append(Spacer(1, 12))

    # The Question
    question_text = f"""
    <b>Task:</b><br/>
    You have received the following stream of LZW codes:<br/>
    <b>{codes}</b><br/><br/>
    <b>Given:</b><br/>
    1. The alphabet is {{A, B, C}}.<br/>
    2. The initial dictionary is: A=0, B=1, C=2.<br/>
    3. Decode the stream to find the original message.<br/>
    4. Show the dictionary build process.
    """
    elements.append(Paragraph(question_text, styles['BodyText']))
    elements.append(Spacer(1, 20))

    # Blank Student Table
    elements.append(Paragraph("<b>Student Answer Sheet:</b>", styles['Heading3']))
    student_header = [["Input Code", "Output String", "New Dict Entry (Key: Value)"]]
    # Add empty rows for them to fill
    empty_data = student_header + [["", "", ""] for _ in codes]
    
    t_student = Table(empty_data, colWidths=[80, 150, 200])
    t_student.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ROWHEIGHT', (0,0), (-1,-1), 20)
    ]))
    elements.append(t_student)
    elements.append(Spacer(1, 25))
    elements.append(Paragraph("-" * 60, styles['BodyText']))
    elements.append(Spacer(1, 25))

    # ----------------
    # SOLUTION KEY
    # ----------------
    elements.append(Paragraph("<b>Examiner Solution Key</b>", styles['Heading2']))
    
    # Re-simulate for the table
    dictionary = {idx: ch for idx, ch in enumerate(SYMBOLS)}
    dict_size = len(dictionary)
    w = dictionary[codes[0]]
    result = w
    
    # Initial Step (Just output, no dict add)
    sol_data = [["Code", "Output", "Description", "Dict Update"]]
    sol_data.append([str(codes[0]), w, "First code: Output symbol", "-"])
    
    for k in codes[1:]:
        desc = "Standard Lookup"
        if k in dictionary:
            entry = dictionary[k]
        elif k == dict_size:
            entry = w + w[0]
            desc = "<b>SPECIAL CASE (k=Size)</b>"
        
        # New dict entry
        new_entry = w + entry[0]
        sol_data.append([
            str(k), 
            entry, 
            Paragraph(desc, styles['BodyText']), 
            f"{dict_size}: {new_entry}"
        ])
        
        dictionary[dict_size] = new_entry
        dict_size += 1
        w = entry
        result += entry

    t_sol = Table(sol_data, colWidths=[50, 100, 150, 100])
    t_sol.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgreen),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(t_sol)
    
    elements.append(Spacer(1, 15))
    elements.append(Paragraph(f"<b>Final Decoded String:</b> {result}", styles['Heading3']))
    
    doc.build(elements)
    return filename

# ------------------------------------------------------------------
# MAIN EXECUTION
# ------------------------------------------------------------------
if __name__ == "__main__":
    print("--- LZW Decompression Generator ---")
    
    try:
        print("Select Difficulty:")
        print("1. Standard (Bookkeeping only)")
        print("2. Hard (Must contain KwKwK Special Case)")
        choice = input("Choice (1/2): ").strip()
        force_special = (choice == '2')
        
        length = 15 # Good default for decompression
    except:
        force_special = False

    print(f"Searching for a valid sequence (Special Case: {force_special})...")
    
    text, codes, label = generate_decompression_problem(length, force_special)
    
    print(f"Found Sequence: {text}")
    print(f"Codes: {codes}")
    
    pdf_name = generate_decompression_pdf(codes, text, label)
    print(f"PDF Generated: {pdf_name}")