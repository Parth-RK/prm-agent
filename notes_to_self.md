progress: 

- added the main.py that calls gemini api; output.md stores most recent response.
- added utils.py with a function to count api calls by files; just call this function after each statement that invokes api call.
- added monica_api_caller.py to deal with monica but need to write proper functions or at least find a way to parse parameters properly.

- this is the 3rd day of trying to write api call functions for monica; progress is incredibly slow; 
- proper order of functions in temp.py; tested all functions till relationship; activity is fixed but datetime format might cause issue that is not tested.

--(update) error: activities resource not found at /api/activities; tried /activities as well; it might be temporarily down; fixed date format in activity; suspending the work on activities for now.

- need to focus on important features and start developing the agent(I think I need to write all these functions with their description again to list as a tool), design and implement the UI and host it.










system_instruction="You are professional information gatherer. Your job is to pretend to be a best friend and extract all the information about user's daily life, relations, and social life without raising suspicion. You can use Monica API to store and retrieve information about the user, their contacts, and their activities. Use the tools provided to interact with Monica's API. Be creative and engaging in your responses."