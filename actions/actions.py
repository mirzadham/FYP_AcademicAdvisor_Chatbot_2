"""
Custom actions for the Academic Advisor Chatbot.
Connects to academic.db to provide course information and prerequisites.
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import sqlite3
import os


class ActionProvidePrerequisite(Action):
    """
    Action to provide prerequisite information for a course.
    Queries the 'prerequisites' table for a given course code.
    """

    def name(self) -> Text:
        return "action_provide_prerequisite"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get the course code from the entities
        course_code = None
        entities = tracker.latest_message.get('entities', [])
        
        for entity in entities:
            if entity.get('entity') == 'course_code':
                course_code = entity.get('value', '').upper()
                break
        
        if not course_code:
            dispatcher.utter_message(text="I couldn't identify the course code. Please provide a course code (e.g., CCS3101).")
            return []
        
        # Query the database
        try:
            db_path = "academic.db"
            if not os.path.exists(db_path):
                dispatcher.utter_message(text="Sorry, the course database is not available.")
                return []
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # First check if the course exists
            cursor.execute("SELECT course_name FROM courses WHERE course_code = ?", (course_code,))
            course = cursor.fetchone()
            
            if not course:
                dispatcher.utter_message(text=f"Sorry, I couldn't find course {course_code} in the database.")
                conn.close()
                return []
            
            course_name = course[0]
            
            # Get prerequisites
            cursor.execute("SELECT prereq_code FROM prerequisites WHERE course_code = ?", (course_code,))
            prereqs = cursor.fetchall()
            conn.close()
            
            if not prereqs:
                message = f"📚 **{course_code}** ({course_name})\n\n✅ **No prerequisites required** - You can take this course directly!"
            else:
                prereq_list = []
                for prereq in prereqs:
                    prereq_code = prereq[0]
                    if prereq_code == "DEPT_PERMISSION":
                        prereq_list.append("**Dengan Kebenaran Jabatan** (Department Permission Required)")
                    else:
                        prereq_list.append(f"**{prereq_code}**")
                
                prereq_str = "\n".join([f"  • {p}" for p in prereq_list])
                message = f"📚 **{course_code}** ({course_name})\n\n📋 **Prerequisites:**\n{prereq_str}"
            
            dispatcher.utter_message(text=message)
            
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I encountered an error while retrieving prerequisite information: {str(e)}")
        
        return []


class ActionProvideCourseInfo(Action):
    """
    Action to provide detailed course information.
    Queries the 'courses' table for name, credits, and description.
    """

    def name(self) -> Text:
        return "action_provide_course_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get the course code from the entities
        course_code = None
        entities = tracker.latest_message.get('entities', [])
        
        for entity in entities:
            if entity.get('entity') == 'course_code':
                course_code = entity.get('value', '').upper()
                break
        
        if not course_code:
            dispatcher.utter_message(text="I couldn't identify the course code. Please provide a course code (e.g., CCS3101).")
            return []
        
        # Query the database
        try:
            db_path = "academic.db"
            if not os.path.exists(db_path):
                dispatcher.utter_message(text="Sorry, the course database is not available.")
                return []
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get course information
            cursor.execute("""
                SELECT course_name, credit_hours, description 
                FROM courses 
                WHERE course_code = ?
            """, (course_code,))
            
            course = cursor.fetchone()
            
            if not course:
                dispatcher.utter_message(text=f"Sorry, I couldn't find course {course_code} in the database.")
                conn.close()
                return []
            
            course_name, credit_hours, description = course
            
            # Get prerequisites for additional info
            cursor.execute("SELECT prereq_code FROM prerequisites WHERE course_code = ?", (course_code,))
            prereqs = cursor.fetchall()
            conn.close()
            
            # Format prerequisites
            if prereqs:
                prereq_list = []
                for prereq in prereqs:
                    prereq_code = prereq[0]
                    if prereq_code == "DEPT_PERMISSION":
                        prereq_list.append("Dengan Kebenaran Jabatan")
                    else:
                        prereq_list.append(prereq_code)
                prereq_str = ", ".join(prereq_list)
            else:
                prereq_str = "None"
            
            # Build the message
            message = f"""📚 **{course_code}**: {course_name}

💳 **Credit Hours:** {credit_hours if credit_hours else 'N/A'}

📋 **Prerequisites:** {prereq_str}

📖 **Description:**
{description}"""
            
            dispatcher.utter_message(text=message)
            
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I encountered an error while retrieving course information: {str(e)}")
        
        return []
