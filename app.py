import google.generativeai as genai
import os
import dotenv
from utils import count_api_call

dotenv.load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')

prompt = "IN SHORT what will be the reason for world war 3?"
response = model.generate_content(prompt)
count_api_call(__file__)

with open('output.md', 'w') as f:
    f.write(response.text)