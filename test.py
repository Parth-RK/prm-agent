import os
from datetime import datetime, timedelta
from temp import *

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
        "call": None,
    }

    try:
        # === Account & Lookup Data ===
        print("\n--- Testing Account & Lookup ---")
        user = get_user()
        print(f"Authenticated as: {user.get('first_name')} {user.get('last_name')}")
        assert user is not None

        print("Genders:", len(list_genders()))
        print("Currencies:", len(list_currencies()))
        print("Countries:", len(list_countries()))
        print("Activity Types:", len(list_activity_types()))
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

        print("Listing contacts:", len(list_contacts(query="Test Contact")))

        update_contact(created_ids["contact1"], {"nickname": "Tester"})
        print(f"Updated Contact 1 with nickname.")
        assert get_contact(created_ids["contact1"])["nickname"] == "Tester"

        set_contact_occupation(created_ids["contact1"], job_title="API Tester", company_name="Test Corp")
        print("Set occupation for Contact 1.")


        # === Contact Sub-Resources ===
        print("\n--- Testing Contact Sub-Resources ---")
        address = add_address(created_ids["contact1"], name="Work", street="123 Test St", city="Testville")
        created_ids["address"] = address["id"]
        print(f"Added address {created_ids['address']} to Contact 1")
        update_address(created_ids["address"], created_ids["contact1"], city="New Testville")
        print("Updated address.")


        if contact_field_types:
            field_type_id = contact_field_types[0]['id']
            set_contact_field_value(created_ids["contact1"], field_type_id, "Test Value")
            print(f"Set contact field value for type {field_type_id}.")


        # === Relationships ===
        if relationship_types:
            print("\n--- Testing Relationships ---")
            rel_type_id = relationship_types[0]['id']
            relationship = create_relationship(created_ids["contact1"], rel_type_id, created_ids["contact2"])
            created_ids["relationship"] = relationship['id']
            print(f"Set relationship between contacts.")


        # # === Activities ===
        # # print("\n--- Testing Activities ---")
        # # two_list = [created_ids["contact1"], created_ids["contact2"]]
        # # activity = create_activity(two_list, summary="Tested the API", activity_type_id=1)
        # # created_ids["activity"] = activity["id"]
        # # print(f"Created activity {created_ids['activity']}.")
        # # update_activity(created_ids["activity"], summary="Thoroughly tested the API")
        # # print("Updated activity.")
        # # print("All activities:", len(list_all_activities()))
        # # print("Contact 1 activities:", len(list_activities_for_contact(created_ids["contact1"])))


        # === Notes ===
        print("\n--- Testing Notes ---")
        note = create_note(created_ids["contact1"], "This is a test note.")
        created_ids["note"] = note["id"]
        print(f"Created note {created_ids['note']}.")
        update_note(created_ids["note"], body="This is an updated test note.", is_favorited=True)
        print("Updated note.")


        # === Reminders ===
        print("\n--- Testing Reminders ---")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        reminder = create_reminder(
            contact_id=created_ids["contact1"], 
            title="Follow up", 
            next_expected_date=tomorrow, 
            frequency_type="one_time",
            frequency_number=1,
            description="This is a test reminder"
        )
        created_ids["reminder"] = reminder["id"]
        print(f"Created reminder {created_ids['reminder']}.")
        tomorrow = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        update_reminder(
            reminder_id=created_ids["reminder"], 
            contact_id=created_ids["contact1"],
            title="Follow up urgently",
            next_expected_date=tomorrow, 
            frequency_type="year",
            frequency_number=1,
            description="This is an updated test reminder"
        )
        print("Updated reminder.")


        # === Tasks ===
        print("\n--- Testing Tasks ---")
        task = create_task("Test the task system", contact_id=created_ids["contact1"])
        created_ids["task"] = task["id"]
        print(f"Created task {created_ids['task']}.")
        update_task(created_ids["task"], contact_id=created_ids["contact1"], completed=True)
        print("Updated task.")
        print("All tasks:", len(list_tasks()))


        # === Debts ===
        print("\n--- Testing Debts ---")
        debt = create_debt(
            contact_id=created_ids["contact1"],
            in_debt="yes",  # "yes" means you owe the contact, "no" means the contact owes you
            status="inprogress",  # either "inprogress" or "complete"
            amount=100,
            reason="For testing"
        )
        created_ids["debt"] = debt["id"]
        print(f"Created debt {created_ids['debt']}.")
        print("Contact 1 debts:", len(list_debts(contact_id=created_ids["contact1"])))        # === Tags ===
        print("\n--- Testing Tags ---")
        # Create a new tag
        tag_name = f"TestTag-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        new_tag = create_tag(tag_name)
        print(f"Created new tag: {new_tag['name']} with ID {new_tag['id']}")
        
        # Get the tag
        retrieved_tag = get_tag(new_tag['id'])
        print(f"Retrieved tag: {retrieved_tag['name']}")
        assert retrieved_tag['name'] == tag_name
        
        # Update the tag name
        updated_tag_name = f"{tag_name}-updated"
        updated_tag = update_tag(new_tag['id'], updated_tag_name)
        print(f"Updated tag name to: {updated_tag['name']}")
        assert updated_tag['name'] == updated_tag_name
        
        # Set tags for contact
        response = set_tags_for_contact(created_ids["contact1"], [updated_tag_name])
        print(f"Set tag {updated_tag_name} for Contact 1")
        
        # Unset specific tag from contact
        response = unset_tags_for_contact(created_ids["contact1"], [new_tag['id']])
        print(f"Unset tag {new_tag['id']} from Contact 1")
        
        # Set tags again and then unset all
        set_tags_for_contact(created_ids["contact1"], [updated_tag_name])
        response = unset_all_tags_for_contact(created_ids["contact1"])
        print("Unset all tags from Contact 1")
        
        # Delete the tag 
        response = delete_tag(new_tag['id'])
        print(f"Deleted tag {new_tag['id']}")


        # === Journal & Days ===
        print("\n--- Testing Journal & Days ---")
        
        # Create a journal entry
        title = "Journal Test"
        post = "Today I tested the Monica API."
        journal_entry = create_journal_entry(title, post)
        journal_id = journal_entry["id"]
        print(f"Created journal entry with ID {journal_id}")
        
        # Get the journal entry
        retrieved_entry = get_journal_entry(journal_id)
        print(f"Retrieved journal entry: {retrieved_entry['title']}")
        assert retrieved_entry["title"] == title
        
        # Update the journal entry
        updated_title = "Updated Journal Test"
        updated_post = "I thoroughly tested the Monica API."
        updated_entry = update_journal_entry(journal_id, updated_title, updated_post)
        print(f"Updated journal entry to: {updated_entry['title']}")
        assert updated_entry["title"] == updated_title
        
        # List journal entries
        entries = list_journal_entries()
        print(f"Journal entries: {len(entries)}")
        
        # Delete the journal entry (usually would be in cleanup section, but showing here for completeness)
        delete_journal_entry(journal_id)
        print(f"Deleted journal entry {journal_id}")        
        # === Gifts ===
        print("\n--- Testing Gifts ---")
        gift = create_gift(
            contact_id=created_ids["contact1"], 
            name="Test Gift", 
            status="idea",
            comment="A test gift idea"
        )
        created_ids["gift"] = gift["id"]
        print(f"Created gift {created_ids['gift']}.")
        
        # Get gift details
        gift_details = get_gift(created_ids["gift"])
        print(f"Retrieved gift: {gift_details['name']}")
        assert gift_details["name"] == "Test Gift"
        
        # Update the gift
        updated_gift = update_gift(
            gift_id=created_ids["gift"],
            contact_id=created_ids["contact1"],
            name="Updated Gift Name",
            status="offered",
            comment="This gift was offered"
        )
        print(f"Updated gift to: {updated_gift['name']}")
        assert updated_gift["name"] == "Updated Gift Name"
        
        # List gifts
        gifts = list_gifts(contact_id=created_ids["contact1"])
        print(f"Contact 1 gifts: {len(gifts)}")
        
        # === Calls ===
        print("\n--- Testing Calls ---")
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        call = create_call(
            contact_id=created_ids["contact1"], 
            called_at=now_str,
            content="Discussed testing the API"
        )
        created_ids["call"] = call["id"]
        print(f"Created call log {created_ids['call']}.")
        
        # Get call details
        call_details = get_call(created_ids["call"])
        print(f"Retrieved call with content: {call_details['content']}")
        
        # Update the call
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        updated_call = update_call(
            call_id=created_ids["call"],
            contact_id=created_ids["contact1"],
            called_at=tomorrow,
            content="Updated call notes"
        )
        print(f"Updated call with new content: {updated_call['content']}")
        
        # List calls
        calls = list_calls(contact_id=created_ids["contact1"])
        print(f"Contact 1 calls: {len(calls)}")
        
        # === Companies ===
        print("\n--- Testing Companies ---")
        company = create_company("Test Company Inc.")
        created_ids["company"] = company["id"]
        print(f"Created company {created_ids['company']}.")
        assert get_company(created_ids["company"]) is not None
        print("All companies:", len(list_companies()))        
        
        # === Conversations ===
        print("\n--- Testing Conversations ---")
        if contact_field_types:
            conv_field_type_id = contact_field_types[0]['id']
            
            # Create the conversation
            # The response is the unwrapped conversation object
            conversation_response = create_conversation(
                contact_id=created_ids["contact1"], 
                happened_at=now_str, 
                contact_field_type_id=conv_field_type_id
            )
            created_ids["conversation"] = conversation_response['id']
            print(f"Created conversation {created_ids['conversation']}.")
            
            # Get conversation details
            # The response is the unwrapped conversation object
            conversation_details = get_conversation(created_ids["conversation"])
            print(f"Retrieved conversation from: {conversation_details['happened_at']}")

            # Update the conversation
            # The update endpoint only takes 'happened_at'
            update_conversation(
                conversation_id=created_ids["conversation"],
                contact_id=created_ids["contact1"],
                contact_field_type_id=conv_field_type_id,
                happened_at=tomorrow
            )
            print("Updated conversation successfully")
            
            # Add a message to the conversation
            # The response is the unwrapped conversation object, containing the messages list
            add_message_response = add_message_to_conversation(
                conversation_id=created_ids["conversation"],
                contact_id=created_ids["contact1"],
                written_at=now_str,
                written_by_me=True,
                content="Hello, this is a test message"
            )
            # CORRECT WAY: Get the 'messages' list, get the last item [-1], then its 'id'.
            created_ids["message"] = add_message_response['messages'][-1]['id']
            print(f"Added message {created_ids['message']} to conversation.")
            
            # Update the message
            # The response is the unwrapped conversation object
            updated_message_response = update_message_in_conversation(
                conversation_id=created_ids["conversation"],
                message_id=created_ids["message"],
                contact_id=created_ids["contact1"],
                written_at=now_str,
                written_by_me=True,
                content="Updated test message"
            )
            # CORRECT: Parse the response to verify the update.
            updated_content = updated_message_response['messages'][-1]['content']
            print(f"Updated message to: '{updated_content}'")
            
            # Delete the message
            delete_message(created_ids["conversation"], created_ids["message"])
            print(f"Deleted message {created_ids['message']}")
            
            # List conversations
            # The response is the unwrapped LIST of conversation objects
            conversations_list = list_conversations(contact_id=created_ids["contact1"])
            print(f"Contact 1 conversations: {len(conversations_list)}")
    except Exception as e:
        print(f"\nAN ERROR OCCURRED: {e}")
    finally:
        # === Cleanup ===
        print("\n--- Cleaning up created resources ---")
        if created_ids.get("conversation"):
            delete_conversation(created_ids["conversation"])
            print(f"Deleted conversation {created_ids['conversation']}")
        if created_ids.get("call"):
            delete_call(created_ids["call"])
            print(f"Deleted call {created_ids['call']}")
        if created_ids.get("gift"):
            delete_gift(created_ids["gift"])
            print(f"Deleted gift {created_ids['gift']}")
        if created_ids.get("company"):
            delete_company(created_ids["company"])
            print(f"Deleted company {created_ids['company']}")
        if created_ids.get("debt"):
            delete_debt(created_ids["debt"])
            print(f"Deleted debt {created_ids['debt']}")
        if created_ids.get("task"):
            delete_task(created_ids["task"])
            print(f"Deleted task {created_ids['task']}")
        if created_ids.get("reminder"):
            delete_reminder(created_ids["reminder"])
            print(f"Deleted note {created_ids['reminder']}")
        if created_ids.get("note"):
            delete_note(created_ids["note"])
            print(f"Deleted note {created_ids['note']}")
        # if created_ids["activity"]:
        #     delete_activity(created_ids["activity"])
        #     print(f"Deleted activity {created_ids['activity']}")
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