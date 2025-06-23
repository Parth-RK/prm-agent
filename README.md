A repo for project that aims to build an AI agent to manage your personal connections.

This project is a personal relationship manager powered by AI. 
Think of it as a friendly chat assistant that helps you remember important details about the people in your life. 
You can tell it about new people you meet, things you've discussed, or tasks you need to do, and it will neatly organize everything for you in your Monica CRM account. 
It's a simple, open-source tool designed to make managing your personal connections a little easier.

*Finally, built the tool that will make it easier for me to use Monica-PRM.*

I wanna build a mobile app for this. Let's see when it will be possible.

Also mind it
any and all None type errors are caused because the agent couldn't find right tool to execute the task. Will fix in near future.
So if such errors occur, just add the name of the tool to monica_data_agent.py from monica_api_caller.py or monica_alf.py
And if those functions are not there then I will probably need to add the missing ones.

And Customize the perosnality of the AI but don't alter or contradict base structure of the existing prompts.


### Setup
Create a virtual environment(Optional, but recommended. Alt. Conda)
```bash
python -m venv venv
```

on linux/mac
```bash
source venv/bin/activate
```
on windows
```bash
.\venv\Scripts\activate
```

Install Requirements
```bash
pip install -r requirements.txt
```

### .env
Create a .env file and copy the contents of .env.example given.
Or on Linux
```bash
cp .env.example .env
```
Replace the relevant fields with actual credentials.

### Run the App
```bash
python3 app.py
```