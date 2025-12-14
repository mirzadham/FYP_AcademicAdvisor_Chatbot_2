import sqlite3
import re
import os
import sys

# SETTINGS
DB_PATH = "academic.db"

# List of handbook files to process
HANDBOOK_FILES = [
    "data/handbook/txt/fsktm.txt"
]

def ingest_handbook_file(txt_path, conn):
    """
    Ingest a single handbook text file into the database.
    
    Args:
        txt_path: Path to the text file
        conn: SQLite database connection
    
    Returns:
        Number of courses imported
    """
    print(f"\n[INFO] Processing {txt_path}...")
    
    if not os.path.exists(txt_path):
        print(f"[WARNING] ⚠️ File not found: {txt_path} - Skipping...")
        return 0
    
    cursor = conn.cursor()
    
    # Read Text from File
    with open(txt_path, 'r', encoding='utf-8') as f:
        full_text = f.read()
    
    # Parse Data using Regex
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

        # Extract Synopsis (English only - capture complete description)
        desc = "Synopsis not available in handbook."
        # Match from "This course" and capture everything until the paragraph ends
        desc_match = re.search(r"This course (?:covers|comprises|includes|introduces|is|encompasses|provides|exposes|consists|offers).*?(?=\s+[A-Z]{3}\d{4}|$)", clean_content, re.IGNORECASE | re.DOTALL)
        if desc_match:
            # Get the match and trim to the last complete sentence
            raw_desc = desc_match.group(0).strip()
            # Find the last period to ensure we have complete sentences
            last_period = raw_desc.rfind('.')
            if last_period > 0:
                desc = raw_desc[:last_period + 1].strip()

        # Extract Prerequisite(s)
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

        # Insert into Database
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
    
    return count


def ingest_all_handbooks(file_list=None):
    """
    Ingest all handbook files into the database.
    
    Args:
        file_list: Optional list of specific files to ingest. If None, ingest all handbooks.
    """
    print("=" * 70)
    print("UNIFIED HANDBOOK INGESTION SCRIPT")
    print("=" * 70)
    
    # Initialize Database
    print(f"\n[INFO] Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create Tables if they don't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS courses 
                      (course_code TEXT PRIMARY KEY, course_name TEXT, credit_hours INTEGER, description TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS prerequisites 
                      (course_code TEXT, prereq_code TEXT)''')
    
    # Determine which files to process
    files_to_process = file_list if file_list else HANDBOOK_FILES
    
    total_count = 0
    
    # Process each handbook file
    for txt_path in files_to_process:
        count = ingest_handbook_file(txt_path, conn)
        total_count += count
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 70)
    print(f"[SUCCESS] Successfully imported {total_count} courses total from {len(files_to_process)} handbook(s).")
    print("=" * 70)


if __name__ == "__main__":
    # Check if specific file(s) are provided as arguments
    if len(sys.argv) > 1:
        # Process specific files from command line arguments
        files = sys.argv[1:]
        print(f"[INFO] Processing specific file(s): {', '.join(files)}")
        ingest_all_handbooks(files)
    else:
        # Process all handbooks
        print(f"[INFO] Processing all handbooks...")
        ingest_all_handbooks()
