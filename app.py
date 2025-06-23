import gradio as gr
import os
import dotenv
from main import StatefulOrchestrator

dotenv.load_dotenv()

# 1. Get API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")

# 2. Core Logic
def create_orchestrator():
    """Factory function to create a new orchestrator instance for a user session."""
    return StatefulOrchestrator(gemini_api_key=GEMINI_API_KEY)

def chat_interface(user_input, history, orchestrator_state, logs_history):
    """
    Main function to handle a single turn of the chat.
    It manages state and calls the orchestrator.
    """
    if not user_input.strip():
        # Return original state if input is empty
        return history, orchestrator_state, logs_history, ""

    if orchestrator_state is None:
        orchestrator_state = create_orchestrator()

    bot_message, logs = orchestrator_state.process_user_turn(user_input)
    
    history.append((user_input, bot_message))
    
    new_logs = logs_history
    if logs:
        # Prepend new logs to show the most recent ones at the top
        log_entry = f"--- User: {user_input} ---\n{logs}"
        new_logs = f"{log_entry}\n\n{new_logs}"
        
    # Return updated history, state, logs, and clear the textbox
    return history, orchestrator_state, new_logs, ""

# 3. Gradio UI
with gr.Blocks(theme=gr.themes.Soft(), title="Monica CRM") as demo:
    gr.Markdown("# 🤖 AI Best Friend (Monica CRM)")
    gr.Markdown("Your personal AI assistant to help manage your social life. Start chatting below!")

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                label="Conversation", 
                height=600, 
                bubble_full_width=False,
                avatar_images=(None, "https://www.google.com/s2/favicons?sz=128&domain=gemini.google.com") # Bot avatar
            )
            user_textbox = gr.Textbox(
                label="Your Message",
                placeholder="e.g., I met a new person today, her name is Jane.",
                lines=1,
            )
        with gr.Column(scale=1):
            with gr.Accordion("📝 Execution Logs", open=False):
                log_output = gr.Textbox(label="Logs", lines=31, interactive=False, max_lines=31)

    # State management for each user session
    orchestrator = gr.State(None)
    logs_state = gr.State("")

    # Wire up components
    user_textbox.submit(
        chat_interface,
        inputs=[user_textbox, chatbot, orchestrator, logs_state],
        outputs=[chatbot, orchestrator, log_output, user_textbox]
    )

if __name__ == "__main__":
    demo.launch(share=True)
