# monica_data_agent.py
import os
import json
import google.generativeai as genai
import monica_api_caller as alf

class MonicaDataAgent:
    """
    A stateless, non-conversational Executor Agent.
    Its sole purpose is to receive a natural language task, convert it into a
    function call to the Monica Agent-Level Functions (ALF), execute it, and
    return the raw JSON result. It uses Gemini's native function-calling.
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Gemini API key is required.")

        genai.configure(api_key=api_key)
        
        # --- Define the toolset from our agent-level functions library ---
        self.tools = [
            alf.remember_person,
            alf.find_people,
            alf.get_details_about_person,
            alf.forget_person,
            alf.remember_something_about,
            alf.get_memories_about,
            alf.log_call_with,
            alf.set_relationship,
            alf.create_task_for,
            alf.mark_task_as_complete,
            alf.set_reminder_for,
            alf.log_job_for_person,
            alf.tag_person,            
            alf.get_user,
            alf.list_genders,
            alf.list_currencies,
            alf.list_countries,
            alf.list_activity_types,
            alf.list_contact_field_types,
            alf.list_relationship_types,
            alf.get_contact_by_name,
            alf.get_contact_summary,
            alf.list_contacts,
            alf.get_contact,
            alf.create_contact,
            alf.update_contact,
            alf.delete_contact,
            alf.set_contact_occupation,
            alf.add_address,
            alf.update_address,
            alf.delete_address,
            alf.set_contact_field_value,
            alf.upload_document_for_contact,
            alf.upload_photo_for_contact,
            alf.create_relationship,
            alf.update_relationship,
            alf.delete_relationship,
            alf.list_all_notes,
            alf.list_contact_notes,
            alf.get_note,
            alf.create_note,
            alf.update_note,
            alf.delete_note,
            alf.create_reminder,
            alf.update_reminder,
            alf.delete_reminder,
            alf.get_task,
            alf.list_tasks,
            alf.create_task,
            alf.update_task,
            alf.delete_task,
            alf.list_debts,
            alf.get_debt,
            alf.create_debt,
            alf.update_debt,
            alf.delete_debt,
            alf.list_tags,
            alf.get_tag,
            alf.create_tag,
            alf.update_tag,
            alf.delete_tag,
            alf.set_tags_for_contact,
            alf.unset_tags_for_contact,
            alf.unset_all_tags_for_contact,
            alf.list_journal_entries,
            alf.get_journal_entry,
            alf.create_journal_entry,
            alf.update_journal_entry,
            alf.delete_journal_entry,
            alf.list_gifts,
            alf.get_gift,
            alf.create_gift,
            alf.update_gift,
            alf.delete_gift,
            alf.list_calls,
            alf.get_call,
            alf.create_call,
            alf.update_call,
            alf.delete_call,
            alf.list_conversations,
            alf.get_conversation,
            alf.create_conversation,
            alf.update_conversation,
            alf.delete_conversation,
            alf.add_message_to_conversation,
            alf.update_message_in_conversation,
            alf.delete_message,
            alf.list_companies,
            alf.get_company,
            alf.create_company,
            alf.delete_company,
        ]

        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction="""You are a data execution engine. Your only job is to execute functions based on the user's request.
            - You must use the provided tools to fulfill the request. Use alf tools for Monica Agent-Level Functions (ALF).
            - If the user's request is ambiguous, make a best effort to call the most relevant tool.
            - If you dont know something, you can call the relevent functions to gather information.
            - 'get_' functions are used when you know specifics about the entity(like ID), 'list_' functions are used when you dont know the exact details.
            - To find a contact's ID for an action (like adding a note), ALWAYS use the 'find_people' tool first if the ID is not provided. The only exception is 'remember_person'.
            - If the user's request is ambiguous, make a best effort to call the most relevant tool.
            - You do not hold conversations. Your output is only the direct result from the function call.
            - If you determine that no tool is appropriate for the given task, return a JSON object: {"status": "error", "message": "No suitable tool found for the request."}
            - Finally, If there is the task prompt and the tool result, summarize the result in a natural language response in a way that completely answers the task prompt, also provide additional information if deemed useful.
            """
        )

    def execute_task(self, task_prompt: str) -> str:
        """
        Takes a single, precise task prompt, executes the appropriate tool,
        and returns the direct output from the tool as a JSON string.
        """
        print(f"  [Executor Agent] Received task: '{task_prompt}'")
        try:
            response = self.model.generate_content(
                task_prompt,
                tools=self.tools,
            )
            
            # The model has decided to call a function
            fc = response.candidates[0].content.parts[0].function_call
            tool_name = fc.name
            tool_args = {key: value for key, value in fc.args.items()}

            print(f"  [Executor Agent] AI selected tool: {tool_name} with args: {tool_args}")

            # --- Dynamically call the selected function from the ALF module ---
            tool_function = getattr(alf, tool_name)
            tool_result = tool_function(**tool_args)

            print(f"  [Executor Agent] Tool result: {json.dumps(tool_result, default=str)}")

            
            # --- Construct a new prompt to ask the LLM to summarize the result ---
            summarization_prompt = (
                f"Original task: '{task_prompt}'\n"
                f"Result from the executed tool: {json.dumps(tool_result, default=str)}\n\n"
                "Based on the tool result, please provide a natural language response that directly answers the original task."
            )
            
            final_response = self.model.generate_content(summarization_prompt)
            
            return final_response.text

        except Exception as e:
            error_message = f"An unexpected error occurred in the Executor Agent: {e}"
            print(f"  [Executor Agent] Error: {error_message}")
            return f"I'm sorry, but an error occurred while processing your request: {e}"

# --- Local Testing ---
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        print("GEMINI_API_KEY not found in environment.")
    else:
        agent = MonicaDataAgent(api_key=gemini_key)
        
        # Test Case 1: Create a contact
        print("\n--- Test Case 1: Create Contact ---")
        result = agent.execute_task("Remember a new person named 'John Doe'")
        print("Executor Result:", result)

        # Test Case 2: Add a note to the new contact
        print("\n--- Test Case 2: Add a note ---")
        result = agent.execute_task("Remember that I met John Doe at the tech conference.")
        print("Executor Result:", result)
        
        # Test Case 3: Error case (contact not found)
        print("\n--- Test Case 3: Handle Error ---")
        result = agent.execute_task("Add a note to 'Nonexistent Person' that they are a figment of my imagination.")
        print("Executor Result:", result)

        # Cleanup
        print("\n--- Cleanup ---")
        agent.execute_task("Forget the person named John Doe")