"""
Database layer for the Academic Advisor Chatbot.
Provides Pydantic models and functions for interacting with academic.db.

This module follows the Rasa Pro CALM architecture pattern, using
Pydantic models for type-safe data handling and parameterized queries
for SQL injection prevention.
"""

import os
import sqlite3
from typing import Optional

from pydantic import BaseModel


# Database path configuration
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "academic.db")


class Course(BaseModel):
    """Pydantic model representing a course in the academic database."""
    
    code: str
    name: str
    credits: Optional[int] = None
    description: Optional[str] = None

    def stringify(self) -> str:
        """Return a formatted string representation of the course."""
        credits_str = f"{self.credits} credits" if self.credits else "N/A credits"
        return f"{self.code}: {self.name} ({credits_str})"


class Prerequisite(BaseModel):
    """Pydantic model representing a course prerequisite."""
    
    course_code: str
    prereq_code: str

    def stringify(self) -> str:
        """Return a formatted string representation of the prerequisite."""
        if self.prereq_code == "DEPT_PERMISSION":
            return "Dengan Kebenaran Jabatan (Department Permission)"
        return self.prereq_code


def get_db_connection() -> sqlite3.Connection:
    """
    Create and return a database connection.
    
    Returns:
        sqlite3.Connection: Active database connection
        
    Raises:
        FileNotFoundError: If database file doesn't exist
    """
    if not os.path.exists(DB_PATH):
        # Fallback to root-level academic.db for backward compatibility
        fallback_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "academic.db")
        if os.path.exists(fallback_path):
            return sqlite3.connect(fallback_path)
        raise FileNotFoundError(f"Database not found at {DB_PATH} or {fallback_path}")
    return sqlite3.connect(DB_PATH)


def get_course(course_code: str) -> Optional[Course]:
    """
    Retrieve course information by course code.
    
    Args:
        course_code: The course code to look up (e.g., 'CCS3101')
        
    Returns:
        Course object if found, None otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Parameterized query to prevent SQL injection
        cursor.execute(
            """
            SELECT course_code, course_name, credit_hours, description
            FROM courses
            WHERE course_code = ?
            """,
            (course_code.upper(),)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Course(
                code=row[0],
                name=row[1],
                credits=row[2],
                description=row[3]
            )
        return None
        
    except Exception as e:
        print(f"Error retrieving course {course_code}: {e}")
        return None


def get_prerequisites(course_code: str) -> list[str]:
    """
    Retrieve prerequisite course codes for a given course.
    
    Args:
        course_code: The course code to look up prerequisites for
        
    Returns:
        List of prerequisite course codes (may be empty)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Parameterized query to prevent SQL injection
        cursor.execute(
            """
            SELECT prereq_code
            FROM prerequisites
            WHERE course_code = ?
            """,
            (course_code.upper(),)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in rows]
        
    except Exception as e:
        print(f"Error retrieving prerequisites for {course_code}: {e}")
        return []


def get_prerequisites_detailed(course_code: str) -> list[Prerequisite]:
    """
    Retrieve detailed prerequisite information for a given course.
    
    Args:
        course_code: The course code to look up prerequisites for
        
    Returns:
        List of Prerequisite objects (may be empty)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT course_code, prereq_code
            FROM prerequisites
            WHERE course_code = ?
            """,
            (course_code.upper(),)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            Prerequisite(course_code=row[0], prereq_code=row[1])
            for row in rows
        ]
        
    except Exception as e:
        print(f"Error retrieving prerequisites for {course_code}: {e}")
        return []


def course_exists(course_code: str) -> bool:
    """
    Check if a course exists in the database.
    
    Args:
        course_code: The course code to check
        
    Returns:
        True if course exists, False otherwise
    """
    return get_course(course_code) is not None
