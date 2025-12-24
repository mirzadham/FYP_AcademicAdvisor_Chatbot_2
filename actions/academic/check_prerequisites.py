"""
Custom action to check prerequisites for a course.
Uses the database layer to retrieve prerequisite information.
"""

from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

from actions.db import get_course, get_prerequisites


class CheckPrerequisites(Action):
    """Action to check and return prerequisites for a course."""

    def name(self) -> Text:
        return "check_prerequisites"

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
                SlotSet("prereq_list", None),
                SlotSet("has_prerequisites", False)
            ]
        
        # Normalize course code
        course_code = course_code.upper().strip()
        
        # Check if course exists
        course = get_course(course_code)
        if not course:
            return [
                SlotSet("return_value", "course_not_found"),
                SlotSet("prereq_list", None),
                SlotSet("has_prerequisites", False),
                SlotSet("course_name", None)
            ]
        
        # Get prerequisites
        prereq_codes = get_prerequisites(course_code)
        
        # Format prerequisites for display
        formatted_prereqs = []
        for prereq in prereq_codes:
            if prereq == "DEPT_PERMISSION":
                formatted_prereqs.append("Dengan Kebenaran Jabatan (Department Permission)")
            else:
                formatted_prereqs.append(prereq)
        
        prereq_str = ", ".join(formatted_prereqs) if formatted_prereqs else None
        has_prereqs = len(prereq_codes) > 0
        
        return [
            SlotSet("return_value", "success"),
            SlotSet("course_name", course.name),
            SlotSet("prereq_list", prereq_str),
            SlotSet("has_prerequisites", has_prereqs)
        ]
