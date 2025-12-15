"""
Custom actions for the Academic Advisor Chatbot.
Connects to academic.db to provide course information and prerequisites.
Integrates with Google Gemini AI for enhanced responses.
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import sqlite3
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()


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


class ActionGeminiResponse(Action):
    """
    Action to handle general queries using Google Gemini AI.
    This provides intelligent responses for questions not covered by specific actions.
    """

    def name(self) -> Text:
        return "action_gemini_response"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get API key from environment
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key or api_key == 'your_gemini_api_key_here':
            dispatcher.utter_message(text="⚠️ Gemini API key is not configured. Please set up your GEMINI_API_KEY in the .env file.")
            return []
        
        # Get the user's message
        user_message = tracker.latest_message.get('text', '')
        
        if not user_message:
            dispatcher.utter_message(text="I didn't receive any message. Please try again.")
            return []
        
        try:
            # Configure Gemini
            genai.configure(api_key=api_key)
            
            # Create the model - using gemini-2.5-flash for better quota limits
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # Prepare context for academic advisor chatbot
            context = """You are an academic advisor chatbot helping students with their course-related queries.
Provide helpful, accurate, and concise responses. If the question is about specific courses, 
suggest that they provide a course code for detailed information."""
            
            # Generate response
            prompt = f"{context}\n\nStudent Question: {user_message}\n\nResponse:"
            response = model.generate_content(prompt)
            
            if response and response.text:
                dispatcher.utter_message(text=f"🤖 {response.text}")
            else:
                dispatcher.utter_message(text="I'm sorry, I couldn't generate a response. Please try rephrasing your question.")
        
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I encountered an error while processing your request: {str(e)}")
        
        return []
