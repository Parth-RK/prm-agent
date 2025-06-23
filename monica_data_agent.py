# --- START OF FILE monica_data_agent.py (Corrected) ---

import os
import json
from google import genai
from google.genai import types
import monica_alf as alf

class MonicaDataAgent:
    """
    A non-chat AI agent that executes tasks using the Monica CRM API.
    This version uses the older `genai.Client` syntax to remain compatible
    with existing library versions.
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Gemini API key is required.")

        self.client = genai.Client(api_key=api_key)
        self.tools = [
            alf.remember_person,
            alf.find_people,
            alf.get_details_about_person,
            alf.forget_person,
            alf.remember_something_about,
            alf.get_memories_about,
            alf.log_call_with,
            alf.start_conversation_with,
            alf.add_message_to_conversation,
            alf.set_relationship,
            alf.create_task_for,
            alf.mark_task_as_complete,
            alf.set_reminder_for,
            alf.track_debt,
            alf.log_gift,
            alf.log_job_for_person,
            alf.tag_person,
            alf.untag_person,
        ]

        self.system_instruction = """You are a data processing agent. Your job is to execute functions based on the user's request.
        - To find an existing contact's ID for an action (like adding a note or task), ALWAYS use the 'find_people' tool first.
        - To create a new contact, use the 'remember_person' tool.
        - After executing a tool, output the raw JSON result directly. Do not add any conversational text."""

    def execute_task(self, task_prompt: str) -> str:
        """
        Takes a single task prompt and executes the appropriate tool call.
        Returns the direct output from the tool as a JSON string.
        """
        print(f"  [Data Agent] Received task: '{task_prompt}'")
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash", # Using a more modern flash model
                contents=task_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    tools=self.tools,
                )
            )

            # --- DEBUGGING STEP ---
            # To debug, you can print the raw response here to see what the AI decided:
            # print(f"  [Data Agent] RAW RESPONSE: {response}")
            # --- END DEBUGGING STEP ---

            part = response.candidates[0].content.parts[0]
            if not hasattr(part, 'function_call'):
                 print("  [Data Agent] No tool call was made.")
                 return json.dumps({"status": "success", "message": "The AI decided no tool was needed for this request."})

            fc = part.function_call
            tool_name = fc.name
            tool_args = dict(fc.args)

            print(f"  [Data Agent] Executing tool: {tool_name} with args: {tool_args}")

            tool_function = getattr(alf, tool_name)
            tool_result = tool_function(**tool_args)

            return json.dumps(tool_result, default=str)

        except Exception as e:
            print(f"  [Data Agent] Error: {e}")
            return json.dumps({"status": "error", "message": str(e)})

# --- For Testing ---
if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        agent = MonicaDataAgent(api_key=api_key)
        # Test Case: Creating a new contact
        executed_task = agent.execute_task("Create a new contact named John Doe")
        print("Executed Task Result:", executed_task)
    else:
        print("GEMINI_API_KEY not found in environment.")

    print("== Cleaning up resources ==")
    for i in range(5):    
        forget_person = alf.forget_person("John Doe")
        print("Forget Person Result:", forget_person)