import os
import dotenv
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional, Literal, Union

# --- Configuration & Initialization ---
dotenv.load_dotenv()

API_URL = os.environ.get("MONICA_API_URL")
API_TOKEN = os.environ.get("MONICA_TOKEN")

if not API_URL or not API_TOKEN:
    raise ValueError("MONICA_API_URL and MONICA_TOKEN must be set in your environment or a .env file.")

HEADERS = {"Authorization": f"Bearer {API_TOKEN}", "Accept": "application/json"}


# === Core API Helpers ===

def call(endpoint: str, method: str = "GET", payload: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, use_api_prefix: bool = True) -> Any:
    """A helper function to make JSON requests to the Monica API."""
    base_url = API_URL if use_api_prefix else API_URL.replace('/api', '')
    url = f"{base_url}/{endpoint}"
    print(f"Calling {method} {url}")
    try:
        resp = requests.request(method, url, json=payload, headers=HEADERS, params=params)
        resp.raise_for_status()
        if resp.status_code == 204:
            return None
        response_json = resp.json()
        return response_json.get("data", response_json)
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} for URL: {url}")
        print(f"Response Text: {resp.text}")
        raise
    except Exception as err:
        print(f"An unexpected error occurred: {err}")
        raise

def upload_file(endpoint: str, filepath: str, file_key: str = "document", payload: Optional[Dict[str, Any]] = None) -> Any:
    """A flexible helper to upload files (documents, photos) to the Monica API."""
    url = f"{API_URL}/{endpoint}"
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"The file was not found at {filepath}")

    with open(filepath, 'rb') as f:
        files = {file_key: f}
        try:
            resp = requests.post(url, data=payload, files=files, headers=HEADERS)
            resp.raise_for_status()
            return resp.json().get("data")
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred during upload: {http_err} for URL: {url}")
            print(f"Response Text: {resp.text}")
            raise


# === Account & Lookup Data (Read-Only) ===

def get_user() -> Dict[str, Any]:
    """GET /me - Fetches the authenticated user's details."""
    return call("me")

def list_genders() -> List[Dict[str, Any]]:
    """GET /genders - Lists all available genders."""
    return call("genders")

def list_currencies() -> List[Dict[str, Any]]:
    """GET /currencies - Lists all available currencies."""
    return call("currencies")

def list_countries() -> List[Dict[str, Any]]:
    """GET /countries - Lists all available countries."""
    return call("countries")

def list_activity_types() -> List[Dict[str, Any]]:
    """GET /activitytypes - Lists all available activity types."""
    return call("activitytypes")

def list_contact_field_types() -> List[Dict[str, Any]]:
    """GET /contactfieldtypes - Lists all available contact field types."""
    return call("contactfieldtypes")

def list_relationship_types() -> List[Dict[str, Any]]:
    """GET /relationshiptypes - Lists all available relationship types."""
    return call("relationshiptypes")


# === Contacts ===

def list_contacts(query: Optional[str] = None, page: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
    """GET /contacts - Lists all contacts, with optional search query and pagination."""
    params = {"page": page, "limit": limit}
    if query:
        params["query"] = query
    return call("contacts", params=params)

def get_contact(contact_id: int) -> Dict[str, Any]:
    """GET /contacts/:id - Fetches a single contact by their ID."""
    return call(f"contacts/{contact_id}")

def create_contact(first_name: str, **kwargs: Any) -> Dict[str, Any]:
    """POST /contacts - Creates a new contact. 'first_name' is required."""
    payload = {"first_name": first_name, "is_birthdate_known": False, "is_deceased": False, "is_deceased_date_known": False}
    payload.update(kwargs)
    return call("contacts", "POST", payload)

def update_contact(contact_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
    """PUT /contacts/:id - Dynamically updates a contact's core fields."""
    current_data = get_contact(contact_id)
    payload = current_data.copy()
    payload['is_birthdate_known'] = current_data.get('birthdate', {}).get('is_known', False)
    payload['is_deceased'] = current_data.get('is_deceased', False)
    payload['is_deceased_date_known'] = current_data.get('deceased_date', {}).get('is_known', False)
    payload.update(updates)
    if 'birthdate' in payload and payload.get('birthdate'):
        payload['is_birthdate_known'] = payload['birthdate'].get('is_known', False)
    if 'deceased_date' in payload and payload.get('deceased_date'):
        payload['is_deceased_date_known'] = payload['deceased_date'].get('is_known', False)
    fields_to_remove = [
        'id', 'object', 'account', 'last_activity_date', 'created_at', 'updated_at', 'birthdate',
        'deceased_date', 'information', 'contact_information', 'reminders', 'tasks',
        'activities', 'relationships', 'gifts', 'pets', 'addresses', 'notes'
    ]
    for key in fields_to_remove:
        payload.pop(key, None)
    return call(f"contacts/{contact_id}", "PUT", payload)

def delete_contact(contact_id: int) -> Optional[Dict[str, Any]]:
    """DELETE /contacts/:id - Deletes a contact."""
    call(f"contacts/{contact_id}", "DELETE")
    return {"deleted": True, "id": contact_id}

def set_contact_occupation(contact_id: int, job_title: str = "", company_name: str = "") -> Dict[str, Any]:
    """Helper to set a contact's work information."""
    return update_contact(contact_id, {"work_job_title": job_title, "work_company_name": company_name})


# === Contact Sub-Resources: Addresses ===

def add_address(contact_id: int, name: str, **kwargs: Any) -> Dict[str, Any]:
    """POST /addresses - Creates a new address for a contact."""
    payload = {"contact_id": contact_id, "name": name}
    payload.update(kwargs)
    return call("addresses", "POST", payload=payload)

def update_address(address_id: int, contact_id: int, **kwargs: Any) -> Dict[str, Any]:
    """PUT /addresses/:id - Updates an existing address."""
    payload = {"contact_id": contact_id}
    payload.update(kwargs)
    return call(f"addresses/{address_id}", "PUT", payload=payload)

def delete_address(address_id: int) -> Dict[str, Any]:
    """DELETE /addresses/:id - Deletes an address."""
    call(f"addresses/{address_id}", "DELETE")
    return {"deleted": True, "id": address_id}


# # === Contact Sub-Resources: Pets ===
"""The Pets API is currently not documented in the latest version of Monica. And I couldn't figure out how to use it. Checked the source code on github, but I didn't understand it."""
# def add_pet(contact_id: int, name: str, **kwargs: Any) -> Dict[str, Any]:
#     """POST /contacts/:id/pets - Adds a pet to a contact."""
#     return call(f"contacts/{contact_id}/pets", "POST", {"name": name, **kwargs})

# def update_pet(pet_id: int, **kwargs: Any) -> Dict[str, Any]:
#     """PUT /pets/:id - Updates an existing pet's details."""
#     return call(f"pets/{pet_id}", "PUT", payload=kwargs)

# def delete_pet(pet_id: int) -> Dict[str, Any]:
#     """DELETE /pets/:id - Deletes a pet."""
#     call(f"pets/{pet_id}", "DELETE")
#     return {"deleted": True, "id": pet_id}


# === Contact Sub-Resources: Fields, Documents, Photos ===

def set_contact_field_value(contact_id: int, field_type_id: int, data: Any) -> Dict[str, Any]:
    """POST /contacts/:id/contactfields - Sets a custom field value for a contact."""
    payload = {
        "contact_id": contact_id,
        "contact_field_type_id": field_type_id,
        "data": data,
    }
    return call("contactfields", "POST", payload)

def upload_document_for_contact(contact_id: int, filepath: str) -> Dict[str, Any]:
    """POST /contacts/:id/documents - Uploads a document for a contact."""
    return upload_file(f"contacts/{contact_id}/documents", filepath, file_key="document")

def upload_photo_for_contact(contact_id: int, filepath: str) -> Dict[str, Any]:
    """POST /contacts/:id/photos - Uploads a photo for a contact."""
    return upload_file(f"contacts/{contact_id}/photos", filepath, file_key="photo")


# === Relationships ===

def create_relationship(contact_is: int, relationship_type_id: int, of_contact: int) -> Dict[str, Any]:
    """POST /relationships - Creates a new relationship."""
    payload = {
        "contact_is": contact_is,
        "relationship_type_id": relationship_type_id,
        "of_contact": of_contact,
    }
    return call("relationships", "POST", payload=payload)

def update_relationship(relationship_id: int, relationship_type_id: int) -> Dict[str, Any]:
    """PUT /relationships/:id - Updates an existing relationship's type."""
    return call(f"relationships/{relationship_id}", "PUT", payload={"relationship_type_id": relationship_type_id})

def delete_relationship(relationship_id: int) -> Optional[Dict[str, Any]]:
    """DELETE /relationships/:id - Deletes a relationship."""
    call(f"relationships/{relationship_id}", "DELETE")
    return {"deleted": True, "id": relationship_id}


# === Activities ===

# def list_all_activities(page: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
#     """GET /activities - Lists all activities across all contacts."""
#     return call("activities", params={"page": page, "limit": limit})

# def list_activities_for_contact(contact_id: int) -> List[Dict[str, Any]]:
#     """GET /contacts/:id/activities - Lists all activities for a specific contact."""
#     return call(f"contacts/{contact_id}/activities")

# def create_activity(contact_ids: List[int], summary: str, activity_type_id: int, happened_at: Optional[str] = None, description: str = "", emotions: Optional[List[int]] = None) -> Dict[str, Any]:
#     """POST /activities - Creates a new activity. Date format for happened_at: 'YYYY-MM-DD'."""
#     if not happened_at:
#         happened_at = datetime.now().strftime("%Y-%m-%d")
#     payload = {
#         "summary": summary,
#         "happened_at": happened_at,
#         "activity_type_id": activity_type_id,
#         "contacts": contact_ids,
#     }
#     if description:
#         payload["description"] = description
#     if emotions:
#         payload["emotions"] = emotions
#     return call("activities", "POST", payload)

# def update_activity(activity_id: int, **kwargs: Any) -> Dict[str, Any]:
#     """PUT /activities/:id - Updates an existing activity."""
#     return call(f"activities/{activity_id}", "PUT", payload=kwargs)

# def delete_activity(activity_id: int) -> Dict[str, Any]:
#     """DELETE /activities/:id - Deletes an activity."""
#     call(f"activities/{activity_id}", "DELETE")
#     return {"deleted": True, "id": activity_id}


# === Notes ===

def list_all_notes(limit: int = None, page: int = None) -> Dict[str, Any]:
    """GET /notes/ - List all notes in your account."""
    params = {}
    if limit is not None:
        params['limit'] = limit
    if page is not None:
        params['page'] = page
    return call("notes", "GET", params=params)

def list_contact_notes(contact_id: int, limit: int = None, page: int = None) -> Dict[str, Any]:
    """GET /contacts/:id/notes - List all notes for a specific contact."""
    params = {}
    if limit is not None:
        params['limit'] = limit
    if page is not None:
        params['page'] = page
    return call(f"contacts/{contact_id}/notes", "GET", params=params)

def get_note(note_id: int) -> Dict[str, Any]:
    """GET /notes/:id - Get a specific note."""
    return call(f"notes/{note_id}", "GET")

def create_note(contact_id: int, body: str, is_favorite: bool = False) -> Dict[str, Any]:
    """POST /notes - Creates a new note for a contact."""
    return call("notes", "POST", {"contact_id": contact_id, "body": body, "is_favorite": bool(is_favorite)})

def update_note(
    note_id: int,
    body: Optional[str] = None,
    contact_id: Optional[int] = None,
    is_favorited: Optional[bool] = None
) -> Dict[str, Any]:
    """
    PUT /notes/:id - Updates a note.
    """
    if body is None and is_favorited is None:
        raise ValueError("At least one parameter to update (body or is_favorited) must be provided.")

    payload = {}
    if body is not None:
        payload["body"] = body
    if is_favorited is not None:
        payload["is_favorited"] = 1 if is_favorited else 0
    if contact_id is not None:
        payload["contact_id"] = contact_id
    else:
        print(f"contact_id not provided. Fetching current note {note_id} to get associated contact_id...")
        note_details = get_note(note_id)
        try:
            payload["contact_id"] = note_details['contact']['id']
        except (KeyError, TypeError) as e:
            raise ValueError(
                f"Could not retrieve existing contact_id for note {note_id}. "
                f"The note may not exist or the API response is malformed. Error: {e}"
            )

    return call(f"notes/{note_id}", "PUT", payload)

def delete_note(note_id: int) -> Dict[str, Any]:
    """DELETE /notes/:id - Deletes a note."""
    call(f"notes/{note_id}", "DELETE")
    return {"deleted": True, "id": note_id}


# === Reminders ===

def create_reminder(contact_id: int, title: str, next_expected_date: str, frequency_type: str = "one_time", 
                  frequency_number: Optional[int] = None, description: str = "") -> Dict[str, Any]:
    """POST /reminders - Creates a reminder for a contact.
    
    Args:
        contact_id: The ID of the contact that the reminder is associated with.
        title: The title of the reminder. Max 100000 characters.
        next_expected_date: The date, in the future, when we should warn the user about this reminder. Format: YYYY-MM-DD.
        frequency_type: The frequency type indicates if the reminder is recurring. Values: one_time, week, month, year.
        frequency_number: The frequency of which the event should occur.
        description: A description about what the reminder is. Max 1000000 characters.
    """
    payload = {
        "contact_id": contact_id,
        "title": title, 
        "initial_date": next_expected_date,
        "frequency_type": frequency_type,
        "frequency_number" : frequency_number
    }
    
    if description:
        payload["description"] = description
        
    return call("reminders", "POST", payload)

def update_reminder(reminder_id: int, title: str = None, description: str = None,
                   next_expected_date: str = None, frequency_type: str = None,
                   frequency_number: int = None, contact_id: int = None) -> Dict[str, Any]:
    """PUT /reminders/:id - Updates an existing reminder."""
    payload = {}
    if title is not None:
        payload["title"] = title
    if description is not None:
        payload["description"] = description
    if next_expected_date is not None:
        payload["initial_date"] = next_expected_date
    if frequency_type is not None:
        payload["frequency_type"] = frequency_type
    if frequency_number is not None:
        payload["frequency_number"] = frequency_number
    if contact_id is not None:
        payload["contact_id"] = contact_id
        
    return call(f"reminders/{reminder_id}", "PUT", payload)

def delete_reminder(reminder_id: int) -> Optional[Dict[str, Any]]:
    """DELETE /reminders/:id - Deletes a reminder."""
    call(f"reminders/{reminder_id}", "DELETE")
    return {"deleted": True, "id": reminder_id}


# === Tasks ===

def get_task(task_id: int) -> Dict[str, Any]:
    """GET /tasks/:id - Gets a specific task."""
    return call(f"tasks/{task_id}")

def list_tasks(contact_id: Optional[int] = None, page: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
    """GET /tasks or GET /contacts/:id/tasks - Lists all tasks or tasks for a specific contact."""
    endpoint = f"contacts/{contact_id}/tasks" if contact_id else "tasks"
    return call(endpoint, params={"page": page, "limit": limit})


def create_task(
    title: str,
    contact_id: int,
    completed: int = 0,
    description: Optional[str] = None,
    completed_at: Optional[str] = None
) -> Dict[str, Any]:
    """POST /tasks - Creates a new task."""
    payload = {
        "title": title,
        "contact_id": contact_id,
        "completed": completed,
    }
    if description is not None:
        payload["description"] = description
    if completed_at is not None:
        payload["completed_at"] = completed_at
        
    return call("tasks", "POST", payload)


def update_task(
    task_id: int,
    contact_id: int,
    completed: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    completed_at: Optional[str] = None
) -> Dict[str, Any]:
    """
    PUT /tasks/:id - Updates a task.
    """
    if title is None:
        current_task = get_task(task_id)
        title = current_task['title']
        
    payload = {
        "title": title,
        "contact_id": contact_id,
        "completed": completed
    }
    
    if description is not None:
        payload["description"] = description
        
    if completed_at is not None:
        payload["completed_at"] = completed_at
        
    return call(f"tasks/{task_id}", "PUT", payload)

def delete_task(task_id: int) -> Dict[str, Any]:
    """DELETE /tasks/:id - Deletes a task."""
    return call(f"tasks/{task_id}", "DELETE")


# === Debts ===

def list_debts(
    contact_id: Optional[int] = None,
    page: int = 1,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    GET /debts or GET /contacts/:id/debts 
    """
    endpoint = f"contacts/{contact_id}/debts" if contact_id else "debts"
    return call(endpoint, params={"page": page, "limit": limit})


def get_debt(debt_id: int) -> Dict[str, Any]:
    """GET /debts/:id - Gets a specific debt."""
    return call(f"debts/{debt_id}")


def create_debt(
    contact_id: int,
    in_debt: Literal["yes", "no"],
    status: Literal["inprogress", "complete"],
    amount: int,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """POST /debts - Adds a new debt."""
    payload = {
        "contact_id": contact_id,
        "in_debt": in_debt,
        "status": status,
        "amount": amount,
    }
    if reason is not None:
        payload["reason"] = reason

    return call("debts", "POST", payload)


def update_debt(
    debt_id: int,
    contact_id: int,
    in_debt: Literal["yes", "no"],
    status: Literal["inprogress", "complete"],
    amount: int,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """PUT /debts/:id - Updates a debt."""
    payload = {
        "contact_id": contact_id,
        "in_debt": in_debt,
        "status": status,
        "amount": amount,
    }
    if reason is not None:
        payload["reason"] = reason
        
    return call(f"debts/{debt_id}", "PUT", payload)


def delete_debt(debt_id: int) -> Dict[str, Any]:
    """DELETE /debts/:id - Deletes a debt."""
    return call(f"debts/{debt_id}", "DELETE")


# === Tags ===


def list_tags(page: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
    """GET /tags - Lists all available tags in the account."""
    return call("tags", params={"page": page, "limit": limit})

def get_tag(tag_id: int) -> Dict[str, Any]:
    """GET /tags/:id - Gets a specific tag."""
    return call(f"tags/{tag_id}")

def create_tag(name: str) -> Dict[str, Any]:
    """POST /tags - Creates a new tag."""
    return call("tags", "POST", {"name": name})

def update_tag(tag_id: int, name: str) -> Dict[str, Any]:
    """PUT /tags/:id - Updates a tag's name."""
    return call(f"tags/{tag_id}", "PUT", {"name": name})

def delete_tag(tag_id: int) -> Dict[str, Any]:
    """DELETE /tags/:id - Deletes a tag from the account."""
    return call(f"tags/{tag_id}", "DELETE")

def set_tags_for_contact(contact_id: int, tag_names: List[str]) -> Dict[str, Any]:
    """POST /contacts/:id/setTags - Associates a list of tags with a contact, creating them if necessary."""
    payload = {"tags": tag_names}
    return call(f"contacts/{contact_id}/setTags", "POST", payload)

def unset_tags_for_contact(contact_id: int, tag_ids: List[int]) -> Dict[str, Any]:
    """POST /contacts/:id/unsetTag - Removes one or more specific tags from a contact by their IDs."""
    payload = {"tags": tag_ids}
    return call(f"contacts/{contact_id}/unsetTag", "POST", payload)

def unset_all_tags_for_contact(contact_id: int) -> Dict[str, Any]:
    """POST /contacts/:id/unsetTags - Removes all tags from a contact."""
    return call(f"contacts/{contact_id}/unsetTags", "POST")

# === Journal & Days ===

def list_journal_entries(page: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
    """GET /journal - Lists all entries in your journal."""
    return call("journal", params={"page": page, "limit": limit})

def get_journal_entry(journal_id: int) -> Dict[str, Any]:
    """GET /journal/:id - Gets a specific journal entry."""
    return call(f"journal/{journal_id}")

def create_journal_entry(title: str, post: str) -> Dict[str, Any]:
    """POST /journal - Creates a journal entry."""
    payload = {"title": title, "post": post}
    return call("journal", "POST", payload)

def update_journal_entry(journal_id: int, title: str, post: str) -> Dict[str, Any]:
    """PUT /journal/:id - Updates a journal entry."""
    payload = {"title": title, "post": post}
    return call(f"journal/{journal_id}", "PUT", payload)

def delete_journal_entry(journal_id: int) -> Dict[str, Any]:
    """
    DELETE /journal/:id - Deletes a journal entry.
    
    Note: The official documentation contains a typo for this endpoint (listing /calls/:id).
    This function uses the correct /journal/:id endpoint.
    """
    return call(f"journal/{journal_id}", "DELETE")


# === Gifts ===

def list_gifts(
    contact_id: Optional[int] = None,
    page: int = 1,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    GET /gifts or GET /contacts/:id/gifts - Lists all gifts or gifts for a specific contact.
    """
    endpoint = f"contacts/{contact_id}/gifts" if contact_id else "gifts"
    return call(endpoint, params={"page": page, "limit": limit})


def get_gift(gift_id: int) -> Dict[str, Any]:
    """GET /gifts/:id - Gets a specific gift."""
    return call(f"gifts/{gift_id}")


def create_gift(
    contact_id: int,
    name: str,
    status: Literal["idea", "offered", "received"],
    recipient_id: Optional[int] = None,
    comment: Optional[str] = None,
    url: Optional[str] = None,
    amount: Optional[Union[int, float]] = None,
    date: Optional[str] = None
) -> Dict[str, Any]:
    """POST /gifts - Records a new gift for a contact."""
    payload = {
        "contact_id": contact_id,
        "name": name,
        "status": status,
    }
    if recipient_id is not None:
        payload["recipient_id"] = recipient_id
    if comment is not None:
        payload["comment"] = comment
    if url is not None:
        payload["url"] = url
    if amount is not None:
        payload["amount"] = amount
    if date is not None:
        payload["date"] = date

    return call("gifts", "POST", payload)


def update_gift(
    gift_id: int,
    contact_id: int,
    name: str,
    status: Literal["idea", "offered", "received"],
    recipient_id: Optional[int] = None,
    comment: Optional[str] = None,
    url: Optional[str] = None,
    amount: Optional[Union[int, float]] = None,
    date: Optional[str] = None
) -> Dict[str, Any]:
    """PUT /gifts/:id - Updates a gift."""
    payload = {
        "contact_id": contact_id,
        "name": name,
        "status": status,
    }
    if recipient_id is not None:
        payload["recipient_id"] = recipient_id
    if comment is not None:
        payload["comment"] = comment
    if url is not None:
        payload["url"] = url
    if amount is not None:
        payload["amount"] = amount
    if date is not None:
        payload["date"] = date
        
    return call(f"gifts/{gift_id}", "PUT", payload)


def delete_gift(gift_id: int) -> Dict[str, Any]:
    """DELETE /gifts/:id - Deletes a gift."""
    return call(f"gifts/{gift_id}", "DELETE")

# === Calls ===

def list_calls(
    contact_id: Optional[int] = None,
    page: int = 1,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """GET /calls or GET /contacts/:id/calls - Lists all calls or calls for a specific contact."""
    endpoint = f"contacts/{contact_id}/calls" if contact_id else "calls"
    return call(endpoint, params={"page": page, "limit": limit})


def get_call(call_id: int) -> Dict[str, Any]:
    """GET /calls/:id - Gets a specific call."""
    return call(f"calls/{call_id}")


def create_call(contact_id: int, called_at: str, content: str) -> Dict[str, Any]:
    """POST /calls - Logs a call with a contact. Date format for called_at: 'YYYY-MM-DD'"""
    payload = {
        "contact_id": contact_id,
        "called_at": called_at,
        "content": content,
    }
    return call("calls", "POST", payload)


def update_call(call_id: int, contact_id: int, called_at: str, content: str) -> Dict[str, Any]:
    """PUT /calls/:id - Updates a call. Date format for called_at: 'YYYY-MM-DD'"""
    payload = {
        "contact_id": contact_id,
        "called_at": called_at,
        "content": content,
    }
    return call(f"calls/{call_id}", "PUT", payload)


def delete_call(call_id: int) -> Dict[str, Any]:
    """DELETE /calls/:id - Deletes a call."""
    return call(f"calls/{call_id}", "DELETE")

# === Conversations & Messages ===

def list_conversations(
    contact_id: Optional[int] = None,
    page: int = 1,
    limit: int = 15
) -> List[Dict[str, Any]]:
    """GET /conversations or GET /contacts/:id/conversations - Lists all conversations or those for a contact."""
    endpoint = f"contacts/{contact_id}/conversations" if contact_id else "conversations"
    return call(endpoint, params={"page": page, "limit": limit})


def get_conversation(conversation_id: int) -> Dict[str, Any]:
    """GET /conversations/:id - Gets a specific conversation, including its messages."""
    return call(f"conversations/{conversation_id}")


def create_conversation(
    contact_id: int,
    happened_at: str,
    contact_field_type_id: int
) -> Dict[str, Any]:
    """POST /conversations - Creates a new conversation container. Date format for happened_at: 'YYYY-MM-DD'."""
    payload = {
        "contact_id": contact_id,
        "happened_at": happened_at,
        "contact_field_type_id": contact_field_type_id,
    }
    return call("conversations", "POST", payload)


def update_conversation(conversation_id: int, contact_id: int, contact_field_type_id: int, happened_at: Optional[str] = None) -> Dict[str, Any]:
    """PUT /conversations/:id - Updates a conversation. The contact_field_type_id is required."""
    payload = {
        "contact_id": contact_id,
        "contact_field_type_id": contact_field_type_id
    }
    if happened_at is not None:
        payload["happened_at"] = happened_at
    return call(f"conversations/{conversation_id}", "PUT", payload)


def delete_conversation(conversation_id: int) -> Dict[str, Any]:
    """DELETE /conversations/:id - Deletes a conversation and all its messages."""
    return call(f"conversations/{conversation_id}", "DELETE")


# --- Message Management ---

def add_message_to_conversation(
    conversation_id: int,
    contact_id: int,
    written_at: str,
    written_by_me: bool,
    content: str
) -> Dict[str, Any]:
    """POST /conversations/:id/messages - Adds a message to a conversation. Date format for written_at: 'YYYY-MM-DD'."""
    payload = {
        "contact_id": contact_id,
        "written_at": written_at,
        "written_by_me": written_by_me,
        "content": content,
    }
    return call(f"conversations/{conversation_id}/messages", "POST", payload)


def update_message_in_conversation(
    conversation_id: int,
    message_id: int,
    contact_id: int,
    written_at: str,
    written_by_me: bool,
    content: str
) -> Dict[str, Any]:
    """PUT /conversations/:id/messages/:id - Updates a message in a conversation. Date format for written_at: 'YYYY-MM-DD'."""
    payload = {
        "contact_id": contact_id,
        "written_at": written_at,
        "written_by_me": written_by_me,
        "content": content,
    }
    return call(f"conversations/{conversation_id}/messages/{message_id}", "PUT", payload)


def delete_message(conversation_id: int, message_id: int) -> Dict[str, Any]:
    """DELETE /conversations/:id/messages/:id - Deletes a message from a conversation."""
    return call(f"conversations/{conversation_id}/messages/{message_id}", "DELETE")

# === Companies ===

def list_companies() -> List[Dict[str, Any]]:
    """GET /companies - Lists all companies."""
    return call("companies")

def get_company(company_id: int) -> Dict[str, Any]:
    """GET /companies/:id - Gets a specific company."""
    return call(f"companies/{company_id}")

def create_company(name: str, **kwargs: Any) -> Dict[str, Any]:
    """POST /companies - Creates a company."""
    payload = {"name": name}
    payload.update(kwargs)
    return call("companies", "POST", payload)

def delete_company(company_id: int) -> Dict[str, Any]:
    """DELETE /companies/:id - Deletes a company."""
    call(f"companies/{company_id}", "DELETE")
    return {"deleted": True, "id": company_id}

if __name__ == "__main__":
    print("--- Monica API Wrapper ---")
    print("Used to interact with Monica CRM API.")