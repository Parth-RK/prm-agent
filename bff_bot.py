import os
import json
import dotenv
from google import genai
from google.genai import types
from monica_data_agent import MonicaDataAgent

# Load environment variables
dotenv.load_dotenv()

class StatefulInformationGatherer:
    """
    An AI best friend that intelligently gathers a complete set of information 
    before committing it to the data store. It manages the conversation to
    collect a "batch" of details first.
    """
    def __init__(self, gemini_api_key: str):
        self.data_agent = MonicaDataAgent(api_key=gemini_api_key)
        self.client = genai.Client(api_key=gemini_api_key)

        # --- KEY CHANGE: The new, more detailed system prompt ---
        system_instruction = """You are a helpful and friendly AI best friend. Your main goal is to help the user keep track of their life.

        Your most important skill is gathering COMPLETE information before you act. When the user tells you about something new, like a person, a task, or an event, do not try to save it immediately with partial details. Your job is to ask natural, clarifying follow-up questions to get a complete picture.

        **Information Gathering Rules:**
        1.  **For a new person:** Don't just save a first name. Ask for their full name, phone number, email, or a note about how the user met them.
        2.  **For a new task:** Don't just save the task. Ask if there's a deadline or due date.
        3.  **For a new event:** Ask for the date, time, and location.

        **Committing Data:**
        - Once you believe you have a complete, logical "batch" of information (e.g., all the key details for one new contact), you will summarize it into a single, comprehensive instruction for your data assistant.
        - You will output this final instruction inside a special tag: <commit_task>Instruction goes here</commit_task>.
        - DO NOT use the <commit_task> tag if you only have partial information. Ask for more details instead.

        **Retrieving Data:**
        - Retrieving data is simpler. If the user asks a direct question (e.g., "What is John's phone number?"), you can generate a <commit_task> immediately.

        Example of Storing (Batching):
        User: Bro, I met this girl today—her name’s Sarah.
        You: Ooooh, look at you. Where’d this Sarah appear from?
        User: Park. Just bumped into her. She was actually super nice.
        You: Damn. You got her number or just vibes?
        User: I got her number. Last name’s Smith.
        You: So… Sarah Smith, huh? Pass me that number, Romeo—I’ll stash it for you.
        User: 123‑456‑7890.
        You: Got it. Sarah Smith, saved. But let’s be real, that number sounds faker than your gym schedule 😂
        <commit_task>Create a new contact named Sarah Smith, phone:123‑456‑7890</commit_task>
        
        **Example of Retrieving (Immediate):**
        User: What's on my to-do list for tomorrow?
        You: Let me check for you! <commit_task>Retrieve all tasks due tomorrow.</commit_task>
        """

        self.chat_session = self.client.chats.create(
            model="gemini-2.5-flash", 
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            ),
            history=[]
        )
        print("🤖 AI Best Friend is online. Let's chat!")

    def process_user_turn(self, user_input: str):
        """Processes a single turn of the conversation, handling the commit logic."""
        print(f"\nYou: {user_input}")
        
        # 1. Get the response from the AI
        response = self.chat_session.send_message(user_input)
        response_text = response.text
        
        # 2. Check if the AI wants to commit a task
        if "<commit_task>" in response_text:
            # Separate the conversational part from the task instruction
            task_prompt = response_text.split("<commit_task>")[1].split("</commit_task>")[0]
            display_text = response_text.split("<commit_task>")[0].strip()
            
            # Print the conversational part first
            if display_text:
                print(f"Best Friend: {display_text}")

            print(f"Executing task: {task_prompt}") # For debugging

            # 3. Call the Data Agent to execute the complete task
            task_result_json = self.data_agent.execute_task(task_prompt)
            
            # 4. Formulate a final, natural response based on the result
            final_prompt = f"Here is the result from your data assistant: {task_result_json}. Now, give a very short, natural confirmation to the user based on this result. If there was an error, apologize naturally and say you couldn't do it right now."
            final_response = self.chat_session.send_message(final_prompt)
            print(f"Best Friend: {final_response.text}\n")
        else:
            # No task was committed, just a conversational turn
            # This is the "information gathering" part of the loop
            print(f"Best Friend: {response_text}\n")


def main_demo():
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    
    # Use the new class
    chatbot = StatefulInformationGatherer(gemini_api_key=gemini_api_key)
    
    print("\n--- AI Best Friend (Monica CRM Demo) ---")
    print("Type 'quit' or 'exit' to end the conversation.")

    # Start the conversation loop
    initial_input = "Hey! I met someone new today at the coffee shop, her name is Jane."
    chatbot.process_user_turn(initial_input)
    initial_input = "She was really nice, we talked about books and she gave me her number. Her name is Jane Doe, and her number is 123-456-7890."
    chatbot.process_user_turn(initial_input)

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["quit", "exit"]:
                print("\n🤖 Talk to you later! Goodbye!")
                break
            chatbot.process_user_turn(user_input)
        except (KeyboardInterrupt, EOFError):
            print("\n🤖 Goodbye!")
            break


if __name__ == "__main__":
    main_demo()