# Learning Map Project

A personalized learning path planning application.

## Quick Start

1. **Start the database:**
Download the latest pocketbase zip file and serve the pocketbase using below command. Update the version as needed.
   ```bash
   ../pocketbase_0.29.3_windows_amd64/pocketbase serve --dir ./pocketbase-data
   ```

2. **Activate virtual environment:**
Create a virtual environment and activate it
   ```bash
   venv\Scripts\activate
   ```
3. **Install the requirements**
```bash
pip install -r requirements.txt
```
4. Deploy the agentcore/ to Bedrock Agentcore
5.  **Create .env file**
Copy .env.example content to it and update values.

6. **Run the application:**
This is to start the application.
   ```bash
   python run_server.py
   ```

## Optional: Kuzu Database Explorer

To explore the skills graph database:
```bash
docker run --rm -p 8000:8000 -v "${PWD}:/database" -e KUZU_FILE="skills_graph.db" kuzudb/explorer:latest
```