# monica_alf.py
"""
Agent-Level Functions (ALF) for Monica Personal CRM.

This module provides a high-level, agent-friendly, and robust interface for 
interacting with the Monica CRM. It is the sole layer responsible for translating 
natural language concepts into concrete, multi-step API calls where necessary.

Key Design Principles:
- **Natural Language Input:** Functions accept names, not IDs.
- **Structured JSON I/O:** All functions return a structured dictionary,
  `{"status": "success", "data": ...}` or `{"status": "error", "message": ...}`.
  This prevents crashes from exceptions and provides clear feedback to the calling agent.
- **Idempotency & Safety:** Operations are designed to be as safe as possible,
  using find-or-create patterns where appropriate.
- **Clarity for AI:** Docstrings are written as specifications for a Gemini
  tool-using model, clearly defining parameters and expected outcomes.
"""

import json
from typing import Dict, Any, List, Optional, Literal, Union
from datetime import datetime
import temp as monica_api

# --- Internal Helper Functions ---

def _find_contact_by_name(name: str) -> Dict[str, Any]:
    """
    Finds a single contact by name and returns a structured response.
    This is the primary lookup function used by all other functions.
    """
    results = monica_api.list_contacts(query=name)
    if not results:
        return {"status": "error", "message": f"No contact found matching '{name}'. Please use the 'remember_person' tool to create them first."}
    
    # Prioritize exact matches
    exact_matches = [c for c in results if name.lower() in c.get('complete_name', '').lower()]
    if len(exact_matches) == 1:
        return {"status": "success", "data": exact_matches[0]}

    if len(results) > 1:
        found_names = [f"{c.get('first_name', '')} {c.get('last_name', '')}".strip() for c in results]
        return {"status": "error", "message": f"Multiple contacts found for '{name}'. Please be more specific. Found: {', '.join(found_names)}"}
        
    return {"status": "success", "data": results[0]}

def _find_or_create_company(company_name: str) -> Dict[str, Any]:
    """Finds a company by name. If not found, creates it. Returns the company object."""
    companies = monica_api.list_companies()
    for company in companies:
        if company['name'].lower() == company_name.lower():
            return company
    return monica_api.create_company(name=company_name)
    
def _find_relationship_type_by_name(name: str) -> Dict[str, Any]:
    """Finds a relationship type object by its name."""
    all_types = monica_api.list_relationship_types()
    for rel_type in all_types:
        if rel_type['name'].lower() == name.lower() or rel_type.get('name_reverse_relationship', '').lower() == name.lower():
            return {"status": "success", "data": rel_type}
    valid_types = [t['name'] for t in all_types]
    return {"status": "error", "message": f"Relationship type '{name}' not found. Valid types include: {', '.join(valid_types)}"}

# --- Public Agent-Facing Tools ---

def remember_person(first_name: str, last_name: Optional[str] = None, nickname: Optional[str] = None) -> Dict[str, Any]:
    """
    Creates a new contact in Monica.

    Args:
        first_name: The first name of the person.
        last_name: The last name of the person.
        nickname: The person's nickname.

    Returns:
        A dictionary with the result of the operation.
    """
    try:
        contact = monica_api.create_contact(
            first_name=first_name, 
            last_name=last_name, 
            nickname=nickname
        )
        return {"status": "success", "data": contact}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def find_people(query: str) -> Dict[str, Any]:
    """Searches for contacts matching a specific name or query."""
    contacts = monica_api.list_contacts(query=query)
    if not contacts:
        return {"status": "success", "data": [], "message": "No people found matching that search."}
    
    # Return a simplified list for the agent to process
    simplified_contacts = [{
        "id": c.get('id'),
        "name": c.get('complete_name', f"{c.get('first_name')} {c.get('last_name') or ''}".strip()),
        "job": c.get('information', {}).get('career', {}).get('job'),
    } for c in contacts]
    return {"status": "success", "data": simplified_contacts}

def get_details_about_person(person_name: str) -> Dict[str, Any]:
    """Retrieves all available details for a specific person, including notes, tasks, etc."""
    contact_result = _find_contact_by_name(person_name)
    if contact_result["status"] == "error":
        return contact_result
    
    contact = contact_result["data"]
    details = monica_api.get_contact(contact['id'])
    return {"status": "success", "data": details}

def forget_person(person_name: str) -> Dict[str, Any]:
    """Deletes a contact from Monica. This action is permanent."""
    contact_result = _find_contact_by_name(person_name)
    if contact_result["status"] == "error":
        return contact_result
    
    contact_id = contact_result["data"]['id']
    monica_api.delete_contact(contact_id)
    return {"status": "success", "data": {"deleted": True, "id": contact_id, "name": person_name}}

def remember_something_about(person_name: str, memory_text: str, is_important: bool = False) -> Dict[str, Any]:
    """Adds a new note or "memory" to a contact's profile."""
    contact_result = _find_contact_by_name(person_name)
    if contact_result["status"] == "error":
        return contact_result
    
    contact = contact_result["data"]
    note = monica_api.create_note(contact_id=contact['id'], body=memory_text, is_favorite=is_important)
    return {"status": "success", "data": note}

def get_memories_about(person_name: str) -> Dict[str, Any]:
    """Retrieves all notes ("memories") associated with a specific person."""
    contact_result = _find_contact_by_name(person_name)
    if contact_result["status"] == "error":
        return contact_result
        
    notes = monica_api.list_contact_notes(contact_result["data"]['id'])
    return {"status": "success", "data": notes}

def log_call_with(person_name: str, description: str, date: Optional[str] = None) -> Dict[str, Any]:
    """
    Logs a phone call made with a specific contact.
    
    Args:
        person_name: The name of the person who was called.
        description: A summary of what was discussed in the call.
        date: The date of the call in "YYYY-MM-DD" format. Defaults to today.
    """
    contact_result = _find_contact_by_name(person_name)
    if contact_result["status"] == "error":
        return contact_result
    
    call_date = date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    call = monica_api.create_call(contact_id=contact_result["data"]['id'], called_at=call_date, content=description)
    return {"status": "success", "data": call}

def set_relationship(person1_name: str, relationship_name: str, person2_name: str) -> Dict[str, Any]:
    """Defines a relationship between two contacts. E.g., set_relationship("John Doe", "Spouse", "Jane Doe")."""
    contact1_result = _find_contact_by_name(person1_name)
    if contact1_result["status"] == "error":
        return contact1_result

    contact2_result = _find_contact_by_name(person2_name)
    if contact2_result["status"] == "error":
        return contact2_result

    rel_type_result = _find_relationship_type_by_name(relationship_name)
    if rel_type_result["status"] == "error":
        return rel_type_result
        
    relationship = monica_api.create_relationship(
        contact_is=contact1_result['data']['id'], 
        relationship_type_id=rel_type_result['data']['id'], 
        of_contact=contact2_result['data']['id']
    )
    return {"status": "success", "data": relationship}

def create_task_for(person_name: str, title: str, description: Optional[str] = None) -> Dict[str, Any]:
    """Creates a to-do task related to a specific person."""
    contact_result = _find_contact_by_name(person_name)
    if contact_result["status"] == "error":
        return contact_result
        
    task = monica_api.create_task(contact_id=contact_result['data']['id'], title=title, description=description)
    return {"status": "success", "data": task}

def mark_task_as_complete(task_id: int) -> Dict[str, Any]:
    """Marks a specific task as complete by its ID."""
    try:
        task = monica_api.get_task(task_id)
        if task.get('completed'):
            return {"status": "success", "data": task, "message": f"Task ID {task_id} was already complete."}
        
        updated_task = monica_api.update_task(task_id=task_id, contact_id=task['contact']['id'], completed=1)
        return {"status": "success", "data": updated_task}
    except Exception as e:
        return {"status": "error", "message": f"Could not find or update task with ID {task_id}. Error: {e}"}

def set_reminder_for(person_name: str, title: str, date: str, frequency_type: Literal["one_time", "week", "month", "year"] = "one_time") -> Dict[str, Any]:
    """
    Sets a reminder for a contact.
    
    Args:
        person_name: The name of the contact.
        title: The title of the reminder.
        date: The date for the reminder in "YYYY-MM-DD" format.
        frequency_type: How often the reminder should repeat.
    """
    contact_result = _find_contact_by_name(person_name)
    if contact_result["status"] == "error":
        return contact_result
        
    reminder = monica_api.create_reminder(
        contact_id=contact_result['data']['id'], title=title, next_expected_date=date,
        frequency_type=frequency_type, frequency_number=1
    )
    return {"status": "success", "data": reminder}

def log_job_for_person(person_name: str, job_title: str, company_name: str) -> Dict[str, Any]:
    """
    Logs an occupation (job) for a contact. If the company doesn't exist, it will be created.
    """
    contact_result = _find_contact_by_name(person_name)
    if contact_result["status"] == "error":
        return contact_result
    
    try:
        _find_or_create_company(company_name)
        result = monica_api.set_contact_occupation(
            contact_id=contact_result['data']['id'],
            job_title=job_title,
            company_name=company_name
        )
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def tag_person(person_name: str, tags: List[str]) -> Dict[str, Any]:
    """
    Adds one or more tags to a contact. New tags will be created if they don't exist.
    """
    contact_result = _find_contact_by_name(person_name)
    if contact_result["status"] == "error":
        return contact_result
        
    result = monica_api.set_tags_for_contact(contact_result['data']['id'], tags)
    return {"status": "success", "data": result}