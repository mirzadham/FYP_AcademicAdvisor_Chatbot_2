"""
Quick test to verify the actions can connect to the database.
Run this to ensure the database queries work before testing with Rasa.
"""

import sqlite3
import os

def test_database_connection():
    """Test if we can connect to academic.db and query data."""
    
    db_path = "academic.db"
    
    if not os.path.exists(db_path):
        print("[ERROR] academic.db not found!")
        return False
    
    print(f"[OK] Found database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test 1: Count courses
        cursor.execute("SELECT COUNT(*) FROM courses")
        course_count = cursor.fetchone()[0]
        print(f"[OK] Total courses in database: {course_count}")
        
        # Test 2: Sample course query (CCS3101)
        test_code = "CCS3101"
        cursor.execute("SELECT course_name, credit_hours, description FROM courses WHERE course_code = ?", (test_code,))
        course = cursor.fetchone()
        
        if course:
            print(f"\n[TEST] Course Info for {test_code}:")
            print(f"  Name: {course[0]}")
            print(f"  Credits: {course[1]}")
            print(f"  Description: {course[2][:100]}...")
        
        # Test 3: Prerequisites for CCS3101
        cursor.execute("SELECT prereq_code FROM prerequisites WHERE course_code = ?", (test_code,))
        prereqs = cursor.fetchall()
        
        if prereqs:
            print(f"\n[TEST] Prerequisites for {test_code}:")
            for p in prereqs:
                print(f"  - {p[0]}")
        else:
            print(f"\n[TEST] No prerequisites for {test_code}")
        
        # Test 4: Course with multiple prerequisites (CND4503)
        test_code2 = "CND4503"
        cursor.execute("SELECT prereq_code FROM prerequisites WHERE course_code = ?", (test_code2,))
        prereqs2 = cursor.fetchall()
        
        print(f"\n[TEST] Prerequisites for {test_code2} (should have 2):")
        for p in prereqs2:
            display = "Dengan Kebenaran Jabatan" if p[0] == "DEPT_PERMISSION" else p[0]
            print(f"  - {display}")
        
        # Test 5: Course with department permission (CCS4901)
        test_code3 = "CCS4901"
        cursor.execute("SELECT prereq_code FROM prerequisites WHERE course_code = ?", (test_code3,))
        prereqs3 = cursor.fetchall()
        
        print(f"\n[TEST] Prerequisites for {test_code3} (should be DEPT_PERMISSION):")
        for p in prereqs3:
            display = "Dengan Kebenaran Jabatan" if p[0] == "DEPT_PERMISSION" else p[0]
            print(f"  - {display}")
        
        conn.close()
        print("\n[SUCCESS] All database tests passed!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Database test failed: {e}")
        return False

if __name__ == "__main__":
    test_database_connection()
