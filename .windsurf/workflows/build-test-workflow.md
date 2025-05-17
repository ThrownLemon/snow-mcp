---
description: 
---

I'll follow this process whenever I need to build and run the MCP server for example after making code changes and wanting to test the mcp server and or mcp tool:

Step 1. Activate the virtual environment: .venv\Scripts\activate
Step 2. Install the package in development mode: pip install -e .
Step 3. Start the server: servicenow-mcp-sse --host=0.0.0.0 --port=8052
Step 4. Ask the user to refresh our MCP server connection.

IMPORTANT! Only proceed after you've confirmed with the user that the mcp server has been refreshed.

Step 4. Continue with your work/tasks etc.