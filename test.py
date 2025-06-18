import os
from datetime import datetime, timedelta
from temp import (
    # Account & Lookup
    get_user, list_genders, list_currencies, list_countries, list_activity_types,
    list_contact_field_types, list_relationship_types,

    # Contacts
    create_contact, get_contact, list_contacts, update_contact, delete_contact,
    set_contact_occupation,

    # Contact Sub-Resources
    add_address, update_address, delete_address,
    set_contact_field_value,
    # upload_document_for_contact, upload_photo_for_contact, # Need files for these

    # Relationships
    create_relationship, delete_relationship,

    # Activities
    list_all_activities, list_activities_for_contact, create_activity,
    update_activity, delete_activity,

    # Notes
    create_note, update_note, delete_note,

    # Reminders
    create_reminder, update_reminder, delete_reminder,

    # Tasks
    list_tasks, create_task, update_task, delete_task,

    # Debts
    list_debts_for_contact, create_debt, delete_debt,

    # Tags
    list_tags, attach_tag, detach_tag,

    # Journal & Days
    create_journal_entry, set_day_emotion,

    # Other
    list_gifts_for_contact, create_gift, delete_gift,
    create_call,
    create_conversation,
    list_companies, get_company, create_company, delete_company,
)

def main():
    """Runs a sequence of tests for the Monica API wrapper."""
    print("--- Starting Monica API Test Suite ---")
    created_ids = {
        "contact1": None,
        "contact2": None,
        "address": None,
        "pet": None,
        "relationship": None,
        "activity": None,
        "note": None,
        "reminder": None,
        "task": None,
        "debt": None,
        "gift": None,
        "company": None,
    }

    try:
        # # === Account & Lookup Data ===
        # print("\n--- Testing Account & Lookup ---")
        # user = get_user()
        # print(f"Authenticated as: {user.get('first_name')} {user.get('last_name')}")
        # assert user is not None

        # print("Genders:", len(list_genders()))
        # print("Currencies:", len(list_currencies()))
        # print("Countries:", len(list_countries()))
        # print("Activity Types:", len(list_activity_types()))
        contact_field_types = list_contact_field_types()
        print("Contact Field Types:", len(contact_field_types))
        relationship_types = list_relationship_types()
        print("Relationship Types:", len(relationship_types))
        tags = list_tags()
        print("Tags:", len(tags))


        # === Contacts ===
        print("\n--- Testing Contacts ---")
        contact1 = create_contact(first_name="Test", last_name="Contact1")
        created_ids["contact1"] = contact1["id"]
        print(f"Created Contact 1: ID {created_ids['contact1']}")
        assert get_contact(created_ids["contact1"])["first_name"] == "Test"

        contact2 = create_contact(first_name="Test", last_name="Contact2")
        created_ids["contact2"] = contact2["id"]
        print(f"Created Contact 2: ID {created_ids['contact2']}")

        # print("Listing contacts:", len(list_contacts(query="Test Contact")))

        # update_contact(created_ids["contact1"], {"nickname": "Tester"})
        # print(f"Updated Contact 1 with nickname.")
        # assert get_contact(created_ids["contact1"])["nickname"] == "Tester"

        # set_contact_occupation(created_ids["contact1"], job_title="API Tester", company_name="Test Corp")
        # print("Set occupation for Contact 1.")


        # # === Contact Sub-Resources ===
        # print("\n--- Testing Contact Sub-Resources ---")
        # address = add_address(created_ids["contact1"], name="Work", street="123 Test St", city="Testville")
        # created_ids["address"] = address["id"]
        # print(f"Added address {created_ids['address']} to Contact 1")
        # update_address(created_ids["address"], created_ids["contact1"], city="New Testville")
        # print("Updated address.")


        # if contact_field_types:
        #     field_type_id = contact_field_types[0]['id']
        #     set_contact_field_value(created_ids["contact1"], field_type_id, "Test Value")
        #     print(f"Set contact field value for type {field_type_id}.")


        # === Relationships ===
        if relationship_types:
            print("\n--- Testing Relationships ---")
            rel_type_id = relationship_types[0]['id']
            relationship = create_relationship(created_ids["contact1"], rel_type_id, created_ids["contact2"])
            created_ids["relationship"] = relationship['id']
            print(f"Set relationship between contacts.")


        # === Activities ===
        print("\n--- Testing Activities ---")
        two_list = [created_ids["contact1"], created_ids["contact2"]]
        activity = create_activity(two_list, summary="Tested the API")
        created_ids["activity"] = activity["id"]
        print(f"Created activity {created_ids['activity']}.")
        update_activity(created_ids["activity"], summary="Thoroughly tested the API")
        print("Updated activity.")
        print("All activities:", len(list_all_activities()))
        print("Contact 1 activities:", len(list_activities_for_contact(created_ids["contact1"])))


        # === Notes ===
        print("\n--- Testing Notes ---")
        note = create_note(created_ids["contact1"], "This is a test note.")
        created_ids["note"] = note["id"]
        print(f"Created note {created_ids['note']}.")
        update_note(created_ids["note"], body="This is an updated test note.", is_favorite=True)
        print("Updated note.")


        # === Reminders ===
        print("\n--- Testing Reminders ---")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        reminder = create_reminder(created_ids["contact1"], "Follow up", tomorrow)
        created_ids["reminder"] = reminder["id"]
        print(f"Created reminder {created_ids['reminder']}.")
        update_reminder(created_ids["reminder"], title="Follow up urgently")
        print("Updated reminder.")


        # === Tasks ===
        print("\n--- Testing Tasks ---")
        task = create_task("Test the task system", contact_id=created_ids["contact1"])
        created_ids["task"] = task["id"]
        print(f"Created task {created_ids['task']}.")
        update_task(created_ids["task"], completed=True)
        print("Updated task.")
        print("All tasks:", len(list_tasks()))


        # === Debts ===
        print("\n--- Testing Debts ---")
        debt = create_debt(created_ids["contact1"], "me", 100.00, "USD", "For testing")
        created_ids["debt"] = debt["id"]
        print(f"Created debt {created_ids['debt']}.")
        print("Contact 1 debts:", len(list_debts_for_contact(created_ids["contact1"])))


        # === Tags ===
        if tags:
            print("\n--- Testing Tags ---")
            tag_id = tags[0]['id']
            attach_tag(created_ids["contact1"], tag_id)
            print(f"Attached tag {tag_id} to Contact 1.")
            detach_tag(created_ids["contact1"], tag_id)
            print(f"Detached tag {tag_id}.")


        # === Journal & Days ===
        print("\n--- Testing Journal & Days ---")
        today = datetime.now().strftime('%Y-%m-%d')
        create_journal_entry("Today I tested the Monica API.", date=today)
        print("Created journal entry.")
        set_day_emotion("happy", date=today)
        print("Set today's emotion.")


        # === Other Resources ===
        print("\n--- Testing Other Resources ---")
        company = create_company("Test Company Inc.")
        created_ids["company"] = company["id"]
        print(f"Created company {created_ids['company']}.")
        assert get_company(created_ids["company"]) is not None
        print("All companies:", len(list_companies()))

        gift = create_gift(created_ids["contact1"], "Test Gift")
        created_ids["gift"] = gift["id"]
        print(f"Created gift {created_ids['gift']}.")
        print("Contact 1 gifts:", len(list_gifts_for_contact(created_ids["contact1"])))

        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        create_call(created_ids["contact1"], called_at=now_str)
        print("Created a call log.")

        if contact_field_types:
            conv_field_type_id = contact_field_types[0]['id']
            create_conversation(created_ids["contact1"], happened_at=now_str, contact_field_type_id=conv_field_type_id)
            print("Created a conversation log.")


    except Exception as e:
        print(f"\nAN ERROR OCCURRED: {e}")
    finally:
        # === Cleanup ===
        print("\n--- Cleaning up created resources ---")
        if created_ids["gift"]:
            delete_gift(created_ids["gift"])
            print(f"Deleted gift {created_ids['gift']}")
        if created_ids["company"]:
            delete_company(created_ids["company"])
            print(f"Deleted company {created_ids['company']}")
        if created_ids["debt"]:
            delete_debt(created_ids["debt"])
            print(f"Deleted debt {created_ids['debt']}")
        if created_ids["task"]:
            delete_task(created_ids["task"])
            print(f"Deleted task {created_ids['task']}")
        if created_ids["reminder"]:
            delete_reminder(created_ids["reminder"])
            print(f"Deleted reminder {created_ids['reminder']}")
        if created_ids["note"]:
            delete_note(created_ids["note"])
            print(f"Deleted note {created_ids['note']}")
        if created_ids["activity"]:
            delete_activity(created_ids["activity"])
            print(f"Deleted activity {created_ids['activity']}")
        if created_ids["relationship"]:
            delete_relationship(created_ids["relationship"])
            print(f"Deleted relationship {created_ids['relationship']}")
        if created_ids["address"]:
            delete_address(created_ids["address"])
            print(f"Deleted address {created_ids['address']}")
        if created_ids["contact1"]:
            delete_contact(created_ids["contact1"])
            print(f"Deleted contact {created_ids['contact1']}")
        if created_ids["contact2"]:
            delete_contact(created_ids["contact2"])
            print(f"Deleted contact {created_ids['contact2']}")

        print("--- Test Suite Finished ---")


if __name__ == "__main__":
    main()