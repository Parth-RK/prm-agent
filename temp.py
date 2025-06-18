import os
import dotenv
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional

# --- Configuration & Initialization ---
dotenv.load_dotenv()

API_URL = os.environ.get("MONICA_API_URL")
API_TOKEN = os.environ.get("MONICA_TOKEN")

if not API_URL or not API_TOKEN:
    raise ValueError("MONICA_API_URL and MONICA_TOKEN must be set in your environment or a .env file.")

HEADERS = {"Authorization": f"Bearer {API_TOKEN}", "Accept": "application/json"}


# === Core Helper Functions ===

def call(endpoint: str, method: str = "GET", payload: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Any:
    """A helper function to make JSON requests to the Monica API."""
    url = f"{API_URL}/{endpoint}"
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

# === Account-Level Resources (Read-Only) ===

def get_user() -> Dict[str, Any]:
    """GET /me - Fetches the authenticated user's details."""
    return call("me")

def list_genders() -> List[Dict[str, Any]]:
    """GET /genders - Lists all available genders."""
    return call("genders")
def list_currencies() -> List[Dict[str, Any]]: return call("currencies")
def list_countries() -> List[Dict[str, Any]]: return call("countries")
def list_activity_types() -> List[Dict[str, Any]]: return call("activitytypes")
def list_contact_field_types() -> List[Dict[str, Any]]: return call("contactfieldtypes")
def list_relationship_types() -> List[Dict[str, Any]]: return call("relationshiptypes")


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

# === Contact Sub-Resources (Addresses, Pets, etc.) ===
def add_address(contact_id: int, **kwargs: Any) -> Dict[str, Any]:
    """POST /contacts/:id/addresses - Adds an address to a contact.
    e.g., street="123 Main St", city="Anytown", country="US"
    """
    return call(f"contacts/{contact_id}/addresses", "POST", payload=kwargs)

def update_address(address_id: int, **kwargs: Any) -> Dict[str, Any]:
    """PUT /addresses/:id - Updates an existing address."""
    return call(f"addresses/{address_id}", "PUT", payload=kwargs)

def delete_address(address_id: int) -> Dict[str, Any]:
    """DELETE /addresses/:id - Deletes an address."""
    call(f"addresses/{address_id}", "DELETE")
    return {"deleted": True, "id": address_id}

def add_pet(contact_id: int, name: str, **kwargs: Any) -> Dict[str, Any]:
    return call(f"contacts/{contact_id}/pets", "POST", {"name": name, **kwargs})

def update_pet(pet_id: int, **kwargs: Any) -> Dict[str, Any]:
    """PUT /pets/:id - Updates an existing pet's details."""
    return call(f"pets/{pet_id}", "PUT", payload=kwargs)

def delete_pet(pet_id: int) -> Dict[str, Any]:
    """DELETE /pets/:id - Deletes a pet."""
    call(f"pets/{pet_id}", "DELETE")
    return {"deleted": True, "id": pet_id}

def set_contact_field_value(contact_id: int, field_type_id: int, data: Any) -> Dict[str, Any]:
    return call(f"contacts/{contact_id}/contactfields", "POST", {"contact_field_type_id": field_type_id, "data": data})


def upload_document_for_contact(contact_id: int, filepath: str) -> Dict[str, Any]:
    return upload_file(f"contacts/{contact_id}/documents", filepath, file_key="document")

def upload_photo_for_contact(contact_id: int, filepath: str) -> Dict[str, Any]:
    return upload_file(f"contacts/{contact_id}/photos", filepath, file_key="photo")

# === Relationships ===
def set_relationship(contact_id: int, relationship_type_id: int, with_contact_id: int) -> Dict[str, Any]:
    return call(f"contacts/{contact_id}/relationships", "POST", {"relationship_type_id": relationship_type_id, "contact_id": with_contact_id})

def delete_relationship(relationship_id: int) -> Optional[Dict[str, Any]]:
    call(f"relationships/{relationship_id}", "DELETE")
    return {"deleted": True, "id": relationship_id}


# === Reminders ===
def create_reminder(contact_id: int, title: str, date: str) -> Dict[str, Any]:
    return call("reminders", "POST", {"contact_id": contact_id, "title": title, "initial_date": date})

def update_reminder(reminder_id: int, **kwargs: Any) -> Dict[str, Any]:
    """PUT /reminders/:id - Updates a reminder with the given key-value pairs."""
    return call(f"reminders/{reminder_id}", "PUT", kwargs)

def delete_reminder(reminder_id: int) -> Optional[Dict[str, Any]]:
    call(f"reminders/{reminder_id}", "DELETE")
    return {"deleted": True, "id": reminder_id}


# === Debts ===

def create_debt(contact_id: int, in_debt_to: str, amount: float, currency_code: str, reason: str = "") -> Dict[str, Any]:
    """POST /debts - Adds a new debt. in_debt_to must be 'me' or 'them'."""
    payload = {"contact_id": contact_id, "in_debt_to": in_debt_to, "amount": amount, "currency_code": currency_code, "reason": reason}
    return call("debts", "POST", payload)

def list_debts_for_contact(contact_id: int) -> List[Dict[str, Any]]:
    """GET /contacts/:id/debts - Lists all debts for a specific contact."""
    return call(f"contacts/{contact_id}/debts")

def delete_debt(debt_id: int) -> Dict[str, Any]:
    """DELETE /debts/:id - Deletes a debt."""
    call(f"debts/{debt_id}", "DELETE")
    return {"deleted": True, "id": debt_id}


# === Activities ===

# Place these in the "Activities" section

def list_all_activities(page: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
    """GET /activities - Lists all activities across all contacts."""
    return call("activities", params={"page": page, "limit": limit})

def list_activities_for_contact(contact_id: int) -> List[Dict[str, Any]]:
    """GET /contacts/:id/activities - Lists all activities for a specific contact."""
    return call(f"contacts/{contact_id}/activities")

def create_activity(contact_id: int, summary: str, description: str = "", happened_at: str = None) -> Dict[str, Any]:
    """POST /activities - Creates a new activity. Date format for happened_at: 'YYYY-MM-DD HH:MM:SS'."""
    if not happened_at:
        happened_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = {"contact_id": contact_id, "summary": summary, "description": description, "happened_at": happened_at}
    return call("activities", "POST", payload)

def update_activity(activity_id: int, **kwargs: Any) -> Dict[str, Any]:
    """PUT /activities/:id - Updates an existing activity.
    Can update 'summary', 'description', 'happened_at'.
    """
    return call(f"activities/{activity_id}", "PUT", payload=kwargs)

def delete_activity(activity_id: int) -> Dict[str, Any]:
    """DELETE /activities/:id - Deletes an activity."""
    call(f"activities/{activity_id}", "DELETE")
    return {"deleted": True, "id": activity_id}


# === Notes, Documents & Photos ===

def create_note(contact_id: int, body: str, is_favorite: bool = False) -> Dict[str, Any]:
    """POST /notes - Creates a new note for a contact."""
    return call("notes", "POST", {"contact_id": contact_id, "body": body, "is_favorite": bool(is_favorite)})

def update_note(note_id: int, body: str, is_favorite: bool = False) -> Dict[str, Any]:
    """PUT /notes/:id - Updates a note."""
    payload = {}
    if body is not None:
        payload["body"] = body
    if is_favorite is not None:
        payload["is_favorite"] = bool(is_favorite)
    if not payload:
        raise ValueError("At least one parameter (body or is_favorite) must be provided for update")
    return call(f"notes/{note_id}", "PUT", payload)

def delete_note(note_id: int) -> Dict[str, Any]:
    """DELETE /notes/:id - Deletes a note."""
    call(f"notes/{note_id}", "DELETE")
    return {"deleted": True, "id": note_id}

def upload_document_for_contact(contact_id: int, filepath: str) -> Dict[str, Any]:
    """POST /contacts/:id/documents - Uploads a document for a contact."""
    return upload_file(f"contacts/{contact_id}/documents", filepath)

def upload_photo_for_contact(contact_id: int, filepath: str) -> Dict[str, Any]:
    """POST /contacts/:id/photos - Uploads a photo for a contact."""
    return upload_file(f"contacts/{contact_id}/photos", filepath)


# === Tasks ===

def list_tasks(contact_id: Optional[int] = None, page: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
    """GET /tasks or GET /contacts/:id/tasks - Lists all tasks or tasks for a specific contact."""
    endpoint = f"contacts/{contact_id}/tasks" if contact_id else "tasks"
    return call(endpoint, params={"page": page, "limit": limit})

def create_task(title: str, contact_id: Optional[int] = None, **kwargs: Any) -> Dict[str, Any]:
    """POST /tasks - Creates a new task, optionally assigned to a contact."""
    payload = {"title": title, **kwargs}
    if contact_id:
        payload["contact_id"] = contact_id
    return call("tasks", "POST", payload)

def update_task(task_id: int, **kwargs: Any) -> Dict[str, Any]:
    """PUT /tasks/:id - Updates a task with the given key-value pairs."""
    return call(f"tasks/{task_id}", "PUT", kwargs)

def delete_task(task_id: int) -> Optional[Dict[str, Any]]:
    call(f"tasks/{task_id}", "DELETE")
    return {"deleted": True, "id": task_id}


# === Journal & Days ===

def create_journal_entry(entry: str, date: str = None) -> Dict[str, Any]:
    """POST /journal - Creates a journal entry for a given day."""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    return call("journal", "POST", {"post": entry, "date": date})

def set_day_emotion(emotion: str, date: str = None) -> Dict[str, Any]:
    """POST /days - Records how your day went with an emotion."""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    return call("days", "POST", {"emotion": emotion, "date": date})


# === Tags ===

def list_tags() -> List[Dict[str, Any]]:
    """GET /tags - Lists all available tags in the account."""
    return call("tags")

def attach_tag(contact_id: int, tag_id: int) -> Dict[str, Any]:
    """POST /contacts/:id/tags - Attaches an existing tag to a contact."""
    return call(f"contacts/{contact_id}/tags", "POST", {"tag_id": tag_id})

def detach_tag(contact_id: int, tag_id: int) -> Dict[str, Any]:
    """DELETE /contacts/:id/tags/:id - Detaches a tag from a contact."""
    call(f"contacts/{contact_id}/tags/{tag_id}", "DELETE")
    return {"detached": True, "contact_id": contact_id, "tag_id": tag_id}


# === Additional Resources ===

def create_gift(contact_id: int, name: str, **kwargs: Any) -> Dict[str, Any]:
    """POST /gifts - Records a gift for a contact."""
    payload = {"contact_id": contact_id, "name": name}
    payload.update(kwargs)
    return call("gifts", "POST", payload)

def list_gifts_for_contact(contact_id: int) -> List[Dict[str, Any]]:
    """GET /contacts/:id/gifts - Lists all gifts for a specific contact."""
    return call(f"contacts/{contact_id}/gifts")

def delete_gift(gift_id: int) -> Dict[str, Any]:
    """DELETE /gifts/:id - Deletes a gift."""
    call(f"gifts/{gift_id}", "DELETE")
    return {"deleted": True, "id": gift_id}

def create_call(contact_id: int, called_at: str, **kwargs: Any) -> Dict[str, Any]:
    """POST /calls - Logs a call with a contact. called_at: 'YYYY-MM-DD HH:MM:SS'"""
    payload = {"contact_id": contact_id, "called_at": called_at}
    payload.update(kwargs)
    return call("calls", "POST", payload)

def create_conversation(contact_id: int, happened_at: str, contact_field_type_id: int, **kwargs: Any) -> Dict[str, Any]:
    """POST /conversations - Logs a conversation. happened_at: 'YYYY-MM-DD HH:MM:SS'"""
    payload = {"contact_id": contact_id, "happened_at": happened_at, "contact_field_type_id": contact_field_type_id}
    payload.update(kwargs)
    return call("conversations", "POST", payload)

def create_company(name: str, **kwargs: Any) -> Dict[str, Any]:
    """POST /companies - Creates a company."""
    payload = {"name": name}
    payload.update(kwargs)
    return call("companies", "POST", payload)

def list_companies() -> List[Dict[str, Any]]:
    """GET /companies - Lists all companies."""
    return call("companies")

def get_company(company_id: int) -> Dict[str, Any]:
    """GET /companies/:id - Gets a specific company."""
    return call(f"companies/{company_id}")

def delete_company(company_id: int) -> Dict[str, Any]:
    """DELETE /companies/:id - Deletes a company."""
    call(f"companies/{company_id}", "DELETE")
    return {"deleted": True, "id": company_id}


# === Example Usage ===
if __name__ == "__main__":
    print("--- Monica API Caller Full Demo ---")
    created_contact_id = None
    try:
        user = get_user()
        print(f"Authenticated as: {user.get('first_name')} ({user.get('email')})")
        print("\n[1] Creating contact...")
        contact = create_contact("Sam", last_name="Jones", gender="other", notes="Initial note about Sam.")
        created_contact_id = contact["id"]
        print(f"  -> Created: {contact['first_name']} {contact['last_name']} (ID: {created_contact_id})")

        print("\n[2] Updating contact's notes...")
        updated_contact_note = create_note(created_contact_id, body="Updated note about Sam.")
        print(f"  -> Created note with ID: {updated_contact_note['id']} and body: {updated_contact_note['body']}")
        

    except Exception as e:
        print(f"\nAN ERROR OCCURRED: {e}")
    finally:
        if created_contact_id:
            print("\n--- Cleaning up created resources ---")
            d = input("Are you sure you want to delete this contact? (y/n): ").strip().lower()
            if d == 'y':
                delete_contact(created_contact_id)
                print(f"Deleting contact {created_contact_id}...")
            print("--- Cleanup complete ---")