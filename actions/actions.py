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
            db_path = "db/academic.db"
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
            db_path = "db/academic.db"
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
    RAG-Enhanced Action using Google Gemini AI.
    
    This action implements Retrieval-Augmented Generation (RAG):
    1. Retrieves relevant course data from the database
    2. Provides domain-specific context to Gemini
    3. Generates grounded, accurate responses
    
    This is NOT just an API wrapper - it feeds real academic data to the LLM.
    """

    def name(self) -> Text:
        return "action_gemini_response"

    def _get_relevant_courses(self, user_message: str, limit: int = 5) -> str:
        """
        Retrieve relevant course information from the database.
        This is the 'Retrieval' part of RAG.
        """
        try:
            db_path = "db/academic.db"
            if not os.path.exists(db_path):
                return ""
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Search for courses that might be relevant to the query
            # Look for course codes mentioned in the message
            import re
            course_codes = re.findall(r'[A-Z]{2,4}\d{4}', user_message.upper())
            
            course_context = []
            
            # If specific course codes found, get their details
            if course_codes:
                for code in course_codes[:3]:  # Limit to 3 courses
                    cursor.execute("""
                        SELECT course_code, course_name, credit_hours, description 
                        FROM courses WHERE course_code = ?
                    """, (code,))
                    course = cursor.fetchone()
                    if course:
                        cursor.execute("SELECT prereq_code FROM prerequisites WHERE course_code = ?", (code,))
                        prereqs = [p[0] for p in cursor.fetchall()]
                        prereq_str = ", ".join(prereqs) if prereqs else "None"
                        course_context.append(
                            f"- {course[0]}: {course[1]} ({course[2]} credits)\n"
                            f"  Prerequisites: {prereq_str}\n"
                            f"  Description: {course[3][:200]}..."
                        )
            
            # Also get a sample of courses for general context
            cursor.execute("""
                SELECT course_code, course_name, credit_hours 
                FROM courses 
                ORDER BY RANDOM() 
                LIMIT ?
            """, (limit,))
            sample_courses = cursor.fetchall()
            
            conn.close()
            
            if course_context:
                return "RELEVANT COURSES FROM DATABASE:\n" + "\n".join(course_context)
            elif sample_courses:
                sample_str = "\n".join([f"- {c[0]}: {c[1]} ({c[2]} credits)" for c in sample_courses])
                return f"SAMPLE COURSES IN DATABASE:\n{sample_str}"
            return ""
            
        except Exception as e:
            return f"(Database error: {str(e)})"

    def _get_conversation_history(self, tracker: Tracker, max_turns: int = 3) -> str:
        """
        Get recent conversation history for context.
        """
        events = tracker.events
        history = []
        
        for event in reversed(events):
            if len(history) >= max_turns * 2:
                break
            if event.get('event') == 'user':
                history.insert(0, f"Student: {event.get('text', '')}")
            elif event.get('event') == 'bot':
                history.insert(0, f"Advisor: {event.get('text', '')[:100]}...")
        
        if history:
            return "RECENT CONVERSATION:\n" + "\n".join(history[-4:])
        return ""

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
            
            # Create the model
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # === RAG: Retrieve relevant context ===
            course_context = self._get_relevant_courses(user_message)
            conversation_history = self._get_conversation_history(tracker)
            
            # === Enhanced System Prompt with UPM-specific knowledge ===
            system_prompt = """You are the UPM Academic Advisor, an AI assistant for 
Universiti Putra Malaysia students.

YOUR ROLE:
- Help students with academic queries about courses, prerequisites, and procedures
- Provide accurate information based on the data provided
- Be friendly, helpful, and encouraging
- Use Bahasa Malaysia terms when appropriate (e.g., "Dengan Kebenaran Jabatan")

IMPORTANT GUIDELINES:
1. If course data is provided below, use it to give accurate answers
2. If you don't have specific information, say so honestly
3. For complex administrative issues, suggest contacting the relevant faculty office
4. Keep responses concise but helpful

UPM ACADEMIC CONTEXT:
- Semesters: Semester 1 (Oct-Feb), Semester 2 (Mar-Jul)
- Credit system: Most courses are 3 credits
- Prerequisites must be completed before taking advanced courses
- "Dengan Kebenaran Jabatan" means department permission required"""

            # Build the full prompt with RAG context
            prompt_parts = [system_prompt]
            
            if course_context:
                prompt_parts.append(f"\n\n{course_context}")
            
            if conversation_history:
                prompt_parts.append(f"\n\n{conversation_history}")
            
            prompt_parts.append(f"\n\nSTUDENT QUESTION: {user_message}")
            prompt_parts.append("\n\nProvide a helpful, accurate response:")
            
            full_prompt = "".join(prompt_parts)
            
            # Generate response
            response = model.generate_content(full_prompt)
            
            if response and response.text:
                # Add a subtle indicator that this is an AI-enhanced response
                dispatcher.utter_message(text=f"🎓 {response.text}")
            else:
                dispatcher.utter_message(text="I'm sorry, I couldn't generate a response. Please try rephrasing your question.")
        
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I encountered an error while processing your request: {str(e)}")
        
        return []

