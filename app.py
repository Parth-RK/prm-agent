import gradio as gr
import os
import dotenv
from main import StatefulOrchestrator

dotenv.load_dotenv()

def create_orchestrator(gemini_api_key, gemini_model_name, monica_api_url, monica_api_token):
    """Factory function to create a new orchestrator instance for a user session."""
    return StatefulOrchestrator(
        gemini_api_key=gemini_api_key,
        model_name=gemini_model_name,
        monica_api_url=monica_api_url,
        monica_token=monica_api_token
    )

def chat_interface(user_input, history, orchestrator_state, logs_history, gemini_key, gemini_model, monica_url, monica_token):
    """
    Main function to handle a single turn of the chat.
    It manages state and calls the orchestrator.
    """
    if not user_input.strip():
        return history, orchestrator_state, logs_history, ""

    if orchestrator_state is None:
        try:
            orchestrator_state = create_orchestrator(gemini_key, gemini_model, monica_url, monica_token)
        except Exception as e:
            error_msg = f"Error initializing orchestrator: {str(e)}"
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": error_msg})
            return history, None, logs_history + f"\n{error_msg}", ""

    try:
        bot_message, logs = orchestrator_state.process_user_turn(user_input)
    except Exception as e:
        bot_message = f"Encountered an error: {str(e)}"
        logs = f"Error during execution: {str(e)}"
        
    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": bot_message})
    
    new_logs = logs_history
    if logs:
        log_entry = f"--- User: {user_input} ---\n{logs}"
        new_logs = f"{log_entry}\n\n{new_logs}"
        
    return history, orchestrator_state, new_logs, ""

with gr.Blocks(theme=gr.themes.Soft(), title="Genica") as demo:
    gr.Markdown("# 🤖 Genica the prm-agent")
    gr.Markdown("Your personal AI assistant to help manage your social life. Start chatting below!\nhttps://github.com/parth-rk/prm-agent")

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                label="Conversation", 
                type="messages",
                height=600,
                avatar_images=(None, "https://www.google.com/s2/favicons?sz=128&domain=gemini.google.com")
            )
            user_textbox = gr.Textbox(
                label="Your Message",
                placeholder="e.g., I met a new person today, her name is Jane.",
                lines=1,
            )
        with gr.Column(scale=1):
            with gr.Accordion("⚙️ Settings (Keys & Models)", open=False):
                gr.Markdown("Leave these blank to use the default `.env` configurations.")
                gemini_key_input = gr.Textbox(label="Gemini API Key", placeholder="AIzaSy...", type="password", value=os.getenv("GEMINI_API_KEY", ""))
                gemini_model_input = gr.Textbox(label="Gemini Model Name", placeholder="gemini-3-flash-preview", value=os.getenv("GEMINI_MODEL_NAME", ""))
                monica_url_input = gr.Textbox(label="Monica API URL", placeholder="https://app.monicahq.com/api", value=os.getenv("MONICA_API_URL", "https://app.monicahq.com/api"))
                monica_token_input = gr.Textbox(label="Monica API Token", placeholder="eyJ0...", type="password", value=os.getenv("MONICA_TOKEN", ""))
                
                reset_state_btn = gr.Button("Apply & Restart Session", variant="primary")
            with gr.Accordion("📝 Execution Logs", open=False):
                log_output = gr.Textbox(label="Logs", lines=31, interactive=False, max_lines=31)

    orchestrator = gr.State(None)
    logs_state = gr.State("")

    # Restart session completely
    def restart_session(g_key, g_model, m_url, m_token):
        return [], None, "", "Session restarted with new settings!"
        
    reset_state_btn.click(
        restart_session,
        inputs=[gemini_key_input, gemini_model_input, monica_url_input, monica_token_input],
        outputs=[chatbot, orchestrator, logs_state, log_output]
    )

    user_textbox.submit(
        chat_interface,
        inputs=[user_textbox, chatbot, orchestrator, logs_state, gemini_key_input, gemini_model_input, monica_url_input, monica_token_input],
        outputs=[chatbot, orchestrator, log_output, user_textbox]
    )

if __name__ == "__main__":
    demo.launch(share=True)
