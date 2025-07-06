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
    """GET /me - Fetches the authenticated user's details.

    Returns:
        Dict[str, Any]: A dictionary containing user details such as
                        first_name, last_name, email, timezone, and currency.
    """
    return call("me")

def list_genders() -> List[Dict[str, Any]]:
    """GET /genders - Lists all available genders.

    Returns:
        List[Dict[str, Any]]: A list of gender objects, each containing
                              'id', 'name', and 'account' details.
    """
    return call("genders")

def list_currencies() -> List[Dict[str, Any]]:
    """GET /currencies - Lists all available currencies.

    Returns:
        List[Dict[str, Any]]: A list of currency objects, each containing
                              'id', 'iso', 'name', and 'symbol'.
    """
    return call("currencies")

def list_countries() -> List[Dict[str, Any]]:
    """GET /countries - Lists all available countries.

    Returns:
        Dict[str, Any]: A dictionary of country objects, keyed by a 3-letter code,
                        with each object containing 'id' (2-letter ISO), 'name', and 'iso'.
    """
    return call("countries")

def list_activity_types() -> List[Dict[str, Any]]:
    """GET /activitytypes - Lists all available activity types.

    Returns:
        List[Dict[str, Any]]: A list of activity type objects, each with details
                              like 'id', 'name', and 'activity_type_category'.
    """
    return call("activitytypes")

def list_contact_field_types() -> List[Dict[str, Any]]:
    """GET /contactfieldtypes - Lists all available contact field types.

    Returns:
        List[Dict[str, Any]]: A list of contact field type objects, used to define
                              contact methods like 'Email' or 'Twitter'. Each object
                              contains 'id', 'name', 'protocol', etc.
    """
    return call("contactfieldtypes")

def list_relationship_types() -> List[Dict[str, Any]]:
    """GET /relationshiptypes - Lists all available relationship types.

    Returns:
        List[Dict[str, Any]]: A list of relationship type objects, each with
                              'id', 'name', 'name_reverse_relationship', etc.
    """
    return call("relationshiptypes")


# === Contacts ===

def get_contact_by_name(name: str, exact_match: bool = True) -> Optional[Dict[str, Any]]:
    """Finds a single contact by their first or full name."""
    contacts = list_contacts(query=name)
    if not contacts:
        return None
    
    # Try for an exact match first
    for contact in contacts:
        full_name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
        if name.lower() in full_name.lower():
            return contact # Return the first good match
            
    if exact_match:
        return None # If exact_match is required and we haven't found one.
        
    return contacts[0] # Otherwise, return the best guess

def get_contact_summary(contact_id: int) -> Dict[str, Any]:
    """Aggregates key information about a contact into a single object."""
    contact_details = get_contact(contact_id)
    notes = list_contact_notes(contact_id, limit=5) # Get last 5 notes
    tasks = list_tasks(contact_id, limit=5) # Get last 5 tasks
    
    summary = {
        "details": contact_details,
        "recent_notes": notes.get('data', []) if isinstance(notes, dict) else notes,
        "recent_tasks": tasks,
    }
    return summary

def list_contacts(query: Optional[str] = None, page: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
    """GET /contacts - Lists all contacts, with optional search query and pagination.

    Args:
        query (Optional[str]): A search term to filter contacts by name, food preferences, or job.
        page (int): The page number for pagination. Defaults to 1.
        limit (int): The number of items per page. Defaults to 10, max is 100.

    Returns:
        List[Dict[str, Any]]: A paginated list of contact summary objects.
    """
    params = {"page": page, "limit": limit}
    if query:
        params["query"] = query
    return call("contacts", params=params)

def get_contact(contact_id: int) -> Dict[str, Any]:
    """GET /contacts/:id - Fetches a single contact by their ID.

    This call returns the complete contact object, including detailed information
    about relationships, addresses, tags, and statistics.

    Args:
        contact_id (int): The unique identifier for the contact.

    Returns:
        Dict[str, Any]: A dictionary representing the full contact object.
    """
    return call(f"contacts/{contact_id}")

def create_contact(first_name: str, **kwargs: Any) -> Dict[str, Any]:
    """POST /contacts - Creates a new contact. 'first_name' is required.

    This function sets some boolean flags to False by default to ensure proper
    API behavior. To associate a birthdate or deceased date, you must provide
    the date components and set the corresponding 'is...known' flag to True.

    Args:
        first_name (str): The first name of the person (max 50 chars). This is required.
        **kwargs: Arbitrary keyword arguments that are passed directly to the
            API payload. Supported optional parameters include:
            - last_name (str): The contact's last name (max 100 chars).
            - nickname (str): The contact's nickname (max 100 chars).
            - gender_id (int): The ID for the gender (from list_genders()).
            - is_birthdate_known (bool): Must be True if providing date parts.
            - birthdate_year (int): Year of birth.
            - birthdate_month (int): Month of birth (1-12).
            - birthdate_day (int): Day of birth (1-31).
            - is_deceased (bool): Set to True if the contact is deceased.
            - is_deceased_date_known (bool): Must be True if providing deceased date.
            - deceased_date_year (int): Year of death.
            - deceased_date_month (int): Month of death.
            - deceased_date_day (int): Day of death.
            - food_preferences (str): Notes on food preferences.
            - how_we_met (str): Description of how you met.
            - first_met_day (int): Day you first met.
            - first_met_month (int): Month you first met.
            - first_met_year (int): Year you first met.
            - first_met_through_contact_id (int): ID of a mutual contact.
            - work_job_title (str): The contact's job title.
            - work_company_name (str): The contact's employer.

    Returns:
        Dict[str, Any]: A dictionary representing the newly created contact
                        as returned by the API.

    
    """
    payload = {"first_name": first_name, "is_birthdate_known": False, "is_deceased": False, "is_deceased_date_known": False}
    payload.update(kwargs)
    return call("contacts", "POST", payload)

def update_contact(contact_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
    """PUT /contacts/:id - Dynamically updates a contact's core fields.

    This function fetches the current contact data, applies the given updates,
    and sends the modified flat structure back to the API. Note that nested
    objects like relationships or addresses cannot be updated here; use their
    dedicated functions instead.

    Args:
        contact_id (int): The ID of the contact to update.
        updates (Dict[str, Any]): A dictionary of fields to update. Keys should
            match the parameters used in `create_contact`.

    Returns:
        Dict[str, Any]: The updated contact object from the API.
    """
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
    """DELETE /contacts/:id - Deletes a contact if contact id is known.

    Args:
        contact_id (int): The ID of the contact to delete.

    Returns:
        A confirmation dictionary `{"deleted": True, "id": contact_id}`.
    """
    call(f"contacts/{contact_id}", "DELETE")
    return {"deleted": True, "id": contact_id}

def set_contact_occupation(contact_id: int, job_title: str = "", company_name: str = "") -> Dict[str, Any]:
    """Helper to set a contact's work information.

    Note: This uses the general `update_contact` function. The Monica API also provides a
    dedicated `PUT /contacts/:id/work` endpoint which is not used by this helper.

    Args:
        contact_id (int): The ID of the contact.
        job_title (str): The contact's job title.
        company_name (str): The contact's employer name.

    Returns:
        Dict[str, Any]: The updated contact object.
    """
    return update_contact(contact_id, {"work_job_title": job_title, "work_company_name": company_name})


# === Contact Sub-Resources: Addresses ===

def add_address(contact_id: int, name: str, **kwargs: Any) -> Dict[str, Any]:
    """POST /addresses - Creates a new address and associates it with a contact.

    This function requires the ID of the contact and a descriptive name for
    the address. All other address components are optional and can be passed
    as keyword arguments.

    Args:
        contact_id (int): The unique ID of the contact to whom this address
                          will be linked. This is required.
        name (str): A descriptive label for the address (e.g., "Home", "Work").
                    Required, max 255 characters.
        **kwargs: Arbitrary keyword arguments that are passed directly
            to the API. Supported optional parameters include:
            - street (str): The street and number (max 255 chars).
            - city (str): The city name (max 255 chars).
            - province (str): The state or province name (max 255 chars).
            - postal_code (str): The ZIP or postal code (max 255 chars).
            - country (str): The 2-letter uppercase ISO code for the country (e.g., 'US').

    Returns:
        Dict[str, Any]: A dictionary representing the newly created address
                        object as returned by the API.

    Example:
        # Assuming you have a contact with ID 123
        add_address(
            contact_id=123,
            name="Work Office",
            street="1725 Slough Avenue",
            city="Scranton",
            province="PA",
            postal_code="18503",
            country="US"
        )
    """
    payload = {"contact_id": contact_id, "name": name}
    payload.update(kwargs)
    return call("addresses", "POST", payload=payload)

def update_address(address_id: int, contact_id: int, **kwargs: Any) -> Dict[str, Any]:
    """PUT /addresses/:id - Updates an existing address.

    Note: The `contact_id` is required by the API for updates.

    Args:
        address_id (int): The ID of the address to update.
        contact_id (int): The ID of the contact this address belongs to.
        **kwargs: A dictionary of address fields to update. See `add_address`
                  for available fields.

    Returns:
        Dict[str, Any]: The updated address object.
    """
    payload = {"contact_id": contact_id}
    payload.update(kwargs)
    return call(f"addresses/{address_id}", "PUT", payload=payload)

def delete_address(address_id: int) -> Dict[str, Any]:
    """DELETE /addresses/:id - Deletes an address.

    Args:
        address_id (int): The ID of the address to delete.

    Returns:
        A confirmation dictionary `{"deleted": True, "id": address_id}`.
    """
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
    """POST /contacts/:id/contactfields - Sets a custom field value for a contact.

    Args:
        contact_id (int): The ID of the contact.
        field_type_id (int): The ID of the field type (e.g., for 'Email' or 'Twitter').
                             Get this from `list_contact_field_types()`.
        data (Any): The value for the field (e.g., 'user@example.com').

    Returns:
        Dict[str, Any]: The newly created contact field object.
    """
    payload = {
        "contact_id": contact_id,
        "contact_field_type_id": field_type_id,
        "data": data,
    }
    return call("contactfields", "POST", payload)

def upload_document_for_contact(contact_id: int, filepath: str) -> Dict[str, Any]:
    """POST /contacts/:id/documents - Uploads a document for a contact.

    The API has a `POST /documents` endpoint, but this function uses the more specific
    `POST /contacts/:id/documents` route for clarity.

    Args:
        contact_id (int): The ID of the contact to associate the document with.
        filepath (str): The local path to the file to upload.

    Returns:
        Dict[str, Any]: The created document object from the API.
    """
    return upload_file(f"contacts/{contact_id}/documents", filepath, file_key="document")

def upload_photo_for_contact(contact_id: int, filepath: str) -> Dict[str, Any]:
    """POST /contacts/:id/photos - Uploads a photo for a contact.

    The API has a `POST /photos` endpoint, but this function uses the more specific
    `POST /contacts/:id/photos` route for clarity. The uploaded file's form key must be 'photo'.

    Args:
        contact_id (int): The ID of the contact to associate the photo with.
        filepath (str): The local path to the image file to upload.

    Returns:
        Dict[str, Any]: The created photo object from the API.
    """
    return upload_file(f"contacts/{contact_id}/photos", filepath, file_key="photo")


# === Relationships ===

def create_relationship(contact_is: int, relationship_type_id: int, of_contact: int) -> Dict[str, Any]:
    """POST /relationships - Creates a new relationship.

    Establishes a link like "[contact_is] is the [relationship_type] of [of_contact]".
    Example: `create_relationship(john_id, son_id, jane_id)` means "John is the son of Jane".

    Args:
        contact_is (int): The ID of the primary contact in the relationship.
        relationship_type_id (int): The ID of the relationship type (from `list_relationship_types()`).
        of_contact (int): The ID of the secondary contact.

    Returns:
        Dict[str, Any]: The newly created relationship object.
    """
    payload = {
        "contact_is": contact_is,
        "relationship_type_id": relationship_type_id,
        "of_contact": of_contact,
    }
    return call("relationships", "POST", payload=payload)

def update_relationship(relationship_id: int, relationship_type_id: int) -> Dict[str, Any]:
    """PUT /relationships/:id - Updates an existing relationship's type.

    This only changes the nature of the relationship, not the contacts involved.

    Args:
        relationship_id (int): The ID of the relationship to update.
        relationship_type_id (int): The new relationship type ID.

    Returns:
        Dict[str, Any]: The updated relationship object.
    """
    return call(f"relationships/{relationship_id}", "PUT", payload={"relationship_type_id": relationship_type_id})

def delete_relationship(relationship_id: int) -> Optional[Dict[str, Any]]:
    """DELETE /relationships/:id - Deletes a relationship.

    This removes the link between the two contacts entirely.

    Args:
        relationship_id (int): The ID of the relationship to delete.

    Returns:
        A confirmation dictionary `{"deleted": True, "id": relationship_id}`.
    """
    call(f"relationships/{relationship_id}", "DELETE")
    return {"deleted": True, "id": relationship_id}


# === Activities ===
"""Activities are not working for unknown reasons."""
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
#     """DELETE /activities/:id - Deletes a activity."""
#     call(f"activities/{activity_id}", "DELETE")
#     return {"deleted": True, "id": activity_id}


# === Notes ===

def list_all_notes(limit: int = None, page: int = None) -> Dict[str, Any]:
    """GET /notes/ - List all notes in your account.

    Args:
        limit (Optional[int]): The number of notes per page (max 100).
        page (Optional[int]): The page number to retrieve.

    Returns:
        A dictionary containing a list of note objects and pagination links.
    """
    params = {}
    if limit is not None:
        params['limit'] = limit
    if page is not None:
        params['page'] = page
    return call("notes", "GET", params=params)

def list_contact_notes(contact_id: int, limit: Optional[int] = None, page: Optional[int] = None) -> Dict[str, Any]:
    """GET /contacts/:id/notes - List all notes for a specific contact.

    Args:
        contact_id (int): The ID of the contact.
        limit (Optional[int]): The number of notes per page (max 100).
        page (Optional[int]): The page number to retrieve.

    Returns:
        A dictionary containing a list of note objects and pagination links.
    """
    params = {}
    if limit is not None:
        params['limit'] = limit
    if page is not None:
        params['page'] = page
    return call(f"contacts/{contact_id}/notes", "GET", params=params)

def get_note(note_id: int) -> Dict[str, Any]:
    """GET /notes/:id - Get a specific note.

    Args:
        note_id (int): The ID of the note to retrieve.

    Returns:
        Dict[str, Any]: The full note object.
    """
    return call(f"notes/{note_id}", "GET")

def create_note(contact_id: int, body: str, is_favorite: bool = False) -> Dict[str, Any]:
    """POST /notes - Creates a new note for a contact.

    Args:
        contact_id (int): The ID of the contact to associate the note with.
        body (str): The content of the note (max 100,000 characters).
        is_favorite (bool): Whether to mark the note as a favorite. The API expects
                            this as `is_favorited`. This function maps the name.

    Returns:
        Dict[str, Any]: The newly created note object.
    """
    return call("notes", "POST", {"contact_id": contact_id, "body": body, "is_favorited": bool(is_favorite)})

def update_note(
    note_id: int,
    body: Optional[str] = None,
    contact_id: Optional[int] = None,
    is_favorited: Optional[bool] = None
) -> Dict[str, Any]:
    """
    PUT /notes/:id - Updates a note.

    Note: The API requires the `contact_id` for updates. This function will
    fetch the existing note to find the `contact_id` if it is not provided.

    Args:
        note_id (int): The ID of the note to update.
        body (Optional[str]): The new content for the note (max 100,000 chars).
        contact_id (Optional[int]): The associated contact's ID.
        is_favorited (Optional[bool]): The new favorite status.

    Returns:
        Dict[str, Any]: The updated note object.

    Raises:
        ValueError: If neither 'body' nor 'is_favorited' is provided, or if
                    the `contact_id` cannot be determined.
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
    """DELETE /notes/:id - Deletes a note.

    Args:
        note_id (int): The ID of the note to delete.

    Returns:
        A confirmation dictionary `{"deleted": True, "id": note_id}`.
    """
    call(f"notes/{note_id}", "DELETE")
    return {"deleted": True, "id": note_id}


# === Reminders ===

def create_reminder(contact_id: int, title: str, next_expected_date: str, frequency_type: str = "one_time", 
                  frequency_number: Optional[int] = None, description: str = "") -> Dict[str, Any]:
    """POST /reminders - Creates a reminder for a contact.
    
    Args:
        contact_id (int): The ID of the contact the reminder is for.
        title (str): The title of the reminder (max 100,000 chars).
        next_expected_date (str): The date for the first occurrence in "YYYY-MM-DD" format.
                                  This is sent as `initial_date` to the API.
        frequency_type (str): How often it repeats. One of: "one_time", "week", "month", "year".
        frequency_number (Optional[int]): The interval for recurring reminders (e.g., every 3 weeks).
        description (str): Optional details for the reminder (max 1,000,000 chars).

    Returns:
        Dict[str, Any]: The newly created reminder object.
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
    """PUT /reminders/:id - Updates an existing reminder.

    Note: The Monica API requires `contact_id` for updates. This wrapper makes it optional,
    but the API call may fail if it's omitted.

    Args:
        reminder_id (int): The ID of the reminder to update.
        title (str, optional): The new title.
        description (str, optional): The new description.
        next_expected_date (str, optional): The new next date in "YYYY-MM-DD" format.
                                            Mapped to `initial_date`.
        frequency_type (str, optional): The new frequency type.
        frequency_number (int, optional): The new frequency interval.
        contact_id (int, optional): The associated contact's ID.

    Returns:
        Dict[str, Any]: The updated reminder object.
    """
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
    """DELETE /reminders/:id - Deletes a reminder.

    Args:
        reminder_id (int): The ID of the reminder to delete.

    Returns:
        A confirmation dictionary `{"deleted": True, "id": reminder_id}`.
    """
    call(f"reminders/{reminder_id}", "DELETE")
    return {"deleted": True, "id": reminder_id}


# === Tasks ===

def get_task(task_id: int) -> Dict[str, Any]:
    """GET /tasks/:id - Gets a specific task.

    Args:
        task_id (int): The ID of the task.

    Returns:
        Dict[str, Any]: The full task object.
    """
    return call(f"tasks/{task_id}")

def list_tasks(contact_id: Optional[int] = None, page: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
    """GET /tasks or GET /contacts/:id/tasks - Lists all tasks or tasks for a specific contact.

    Args:
        contact_id (Optional[int]): If provided, lists tasks for only this contact.
        page (int): The page number for pagination.
        limit (int): The number of items per page (max 100).

    Returns:
        List[Dict[str, Any]]: A list of task objects.
    """
    endpoint = f"contacts/{contact_id}/tasks" if contact_id else "tasks"
    return call(endpoint, params={"page": page, "limit": limit})


def create_task(
    title: str,
    contact_id: int,
    completed: int = 0,
    description: Optional[str] = None,
    completed_at: Optional[str] = None
) -> Dict[str, Any]:
    """POST /tasks - Creates a new task.

    Args:
        title (str): The title of the task (max 255 chars).
        contact_id (int): The ID of the contact this task is for.
        completed (int): The status of the task. `0` for incomplete, `1` for complete.
        description (Optional[str]): An optional description (max 1,000,000 chars).
        completed_at (Optional[str]): If completed, the date of completion ("YYYY-MM-DD").

    Returns:
        Dict[str, Any]: The newly created task object.
    """
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

    Note: `contact_id` and `completed` are required by the API for every update.
    The `title` is also required, so this function fetches it if not provided.

    Args:
        task_id (int): The ID of the task to update.
        contact_id (int): The ID of the associated contact.
        completed (int): The new status of the task (`0` or `1`).
        title (Optional[str]): The new title for the task.
        description (Optional[str]): The new description.
        completed_at (Optional[str]): The new completion date ("YYYY-MM-DD").

    Returns:
        Dict[str, Any]: The updated task object.
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
    """DELETE /tasks/:id - Deletes a task.

    Args:
        task_id (int): The ID of the task to delete.

    Returns:
        None if successful (HTTP 204), otherwise the `call` function will raise an exception.
    """
    return call(f"tasks/{task_id}", "DELETE")


# === Debts ===

def list_debts(
    contact_id: Optional[int] = None,
    page: int = 1,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    GET /debts or GET /contacts/:id/debts - Lists debts.

    Args:
        contact_id (Optional[int]): If provided, lists debts for only this contact.
        page (int): The page number.
        limit (int): The number of items per page.

    Returns:
        List[Dict[str, Any]]: A list of debt objects.
    """
    endpoint = f"contacts/{contact_id}/debts" if contact_id else "debts"
    return call(endpoint, params={"page": page, "limit": limit})


def get_debt(debt_id: int) -> Dict[str, Any]:
    """GET /debts/:id - Gets a specific debt.

    Args:
        debt_id (int): The ID of the debt.

    Returns:
        Dict[str, Any]: The full debt object.
    """
    return call(f"debts/{debt_id}")


def create_debt(
    contact_id: int,
    in_debt: Literal["yes", "no"],
    status: Literal["inprogress", "complete"],
    amount: int,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """POST /debts - Adds a new debt.

    Args:
        contact_id (int): The ID of the contact the debt is with.
        in_debt (Literal["yes", "no"]): "yes" if you owe the contact, "no" if the contact owes you.
        status (Literal["inprogress", "complete"]): The current status of the debt.
        amount (int): The amount of money, in your account's default currency.
        reason (Optional[str]): An optional description of the debt (max 10,000,000 chars).

    Returns:
        Dict[str, Any]: The newly created debt object.
    """
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
    """PUT /debts/:id - Updates a debt.

    Note: All parameters except `reason` are required by the API for updates.

    Args:
        debt_id (int): The ID of the debt to update.
        contact_id (int): The ID of the associated contact.
        in_debt (Literal["yes", "no"]): The new debt direction.
        status (Literal["inprogress", "complete"]): The new status.
        amount (int): The new amount.
        reason (Optional[str]): The new reason.

    Returns:
        Dict[str, Any]: The updated debt object.
    """
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
    """DELETE /debts/:id - Deletes a debt.

    Args:
        debt_id (int): The ID of the debt to delete.

    Returns:
        The raw response from the API call, likely `None` on success.
    """
    return call(f"debts/{debt_id}", "DELETE")


# === Tags ===


def list_tags(page: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
    """GET /tags - Lists all available tags in the account.

    Args:
        page (int): The page number.
        limit (int): The number of items per page.

    Returns:
        List[Dict[str, Any]]: A list of tag objects.
    """
    return call("tags", params={"page": page, "limit": limit})

def get_tag(tag_id: int) -> Dict[str, Any]:
    """GET /tags/:id - Gets a specific tag.

    Args:
        tag_id (int): The ID of the tag.

    Returns:
        Dict[str, Any]: The full tag object.
    """
    return call(f"tags/{tag_id}")

def create_tag(name: str) -> Dict[str, Any]:
    """POST /tags - Creates a new tag.

    Args:
        name (str): The name of the tag (max 255 chars).

    Returns:
        Dict[str, Any]: The newly created tag object.
    """
    return call("tags", "POST", {"name": name})

def update_tag(tag_id: int, name: str) -> Dict[str, Any]:
    """PUT /tags/:id - Updates a tag's name.

    Args:
        tag_id (int): The ID of the tag to update.
        name (str): The new name for the tag (max 255 chars).

    Returns:
        Dict[str, Any]: The updated tag object.
    """
    return call(f"tags/{tag_id}", "PUT", {"name": name})

def delete_tag(tag_id: int) -> Dict[str, Any]:
    """DELETE /tags/:id - Deletes a tag from the account.

    This will also remove the tag from all contacts it is associated with.

    Args:
        tag_id (int): The ID of the tag to delete.

    Returns:
        The raw response from the API, likely `None` on success.
    """
    return call(f"tags/{tag_id}", "DELETE")

def set_tags_for_contact(contact_id: int, tag_names: List[str]) -> Dict[str, Any]:
    """POST /contacts/:id/setTags - Associates a list of tags with a contact.

    This adds tags to the contact's existing tags. It does not remove any.
    If a tag in the list does not exist in the account, it will be created automatically.

    Args:
        contact_id (int): The ID of the contact.
        tag_names (List[str]): A list of tag names to associate with the contact.

    Returns:
        Dict[str, Any]: The updated contact object.
    """
    payload = {"tags": tag_names}
    return call(f"contacts/{contact_id}/setTags", "POST", payload)

def unset_tags_for_contact(contact_id: int, tag_ids: List[int]) -> Dict[str, Any]:
    """POST /contacts/:id/unsetTag - Removes one or more specific tags from a contact by their IDs.

    This only removes the association; the tag itself is not deleted from the account.

    Args:
        contact_id (int): The ID of the contact.
        tag_ids (List[int]): A list of tag IDs to remove from the contact.

    Returns:
        Dict[str, Any]: The updated contact object.
    """
    payload = {"tags": tag_ids}
    return call(f"contacts/{contact_id}/unsetTag", "POST", payload)

def unset_all_tags_for_contact(contact_id: int) -> Dict[str, Any]:
    """POST /contacts/:id/unsetTags - Removes all tags from a contact.

    This only removes the associations; the tags themselves are not deleted.

    Args:
        contact_id (int): The ID of the contact to clear tags from.

    Returns:
        Dict[str, Any]: The updated contact object.
    """
    return call(f"contacts/{contact_id}/unsetTags", "POST")

# === Journal & Days ===

def list_journal_entries(page: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
    """GET /journal - Lists all entries in your journal.

    Args:
        page (int): The page number.
        limit (int): The number of items per page.

    Returns:
        List[Dict[str, Any]]: A list of journal entry objects.
    """
    return call("journal", params={"page": page, "limit": limit})

def get_journal_entry(journal_id: int) -> Dict[str, Any]:
    """GET /journal/:id - Gets a specific journal entry.

    Args:
        journal_id (int): The ID of the journal entry.

    Returns:
        Dict[str, Any]: The full journal entry object.
    """
    return call(f"journal/{journal_id}")

def create_journal_entry(title: str, post: str) -> Dict[str, Any]:
    """POST /journal - Creates a journal entry.

    Args:
        title (str): The title of the entry.
        post (str): The body content of the entry.

    Returns:
        Dict[str, Any]: The newly created journal entry object.
    """
    payload = {"title": title, "post": post}
    return call("journal", "POST", payload)

def update_journal_entry(journal_id: int, title: str, post: str) -> Dict[str, Any]:
    """PUT /journal/:id - Updates a journal entry.

    Args:
        journal_id (int): The ID of the entry to update.
        title (str): The new title.
        post (str): The new body content.

    Returns:
        Dict[str, Any]: The updated journal entry object.
    """
    payload = {"title": title, "post": post}
    return call(f"journal/{journal_id}", "PUT", payload)

def delete_journal_entry(journal_id: int) -> Dict[str, Any]:
    """
    DELETE /journal/:id - Deletes a journal entry.
    
    Note: The official documentation contains a typo for this endpoint (listing /calls/:id).
    This function uses the correct /journal/:id endpoint.

    Args:
        journal_id (int): The ID of the journal entry to delete.

    Returns:
        The raw response from the API, likely `None` on success.
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

    Args:
        contact_id (Optional[int]): If provided, lists gifts for only this contact.
        page (int): The page number.
        limit (int): The number of items per page.

    Returns:
        List[Dict[str, Any]]: A list of gift objects.
    """
    endpoint = f"contacts/{contact_id}/gifts" if contact_id else "gifts"
    return call(endpoint, params={"page": page, "limit": limit})


def get_gift(gift_id: int) -> Dict[str, Any]:
    """GET /gifts/:id - Gets a specific gift.

    Args:
        gift_id (int): The ID of the gift.

    Returns:
        Dict[str, Any]: The full gift object.
    """
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
    """POST /gifts - Records a new gift for a contact.

    Args:
        contact_id (int): The ID of the contact the gift is associated with.
        name (str): The name of the gift (max 255 chars).
        status (Literal["idea", "offered", "received"]): The status of the gift.
        recipient_id (Optional[int]): The ID of the actual recipient if it's a partner
                                      or child of the main contact.
        comment (Optional[str]): Notes about the gift (max 1,000,000 chars).
        url (Optional[str]): A URL related to the gift (e.g., a store page).
        amount (Optional[Union[int, float]]): The cost of the gift.
        date (Optional[str]): The date the gift was offered, in "YYYY-MM-DD" format.

    Returns:
        Dict[str, Any]: The newly created gift object.
    """
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
    """PUT /gifts/:id - Updates a gift.

    Note: The API requires `contact_id`, `name`, and `status` for all updates.

    Args:
        gift_id (int): The ID of the gift to update.
        contact_id (int): The ID of the associated contact.
        name (str): The new name for the gift.
        status (Literal["idea", "offered", "received"]): The new status.
        recipient_id (Optional[int]): The new recipient ID.
        comment (Optional[str]): The new comment.
        url (Optional[str]): The new URL.
        amount (Optional[Union[int, float]]): The new amount.
        date (Optional[str]): The new date ("YYYY-MM-DD").

    Returns:
        Dict[str, Any]: The updated gift object.
    """
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
    """DELETE /gifts/:id - Deletes a gift.

    Args:
        gift_id (int): The ID of the gift to delete.

    Returns:
        The raw response from the API, likely `None` on success.
    """
    return call(f"gifts/{gift_id}", "DELETE")

# === Calls ===

def list_calls(
    contact_id: Optional[int] = None,
    page: int = 1,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """GET /calls or GET /contacts/:id/calls - Lists all calls or calls for a specific contact.

    Args:
        contact_id (Optional[int]): If provided, lists calls for only this contact.
        page (int): The page number.
        limit (int): The number of items per page.

    Returns:
        List[Dict[str, Any]]: A list of call log objects.
    """
    endpoint = f"contacts/{contact_id}/calls" if contact_id else "calls"
    return call(endpoint, params={"page": page, "limit": limit})


def get_call(call_id: int) -> Dict[str, Any]:
    """GET /calls/:id - Gets a specific call.

    Args:
        call_id (int): The ID of the call log.

    Returns:
        Dict[str, Any]: The full call log object.
    """
    return call(f"calls/{call_id}")


def create_call(contact_id: int, called_at: str, content: str) -> Dict[str, Any]:
    """POST /calls - Logs a call with a contact.

    Args:
        contact_id (int): The ID of the contact who was called.
        called_at (str): The date of the call in "YYYY-MM-DD" format.
        content (str): A description of the call (max 100,000 chars).

    Returns:
        Dict[str, Any]: The newly created call log object.
    """
    payload = {
        "contact_id": contact_id,
        "called_at": called_at,
        "content": content,
    }
    return call("calls", "POST", payload)


def update_call(call_id: int, contact_id: int, called_at: str, content: str) -> Dict[str, Any]:
    """PUT /calls/:id - Updates a call.

    Note: The API requires all parameters for updates.

    Args:
        call_id (int): The ID of the call log to update.
        contact_id (int): The ID of the associated contact.
        called_at (str): The new date of the call in "YYYY-MM-DD" format.
        content (str): The new content for the call log.

    Returns:
        Dict[str, Any]: The updated call log object.
    """
    payload = {
        "contact_id": contact_id,
        "called_at": called_at,
        "content": content,
    }
    return call(f"calls/{call_id}", "PUT", payload)


def delete_call(call_id: int) -> Dict[str, Any]:
    """DELETE /calls/:id - Deletes a call.

    Args:
        call_id (int): The ID of the call log to delete.

    Returns:
        The raw response from the API, likely `None` on success.
    """
    return call(f"calls/{call_id}", "DELETE")

# === Conversations & Messages ===

def list_conversations(
    contact_id: Optional[int] = None,
    page: int = 1,
    limit: int = 15
) -> List[Dict[str, Any]]:
    """GET /conversations or GET /contacts/:id/conversations - Lists all conversations or those for a contact.

    Args:
        contact_id (Optional[int]): If provided, lists conversations for only this contact.
        page (int): The page number.
        limit (int): The number of items per page.

    Returns:
        List[Dict[str, Any]]: A list of conversation objects, including their messages.
    """
    endpoint = f"contacts/{contact_id}/conversations" if contact_id else "conversations"
    return call(endpoint, params={"page": page, "limit": limit})


def get_conversation(conversation_id: int) -> Dict[str, Any]:
    """GET /conversations/:id - Gets a specific conversation, including its messages.

    Args:
        conversation_id (int): The ID of the conversation.

    Returns:
        Dict[str, Any]: The full conversation object with all messages.
    """
    return call(f"conversations/{conversation_id}")


def create_conversation(
    contact_id: int,
    happened_at: str,
    contact_field_type_id: int
) -> Dict[str, Any]:
    """POST /conversations - Creates a new conversation container.

    This creates an empty conversation. Use `add_message_to_conversation` to add content.

    Args:
        contact_id (int): The ID of the contact.
        happened_at (str): The date of the conversation in "YYYY-MM-DD" format.
        contact_field_type_id (int): The ID of the medium (e.g., 'Email', 'Twitter').
                                     Get this from `list_contact_field_types()`.

    Returns:
        Dict[str, Any]: The newly created conversation object.
    """
    payload = {
        "contact_id": contact_id,
        "happened_at": happened_at,
        "contact_field_type_id": contact_field_type_id,
    }
    return call("conversations", "POST", payload)


def update_conversation(conversation_id: int, contact_id: int, contact_field_type_id: int, happened_at: Optional[str] = None) -> Dict[str, Any]:
    """PUT /conversations/:id - Updates a conversation.

    Note: The `contact_field_type_id` is required for updates by the API.

    Args:
        conversation_id (int): The ID of the conversation to update.
        contact_id (int): The ID of the associated contact.
        contact_field_type_id (int): The new medium for the conversation.
        happened_at (Optional[str]): The new date in "YYYY-MM-DD" format.

    Returns:
        Dict[str, Any]: The updated conversation object.
    """
    payload = {
        "contact_id": contact_id,
        "contact_field_type_id": contact_field_type_id
    }
    if happened_at is not None:
        payload["happened_at"] = happened_at
    return call(f"conversations/{conversation_id}", "PUT", payload)


def delete_conversation(conversation_id: int) -> Dict[str, Any]:
    """DELETE /conversations/:id - Deletes a conversation and all its messages.

    Args:
        conversation_id (int): The ID of the conversation to delete.

    Returns:
        The raw API response, likely `None` on success.
    """
    return call(f"conversations/{conversation_id}", "DELETE")


# --- Message Management ---

def add_message_to_conversation(
    conversation_id: int,
    contact_id: int,
    written_at: str,
    written_by_me: bool,
    content: str
) -> Dict[str, Any]:
    """POST /conversations/:id/messages - Adds a message to a conversation.

    Args:
        conversation_id (int): The ID of the conversation to add the message to.
        contact_id (int): The ID of the contact this conversation is with.
        written_at (str): The date the message was written in "YYYY-MM-DD" format.
        written_by_me (bool): True if you wrote the message, False if the contact wrote it.
        content (str): The text content of the message.

    Returns:
        Dict[str, Any]: The updated conversation object containing the new message.
    """
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
    """PUT /conversations/:id/messages/:id - Updates a message in a conversation.

    Note: The API requires all parameters for updates.

    Args:
        conversation_id (int): The ID of the conversation.
        message_id (int): The ID of the message to update.
        contact_id (int): The ID of the associated contact.
        written_at (str): The new date in "YYYY-MM-DD" format.
        written_by_me (bool): The new direction of the message.
        content (str): The new message content.

    Returns:
        Dict[str, Any]: The updated conversation object.
    """
    payload = {
        "contact_id": contact_id,
        "written_at": written_at,
        "written_by_me": written_by_me,
        "content": content,
    }
    return call(f"conversations/{conversation_id}/messages/{message_id}", "PUT", payload)


def delete_message(conversation_id: int, message_id: int) -> Dict[str, Any]:
    """DELETE /conversations/:id/messages/:id - Deletes a message from a conversation.

    Args:
        conversation_id (int): The ID of the conversation.
        message_id (int): The ID of the message to delete.

    Returns:
        The raw API response, likely `None` on success.
    """
    return call(f"conversations/{conversation_id}/messages/{message_id}", "DELETE")

# === Companies ===

def list_companies() -> List[Dict[str, Any]]:
    """GET /companies - Lists all companies.

    Returns:
        List[Dict[str, Any]]: A list of company objects.
    """
    return call("companies")

def get_company(company_id: int) -> Dict[str, Any]:
    """GET /companies/:id - Gets a specific company.

    Args:
        company_id (int): The ID of the company.

    Returns:
        Dict[str, Any]: The full company object.
    """
    return call(f"companies/{company_id}")

def create_company(name: str, **kwargs: Any) -> Dict[str, Any]:
    """POST /companies - Creates a new company in Monica.

    This function takes the company's name as a required argument and
    allows for any other supported API fields to be passed as keyword
    arguments.

    Args:
        name (str): The name of the company (max 255 chars). This is required.
        **kwargs: Arbitrary keyword arguments that are passed directly
            to the API. Supported optional parameters include:
            - website (str): The company's website address (max 255 chars).
            - number_of_employees (int): The number of employees.
            - type (str): The type of company (e.g., "Corporation").
            - industry (str): The industry the company is in.
            - street (str): The street address.
            - city (str): The city name.
            - province (str): The state or province name.
            - postal_code (str): The ZIP or postal code.
            - country (str): The 2-letter uppercase ISO code for the country (e.g., 'US').

    Returns:
        Dict[str, Any]: A dictionary representing the newly created company
                        as returned by the API.

    Example:
        create_company(
            name="Innovate Corp",
            website="https://innovatecorp.com",
            industry="Technology",
            city="San Francisco"
        )
    """
    payload = {"name": name}
    payload.update(kwargs)
    return call("companies", "POST", payload)

def delete_company(company_id: int) -> Dict[str, Any]:
    """DELETE /companies/:id - Deletes a company.

    Warning: The documentation does not specify what happens to contacts
    associated with this company. Their work information may be affected.

    Args:
        company_id (int): The ID of the company to delete.

    Returns:
        A confirmation dictionary `{"deleted": True, "id": company_id}`.
    """
    call(f"companies/{company_id}", "DELETE")
    return {"deleted": True, "id": company_id}


# === Example Usage ===
if __name__ == "__main__":
    print("--- Monica API Caller Full Demo ---")
    created_contact_id = None
    try:
        # user = get_user()
        # print(f"Authenticated as: {user.get('first_name')} ({user.get('email')})")
        # print("\n[1] Creating contact...")
        # contact = create_contact("Sam", last_name="Jones")
        # created_contact_id = contact["id"]
        # print(f"  -> Created: {contact['first_name']} {contact['last_name']} (ID: {created_contact_id})")

        # print("\n[2] Creating a note for the contact...")
        # updated_contact_note = create_note(created_contact_id, body="This is a note about Sam.")
        # print(f"  -> Created note with ID: {updated_contact_note['id']} and body: '{updated_contact_note['body']}'")
        genders = list_genders()
        for g in genders:
            print("\n[3] Listing genders...", g['name'])

    except Exception as e:
        print(f"\nAN ERROR OCCURRED: {e}")
    finally:
        if created_contact_id:
            print("\n--- Cleaning up created resources ---")
            d = input(f"Are you sure you want to delete contact {created_contact_id}? (y/n): ").strip().lower()
            if d == 'y':
                delete_contact(created_contact_id)
                print(f"  -> Deleting contact {created_contact_id}...")
                print("--- Cleanup complete ---")
            else:
                print("  -> Cleanup skipped.")