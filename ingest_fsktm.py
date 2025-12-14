import sqlite3
import re
import os

# SETTINGS
# Ensure this path matches exactly where you put your text file
TXT_PATH = "data/handbook/txt/fsktm.txt"
DB_PATH = "academic.db"

def ingest_fsktm_txt_data():
    print(f"[INFO] Reading {TXT_PATH} for extraction...")
    
    # 1. Initialize Database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create Tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS courses 
                      (course_code TEXT PRIMARY KEY, course_name TEXT, credit_hours INTEGER, description TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS prerequisites 
                      (course_code TEXT, prereq_code TEXT)''')

    # 2. Read Text from File
    if not os.path.exists(TXT_PATH):
        print(f"[ERROR] ❌ File not found: {TXT_PATH}")
        print("Please convert your PDF to text and place it in that folder.")
        return

    with open(TXT_PATH, 'r', encoding='utf-8') as f:
        full_text = f.read()

    # 3. Parse Data using Regex
    # Strategy: Split by course headers (Course Code + Title + Credit Hours on same line)
    course_blocks = re.split(r'\n(?=[A-Z]{3}\d{4}\s+.+?\d+\(\d+\+\d+\))', full_text)
    
    count = 0
    for block in course_blocks:
        if not block.strip():
            continue
            
        # Extract course code from the first line
        # Looks for: CCS3101 [Space] Title... [Space] 3(2+1)
        code_match = re.match(r'([A-Z]{3}\d{4})\s+(.+?)(\d+)\(\d+\+\d+\)', block)
        
        if not code_match:
            # Fallback if credit format is weird
            # Just grab Code and Title
            code_match = re.match(r'([A-Z]{3}\d{4})\s+(.+)', block)
            if not code_match: continue
            
            code = code_match.group(1)
            title_line = code_match.group(2)
            credits = 3 # Default if not found
        else:
            code = code_match.group(1)
            title_line = code_match.group(2)
            credits = int(code_match.group(3)) # Capture the '3' from '3(2+1)'
        
        # Clean up the block
        clean_content = block.replace("\n", " ").strip()
        name = title_line.strip()

        # B. Extract Synopsis (English only - capture complete description)
        desc = "Synopsis not available in handbook."
        # Match from "This course" and capture everything until the paragraph ends (typically at course code or end)
        desc_match = re.search(r"This course (?:covers|comprises|includes|introduces|is|encompasses|provides|exposes|consists|offers).*?(?=\s+[A-Z]{3}\d{4}|$)", clean_content, re.IGNORECASE | re.DOTALL)
        if desc_match:
            # Get the match and trim to the last complete sentence
            raw_desc = desc_match.group(0).strip()
            # Find the last period to ensure we have complete sentences
            last_period = raw_desc.rfind('.')
            if last_period > 0:
                desc = raw_desc[:last_period + 1].strip()

        # C. Extract Prerequisite(s)
        prereq_codes = []  # List to store multiple prerequisites
        prereq_match = re.search(r'Prasyarat\s*:\s*([^\n]+?)(?=\s+(?:Kursus|This course|Melalui|$))', clean_content, re.IGNORECASE)
        
        if prereq_match:
            prereq_text = prereq_match.group(1).strip()
            
            # Check if it's "Tiada" (None)
            if "Tiada" in prereq_text or "None" in prereq_text:
                prereq_codes = []
            # Check if it requires department permission
            elif "Dengan Kebenaran" in prereq_text:
                # Store as special code and also extract any course codes that might be with it
                prereq_codes = re.findall(r'[A-Z]{3}\d{4}', prereq_text)
                prereq_codes.append("DEPT_PERMISSION")  # Add special marker
            else:
                # Find ALL course codes (e.g., CCS3100, CND4500 atau CCS4500, CCS3101 & CND3200)
                prereq_codes = re.findall(r'[A-Z]{3}\d{4}', prereq_text)

        # D. Insert into Database
        try:
            # Insert Course Info (Now including credits!)
            cursor.execute("INSERT OR REPLACE INTO courses (course_code, course_name, credit_hours, description) VALUES (?, ?, ?, ?)", 
                           (code, name, credits, desc))
            
            # Delete old prerequisites for this course to prevent duplicates
            cursor.execute("DELETE FROM prerequisites WHERE course_code = ?", (code,))
            
            # Insert ALL Prerequisites
            for prereq_code in prereq_codes:
                cursor.execute("INSERT INTO prerequisites (course_code, prereq_code) VALUES (?, ?)", 
                               (code, prereq_code))
            
            # Display all prerequisites with readable format for DEPT_PERMISSION
            if prereq_codes:
                display_codes = ["Dengan Kebenaran Jabatan" if p == "DEPT_PERMISSION" else p for p in prereq_codes]
                prereq_display = ", ".join(display_codes)
            else:
                prereq_display = "None"
            print(f"[OK] Imported: {code} | Credits: {credits} | Prereq: {prereq_display}")
            count += 1
            
        except Exception as e:
            print(f"[ERROR] Error inserting {code}: {e}")

    conn.commit()
    conn.close()
    print(f"\n[SUCCESS] Successfully imported {count} courses from text file.")

if __name__ == "__main__":
    ingest_fsktm_txt_data()