# == monica_agent_level_functions.py ==

# monica_alf.py

"""
Agent-Level Functions for Monica Personal CRM

This module provides a high-level, agent-friendly interface for interacting 
with the Monica Personal CRM. It is built on top of the low-level API-calling
functions in `temp.py`.

Key design principles:
- **Natural Language Input:** Functions are designed to be called with natural 
  inputs like names, rather than requiring the agent to manage API-specific IDs.
- **Robustness and Clarity:** Functions handle common failure cases, such as not 
  finding a contact or finding multiple, and return clear, actionable error 
  messages. All categorical inputs (e.g., gift status, reminder frequency) are
  explicitly listed in the docstrings.
- **Comprehensive Docstrings:** Each function is thoroughly documented to explain 
  its purpose, parameters, return values, and any relevant context, enabling an
  AI agent to understand and use it correctly.
- **Abstraction:** Complex operations that require multiple API calls (e.g., logging
  a job which might require creating a company first) are abstracted into a 
  single, intuitive function call.
"""

from typing import Dict, Any, List, Optional, Literal, Union
from datetime import datetime
import temp as monica_api

# --- Helper Functions for Internal Use ---

def _find_contact_by_name(name: str) -> Dict[str, Any]:
    """Finds a single contact by name and returns their full contact object."""
    results = monica_api.list_contacts(query=name)
    if not results:
        raise ValueError(f"No contact found matching '{name}'. Please try a different name or create the contact first.")
    if len(results) > 1:
        found_names = [f"{c.get('first_name', '')} {c.get('last_name', '')}".strip() for c in results]
        raise ValueError(f"Multiple contacts found for '{name}'. Please be more specific. Found: {found_names}")
    return results[0]

def _find_relationship_type_by_name(name: str) -> Dict[str, Any]:
    """Finds a relationship type object by its name or reverse name."""
    all_types = monica_api.list_relationship_types()
    for rel_type in all_types:
        if rel_type['name'].lower() == name.lower() or rel_type.get('name_reverse_relationship', '').lower() == name.lower():
            return rel_type
    raise ValueError(f"Relationship type '{name}' not found. Please use a valid relationship type.")

def _find_tag_by_name(tag_name: str) -> Optional[Dict[str, Any]]:
    """Finds a tag by its name."""
    all_tags = monica_api.list_tags(limit=100) # Get a decent number of tags
    for tag in all_tags:
        if tag['name'].lower() == tag_name.lower():
            return tag
    return None

def _find_or_create_company(company_name: str) -> Dict[str, Any]:
    """Finds a company by name. If not found, creates it."""
    companies = monica_api.list_companies()
    for company in companies:
        if company['name'].lower() == company_name.lower():
            return company
    # If not found, create it
    return monica_api.create_company(name=company_name)


# --- Contacts and People Management ---

def remember_person(
    first_name: str, 
    last_name: Optional[str] = None, 
    nickname: Optional[str] = None, 
    gender_name: str = "Rather not say"
) -> str:
    """
    Creates a new contact in Monica.

    Args:
        first_name: The first name of the person.
        last_name: The last name of the person.
        nickname: The person's nickname.
        gender_name: The name of the person's gender (e.g., "Man", "Woman"). Defaults to 'Rather not say'.
                     A list of available genders can be retrieved via `monica_api.list_genders()`.

    Returns:
        A confirmation string with the new contact's name and ID.
    """
    genders = monica_api.list_genders()
    gender_id = None
    for gender in genders:
        if gender['name'].lower() == gender_name.lower():
            gender_id = gender['id']
            break
    if gender_id is None:
        raise ValueError(f"Gender '{gender_name}' is not a valid option. Please choose from the available genders.")

    contact = monica_api.create_contact(
        first_name=first_name, 
        last_name=last_name, 
        nickname=nickname, 
        gender_id=gender_id
    )
    return f"Successfully remembered {contact.get('complete_name')} with ID {contact.get('id')}."

def find_people(query: str) -> Union[str, List[Dict[str, Any]]]:
    """Searches for contacts matching a specific query."""
    contacts = monica_api.list_contacts(query=query)
    if not contacts:
        return "No people found matching that search."
    return [{
        "id": c.get('id'),
        "name": c.get('complete_name', f"{c.get('first_name')} {c.get('last_name') or ''}".strip()),
        "job": c.get('information', {}).get('career', {}).get('job'),
        "company": c.get('information', {}).get('career', {}).get('company'),
    } for c in contacts]

def get_details_about_person(person_name: str) -> Dict[str, Any]:
    """Retrieves all available details for a specific person."""
    contact = _find_contact_by_name(person_name)
    return monica_api.get_contact(contact['id'])

def forget_person(person_name: str) -> str:
    """Deletes a contact from Monica. This action is permanent."""
    contact = _find_contact_by_name(person_name)
    monica_api.delete_contact(contact['id'])
    return f"Successfully forgot the contact '{person_name}' (ID: {contact['id']})."


# --- Notes / Memories ---

def remember_something_about(person_name: str, memory_text: str, is_important: bool = False) -> str:
    """Adds a new note or "memory" to a contact's profile."""
    contact = _find_contact_by_name(person_name)
    note = monica_api.create_note(contact_id=contact['id'], body=memory_text, is_favorite=is_important)
    status = "an important" if is_important else "a"
    return f"Successfully remembered {status} memory about {person_name}. (Note ID: {note['id']})"

def get_memories_about(person_name: str) -> List[Dict[str, Any]]:
    """Retrieves all notes ("memories") associated with a specific person."""
    contact = _find_contact_by_name(person_name)
    return monica_api.list_contact_notes(contact['id'])


# --- Activities, Calls, Conversations ---

def log_activity_with(
    people_names: List[str],
    summary: str,
    activity_type_name: str,
    date: str, # "YYYY-MM-DD"
    description: Optional[str] = None
) -> str:
    """Logs an activity that occurred with one or more people."""
    contact_ids = [_find_contact_by_name(name)['id'] for name in people_names]
    activity_types = monica_api.list_activity_types()
    activity_type_id = next((at['id'] for at in activity_types if at['name'].lower() == activity_type_name.lower()), None)
    if not activity_type_id:
        raise ValueError(f"Activity type '{activity_type_name}' not found.")
    activity = monica_api.create_activity(
        contact_ids=contact_ids, summary=summary, activity_type_id=activity_type_id,
        happened_at=date, description=description or ""
    )
    return f"Successfully logged activity '{summary}' with ID {activity['id']}."

def log_call_with(person_name: str, date: str, description: str) -> str:
    """Logs a phone call made with a specific contact."""
    contact = _find_contact_by_name(person_name)
    call = monica_api.create_call(contact_id=contact['id'], called_at=date, content=description)
    return f"Successfully logged a call with {person_name} on {date}. (Call ID: {call['id']})"

def start_conversation_with(person_name: str, date: str, medium: str) -> str:
    """
    Creates a new conversation container for a contact, specifying the communication medium.
    After creating the conversation, you can add messages to it using `add_message_to_conversation`.

    Args:
        person_name: The name of the contact.
        date: The date the conversation took place ("YYYY-MM-DD").
        medium: The communication medium (e.g., "Email", "Twitter", "SMS"). Must match an existing Contact Field Type.

    Returns:
        A confirmation string with the new conversation's ID.
    """
    contact = _find_contact_by_name(person_name)
    field_types = monica_api.list_contact_field_types()
    field_type_id = next((ft['id'] for ft in field_types if ft['name'].lower() == medium.lower()), None)
    if not field_type_id:
        raise ValueError(f"Communication medium '{medium}' not found. Please use a valid Contact Field Type name.")
    conversation = monica_api.create_conversation(contact_id=contact['id'], happened_at=date, contact_field_type_id=field_type_id)
    return f"Started a new conversation with {person_name} on {medium}. (Conversation ID: {conversation['id']})"

def add_message_to_conversation(conversation_id: int, content: str, written_by: Literal["me", "them"], date: Optional[str] = None) -> str:
    """Adds a message to an existing conversation."""
    conversation = monica_api.get_conversation(conversation_id)
    contact_id = conversation['contact']['id']
    written_at = date or datetime.now().strftime("%Y-%m-%d")
    written_by_me = True if written_by == "me" else False
    
    message = monica_api.add_message_to_conversation(conversation_id, contact_id, written_at, written_by_me, content)
    return f"Successfully added message to conversation {conversation_id}."

# --- Relationships ---

def set_relationship(person1_name: str, relationship_name: str, person2_name: str) -> str:
    """Defines a relationship between two contacts. E.g., set_relationship("John Doe", "Spouse", "Jane Doe")"""
    contact1 = _find_contact_by_name(person1_name)
    contact2 = _find_contact_by_name(person2_name)
    rel_type = _find_relationship_type_by_name(relationship_name)
    relationship = monica_api.create_relationship(contact_is=contact1['id'], relationship_type_id=rel_type['id'], of_contact=contact2['id'])
    return f"Successfully set relationship: {person1_name} is now {rel_type['name']} of {person2_name}."

# --- Tasks, Reminders, Debts ---

def create_task_for(person_name: str, title: str, description: Optional[str] = None) -> str:
    """Creates a to-do task related to a specific person."""
    contact = _find_contact_by_name(person_name)
    task = monica_api.create_task(contact_id=contact['id'], title=title, description=description)
    return f"Task '{task['title']}' created for {person_name} (ID: {task['id']})."

def mark_task_as_complete(task_id: int) -> str:
    """Marks a specific task as complete."""
    task = monica_api.get_task(task_id)
    if task['completed']:
        return f"Task ID {task_id} ('{task['title']}') was already marked as complete."
    updated_task = monica_api.update_task(task_id=task_id, contact_id=task['contact']['id'], completed=1)
    return f"Task ID {updated_task['id']} ('{updated_task['title']}') has been marked as complete."

def set_reminder_for(
    person_name: str,
    title: str,
    date: str, # "YYYY-MM-DD"
    frequency_type: Literal["one_time", "week", "month", "year"] = "one_time",
    frequency_number: Optional[int] = 1
) -> str:
    """Sets a reminder for a contact. For recurring reminders, set frequency_type and frequency_number."""
    contact = _find_contact_by_name(person_name)
    reminder = monica_api.create_reminder(
        contact_id=contact['id'], title=title, next_expected_date=date,
        frequency_type=frequency_type, frequency_number=frequency_number
    )
    return f"Reminder '{title}' set for {person_name} on {date}. (ID: {reminder['id']})"

def track_debt(
    person_who_owes_money: str,
    person_who_is_owed_money: str,
    amount: float,
    reason: Optional[str] = None,
    is_settled: bool = False
) -> str:
    """Tracks a debt between the user ('me') and another contact."""
    if person_who_owes_money.lower() == 'me' and person_who_is_owed_money.lower() == 'me':
        raise ValueError("Cannot create a debt where you owe money to yourself.")
    if person_who_owes_money.lower() != 'me' and person_who_is_owed_money.lower() != 'me':
        raise ValueError("One of the parties in the debt must be 'me'. This tool tracks your debts, not debts between two other people.")

    if person_who_owes_money.lower() == 'me':
        contact = _find_contact_by_name(person_who_is_owed_money)
        in_debt, desc = "yes", f"I owe {contact['first_name']} ${amount}."
    else: # person_who_is_owed_money is 'me'
        contact = _find_contact_by_name(person_who_owes_money)
        in_debt, desc = "no", f"{contact['first_name']} owes me ${amount}."

    status = "complete" if is_settled else "inprogress"
    debt = monica_api.create_debt(contact_id=contact['id'], in_debt=in_debt, status=status, amount=int(amount), reason=reason)
    return f"Successfully tracked debt (ID: {debt['id']}): {desc}"


# --- Gifts ---

def log_gift(person_name: str, gift_name: str, status: Literal["idea", "offered", "received"], date: Optional[str] = None, amount: Optional[float] = None) -> str:
    """
    Logs a gift idea, a gift you've offered, or a gift you've received.

    Args:
        person_name: The name of the contact associated with the gift.
        gift_name: A description of the gift.
        status: The status of the gift.
                - 'idea': A gift idea for this person.
                - 'offered': A gift you gave to this person.
                - 'received': A gift you received from this person.
        date: The date the gift was given/received ("YYYY-MM-DD").
        amount: The monetary value of the gift.

    Returns:
        A confirmation string.
    """
    contact = _find_contact_by_name(person_name)
    gift = monica_api.create_gift(contact_id=contact['id'], name=gift_name, status=status, date=date, amount=amount)
    return f"Successfully logged gift '{gift_name}' for {person_name} with status '{status}'."

# --- Career / Work ---

def log_job_for_person(person_name: str, job_title: str, company_name: str, start_date: Optional[str] = None) -> str:
    """
    Logs an occupation (job) for a contact. If the company doesn't exist, it will be created.

    Args:
        person_name: The name of the contact.
        job_title: The person's job title.
        company_name: The name of the company.
        start_date: The date the job started ("YYYY-MM-DD").

    Returns:
        A confirmation string.
    """
    contact = _find_contact_by_name(person_name)
    company = _find_or_create_company(company_name)
    occupation = monica_api.create_occupation(
        contact_id=contact['id'], company_id=company['id'],
        title=job_title, start_date=start_date
    )
    return f"Successfully logged that {person_name} works as a {job_title} at {company_name}."

# --- Tags ---

def tag_person(person_name: str, tags: List[str]) -> str:
    """
    Adds one or more tags to a contact. New tags will be created if they don't exist.
    
    Args:
        person_name: The name of the contact to tag.
        tags: A list of tag names to apply to the contact.

    Returns:
        A confirmation string.
    """
    contact = _find_contact_by_name(person_name)
    monica_api.set_tags_for_contact(contact['id'], tags)
    return f"Successfully tagged {person_name} with: {', '.join(tags)}."

def untag_person(person_name: str, tags_to_remove: List[str]) -> str:
    """
    Removes one or more tags from a contact.
    
    Args:
        person_name: The name of the contact to untag.
        tags_to_remove: A list of tag names to remove from the contact.

    Returns:
        A confirmation string.
    """
    contact = _find_contact_by_name(person_name)
    tag_ids_to_remove = []
    for tag_name in tags_to_remove:
        tag_obj = _find_tag_by_name(tag_name)
        if tag_obj:
            tag_ids_to_remove.append(tag_obj['id'])
        else:
            return f"Cannot untag: Tag '{tag_name}' not found for contact {person_name}."

    if not tag_ids_to_remove:
        return f"No matching tags found to remove from {person_name}."

    monica_api.unset_tags_for_contact(contact['id'], tag_ids_to_remove)
    return f"Successfully removed tags: {', '.join(tags_to_remove)} from {person_name}."

