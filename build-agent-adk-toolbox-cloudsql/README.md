# Google Cloud SQL + MCP Toolbox Demo

This repository demonstrates setting up a Google Cloud SQL (PostgreSQL) database with Vertex AI vector integration, and exposing it to LLM agents using the Model Context Protocol (MCP) Toolbox.

---

## Architecture & File Placement (Where do things go?)

Before starting, it is helpful to understand the relationship between the `toolbox` binary and the `tools.yaml` configuration file:

### 1. The `toolbox` Executable (Install Once)
The `toolbox` is a **standalone compiled binary executable (not a Python library)**. You only need to download it once.

*   **Global Installation (Recommended)**: To avoid copying the binary into every project folder, move it to your system's global executable path:
    ```bash
    sudo mv toolbox /usr/local/bin/
    ```
    After doing this, you can run the server simply as `toolbox` instead of `./toolbox` from any project folder.
*   **Local Installation**: You can keep it locally in the project root folder and execute it as `./toolbox`.

### 2. The `tools.yaml` Configuration (Project Specific)
The `tools.yaml` file defines the connection parameters for the database and maps your specific SQL queries to agent-callable tools. 
*   Because this configuration is specific to the "restaurant" database and schema, `tools.yaml` **must live in the root of your project directory** (`./tools.yaml`).

---

## Chronological Step-by-Step Guide

Follow these steps in order to provision the infrastructure, verify the database, configure the MCP server, and run tests.

### Step 1: Initialize Project & Install Packages
Initialize the project environment and add required dependencies:

```bash
uv init
uv add cloud-sql-python-connector --extra pg8000
uv add python-dotenv
```

### Step 2: Configure Environment Variables & GCP APIs
1. Create a `.env` file in the root of the project:
   ```env
   # Vertex AI / Gemini API Settings
   GOOGLE_CLOUD_LOCATION=global

   # Cloud SQL & Region Settings
   REGION=us-central1
   GOOGLE_CLOUD_PROJECT=your-gcp-project-id
   DB_PASSWORD=restaurant-pwd
   DB_INSTANCE=restaurant-instance
   DB_NAME=restaurant_db
   ```

2. Enable the required Google Cloud APIs in your project:
   ```bash
   gcloud services enable \
     aiplatform.googleapis.com \
     sqladmin.googleapis.com \
     compute.googleapis.com \
     run.googleapis.com \
     cloudbuild.googleapis.com \
     artifactregistry.googleapis.com
   ```

3. Bind active project configurations:
   ```bash
   bash setup_verify_trial_project.sh && source .env
   ```

### Step 3: Provision and Seed the Database
Run the setup script in the background to provision Cloud SQL, grant Vertex AI IAM access, create tables, and seed the menu items:

```bash
mkdir -p logs
bash scripts/setup_database.sh > logs/database_setup.log 2>&1 &
```

> [!NOTE]
> Database creation can take 5–10 minutes. You can monitor the progress with:
> `tail -f logs/database_setup.log`

### Step 4: Verify the Database Seeding
Verify that the database has been successfully initialized and seeded with 15 menu items along with their Vertex AI vector embeddings:

```bash
uv run python scripts/verify_database.py
```

Expected output:
```
Menu Items: 15/15
Embeddings: 15/15

✓ Database ready!
```

---

## PART 1: Running & Querying the MCP Server Directly (No ADK)

### Step 5: Download the macOS Binary
Download the macOS Apple Silicon (arm64) version of the MCP Toolbox binary and make it executable:

```bash
curl -O https://storage.googleapis.com/mcp-toolbox-for-databases/v1.1.0/darwin/arm64/toolbox
chmod +x toolbox
```

*(Optional: Run `sudo mv toolbox /usr/local/bin/` to install it globally).*

### Step 6: Verify YAML Config via Direct Invocation
Before starting the network server, test that the connection settings in `tools.yaml` are correct by executing a direct tool invocation:

```bash
set -a; source .env; set +a
./toolbox invoke search-menu '{"category": "Main Course", "cuisine_type": "Italian"}' --config tools.yaml
```

If successful, it returns the raw JSON list of matching menu items.

### Step 7: Run the Toolbox HTTP Server
Launch the toolbox server as a background service:

```bash
set -a; source .env; set +a
./toolbox --config tools.yaml --enable-api --port 5001 > logs/mcp_toolbox.log 2>&1 &
```

> [!IMPORTANT]
> **macOS AirPlay Port Conflict**: macOS uses port `5000` by default for the `ControlCenter` daemon (AirPlay/AirTunes). Always use `--port 5001` on macOS to avoid traffic hijacking.

Verify the server started successfully by checking the logs (`logs/mcp_toolbox.log`):
```
... INFO "Initialized 1 sources: restaurant-db"
... INFO "Server ready to serve!"
```

### Step 8: Query the Running Server Directly (HTTP REST)
You can call the REST API endpoints directly without any agent wrappers:

1. **List the available tools schema**:
   ```bash
   curl -s http://localhost:5001/api/toolset | python3 -m json.tool
   ```

2. **Invoke a database tool via POST query**:
   ```bash
   curl -s -X POST http://localhost:5001/api/tool/search-menu/invoke \
     -H "Content-Type: application/json" \
     -d '{"category": "Main Course", "cuisine_type": "Italian"}' | jq '.result | fromjson'
   ```

---

## PART 2: Integrating with Google ADK Agent

Once you've verified that the standalone MCP server is functioning, connect it to a Google Agent Development Kit (ADK) agent.

### Step 9: Install ADK Package Dependencies
```bash
uv add google-adk mcp
```

### Step 10: Code Files
* **`agent.py`**: Defines the `root_agent` and attaches the `McpToolset` pointing to the Server-Sent Events (SSE) stream endpoint `http://localhost:5001/mcp/sse`.
* **`main.py`**: A helper execution script that sets up environment flags, configures memory/sessions, runs the agent via `InMemoryRunner`, and prints clean text responses.

### Step 11: Run the Agent
Execute the runner client script to chat with the database agent:

```bash
uv run python main.py "What Italian dishes do you have?"
```
