"""
Custom action to retrieve detailed course information.
Uses the database layer to fetch course details.
"""

from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

from actions.db import get_course, get_prerequisites


class GetCourseDetails(Action):
    """Action to retrieve and return detailed course information."""

    def name(self) -> Text:
        return "get_course_details"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        # Get course_code from slot (collected by flow)
        course_code = tracker.get_slot("course_code")
        
        if not course_code:
            return [
                SlotSet("return_value", "missing_course_code"),
                SlotSet("course_name", None),
                SlotSet("credits", None),
                SlotSet("synopsis", None)
            ]
        
        # Normalize course code
        course_code = course_code.upper().strip()
        
        # Get course details
        course = get_course(course_code)
        
        if not course:
            return [
                SlotSet("return_value", "course_not_found"),
                SlotSet("course_name", None),
                SlotSet("credits", None),
                SlotSet("synopsis", None)
            ]
        
        # Get prerequisites for additional context
        prereq_codes = get_prerequisites(course_code)
        formatted_prereqs = []
        for prereq in prereq_codes:
            if prereq == "DEPT_PERMISSION":
                formatted_prereqs.append("Dengan Kebenaran Jabatan")
            else:
                formatted_prereqs.append(prereq)
        
        prereq_str = ", ".join(formatted_prereqs) if formatted_prereqs else "None"
        
        return [
            SlotSet("return_value", "success"),
            SlotSet("course_name", course.name),
            SlotSet("credits", course.credits),
            SlotSet("synopsis", course.description),
            SlotSet("prereq_list", prereq_str)
        ]
