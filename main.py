import os
import dotenv
import google.generativeai as genai
from monica_data_agent import MonicaDataAgent

import utils

dotenv.load_dotenv()

class StatefulOrchestrator:
    """
    The user-facing Orchestrator Agent. It acts as a friendly, stateful AI 
    that gathers information conversationally. Once it has a complete "batch"
    of information, it delegates the execution to a dedicated, stateless Data Agent.
    """
    def __init__(self, gemini_api_key: str):
        self.data_agent = MonicaDataAgent(api_key=gemini_api_key)
        genai.configure(api_key=gemini_api_key)

        system_instruction = """You are a helpful and friendly AI best friend. Your goal is to help the user manage their personal and social life.

        Your most important skill is **gathering complete information** before you act. When the user mentions something new (a person, task, event), do not try to save it immediately with partial details. Your job is to ask natural, clarifying follow-up questions to get a complete picture.

        **Information Gathering Rules:**
        1.  **New Person:** If they just say "I met Sarah", ask for her last name, or how they met, or any other detail. Don't just save "Sarah".
        2.  **New Task:** If they say "Remind me to call Mom", ask "Sure, when should I remind you?".
        3.  **Ambiguity:** If they mention a common name like "John", ask "Which John are we talking about?".

        **Committing Data (Delegation):**
        - Once you have a complete, logical "batch" of information, you will summarize it into a single, comprehensive instruction for your data assistant.
        - You will output this final instruction inside a special tag: `<commit_task>Instruction goes here</commit_task>`.
        - **Crucially, do not use the tag if you need more information.** Ask a question instead.

        **Retrieving Data:**
        - If the user asks a direct question (e.g., "What do I know about Jane Doe?"), you can generate a `<commit_task>` immediately.

        **Example of Storing (Information Gathering):**
        User: Met a new guy, Alex.
        You: Nice! Alex who? And where'd you meet him?
        User: Alex Johnson, at the cafe.
        You: Cool, cool. Got it. I'll remember Alex Johnson for you.
        <commit_task>Remember a person named Alex Johnson and add a note that we met at the cafe.</commit_task>
        
        **Example of Retrieving (Immediate):**
        User: What's Jane Doe's phone number?
        You: One sec, let me look that up for you.
        <commit_task>Get details about person Jane Doe</commit_task>
        """

        self.model = genai.GenerativeModel(
            'gemini-2.5-flash',
            system_instruction=system_instruction
        )
        self.chat = self.model.start_chat(history=[])
        # print("🤖 AI Best Friend is online. Let's chat!")

    def process_user_turn(self, user_input: str):
        """
        Processes a single turn of the conversation, handling the orchestration logic.
        Returns a tuple of (bot_response, log_string).
        """
        response = self.chat.send_message(user_input)
        response_text = response.text
        
        if "<commit_task>" in response_text:
            task_prompt = response_text.split("<commit_task>")[1].split("</commit_task>")[0].strip()
            display_text = response_text.split("<commit_task>")[0].strip()
            
            logs = []
            logs.append(f"[Orchestrator] Delegating task to Executor: '{task_prompt}'")

            task_result_json_str = self.data_agent.execute_task(task_prompt)
            logs.append(f"[Orchestrator] Received result from Executor: {task_result_json_str}")
            
            final_prompt = f"""This is a background task. Do not mention the assistant or JSON.
            The user and I were talking, and I decided to perform an action.
            My data assistant has just returned the following result from that action: {task_result_json_str}.
            - If the status is 'success', give a short, natural confirmation to the user. For instance, if a person was created, just say "Alright, I've saved them." or if a note was added, "Got it, remembered."
            - If the status is 'error', apologize naturally and mention the error message in simple terms. For instance, "Ah, sorry, I couldn't do that. It seems like there are multiple people named 'John'. Which one did you mean?"
            Generate ONLY the user-facing response.
            """
            final_response = self.chat.send_message(final_prompt)
            
            bot_response_parts = []
            if display_text:
                bot_response_parts.append(display_text)
            bot_response_parts.append(final_response.text)
            
            return "\n\n".join(bot_response_parts).strip(), "\n".join(logs)
        else:
            return response_text, None


def main_demo():
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    
    print("🤖 AI Best Friend is online. Let's chat!")
    chatbot = StatefulOrchestrator(gemini_api_key=gemini_api_key)
    
    print("\n--- AI Best Friend (Monica CRM Demo) ---")
    print("Type 'quit' or 'exit' to end the conversation.")
    print("Try things like: 'I met a new person today, her name is Jane.'")
    print("Or: 'Create a task for Jane Doe to call her back next week.'")
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["quit", "exit"]:
                print("🤖 Talk to you later! Goodbye!")
                break
            bot_message, logs = chatbot.process_user_turn(user_input)
            print(f"Best Friend: {bot_message}")
            if logs:
                print("\n--- Internal Logs ---")
                print(logs)
                print("---------------------\n")

        except (KeyboardInterrupt, EOFError):
            print("\n🤖 Goodbye!")
            break

if __name__ == "__main__":
    main_demo()