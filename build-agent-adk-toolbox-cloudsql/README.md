Set up project

uv init
uv add cloud-sql-python-connector --extra pg8000
uv add python-dotenv

Execute Set up Script
mkdir -p ~/build-agent-adk-toolbox-cloudsql/logs
bash scripts/setup_database.sh > logs/database_setup.log 2>&1 &

Set up .env
echo "DB_PASSWORD=restaurant-pwd" >> .env
echo "DB_INSTANCE=restaurant-instance" >> .env
echo "DB_NAME=restaurant_db" >> .env
source .env

# For Vertex AI / Gemini API calls

echo "GOOGLE_CLOUD_LOCATION=global" > .env

# For Cloud SQL, Cloud Run, Artifact Registry

echo "REGION=us-central1" >> .env

gcloud services enable \
 aiplatform.googleapis.com \
 sqladmin.googleapis.com \
 compute.googleapis.com \
 run.googleapis.com \
 cloudbuild.googleapis.com \
 artifactregistry.googleapis.com

bash setup_verify_trial_project.sh && source .env

Understanding the setup script scripts/setup_database.sh
Now let's try to understand the setup script we previously configured. It does the following process

The very first command we execute there is the gcloud sql instances create command with the following flag
db-custom-1-3840 is the smallest dedicated-core Cloud SQL tier (1 vCPU, 3.75 GB RAM) in ENTERPRISE edition. You can read more details in here. A dedicated core is required for the Vertex AI ML integration — shared-core tiers (db-f1-micro, db-g1-small) do not support it.
--root-password sets the password for the default postgres user.
--enable-google-ml-integration enables Cloud SQL's built-in integration with Vertex AI, which lets you call embedding models directly from SQL using the embedding() function.
Verify whether the instance already in RUNNABLE status
Grant the Cloud SQL instance's service account permission to call Vertex AI using the gcloud projects add-iam-policy-binding command. This is required for the built-in embedding() function that we will use when seeding the database
Creating the database
Executing the seeding script setup_restaurant_db.py script
Understanding the seed script scripts/setup_restaurant_db.py
Now, moving to the seeding script, this script do the following things:

Initialize connection to the database instance
Installs two PostgreSQL extensions:
google_ml_integration — provides the embedding() SQL function, which calls Vertex AI embedding models directly from SQL. This is a database-level extension that makes ML functions available inside restaurant_db. The instance-level flag (--enable-google-ml-integration) you set during instance creation allows the Cloud SQL VM to reach Vertex AI — the extension makes the SQL functions available within this specific database.
vector (pgvector) — adds the vector data type and distance operators for storing and querying embeddings.
Create the table, notes that the description_embedding column is vector(3072) — a pgvector column that stores 3072-dimensional vectors.
Seed the initial menu items data
Generate the embedding data from description field and fill the description_embedding using the built in vertex integration via the embedding() function
embedding('gemini-embedding-001', description) — calls Vertex AI's Gemini embedding model directly from SQL, passing each job's description text. This is the google_ml_integration extension you installed in the seed script.
::vector — casts the returned float array to pgvector's vector type so it can be stored and queried with distance operators.
The UPDATE runs across all 15 rows, generating one 3072-dimensional embedding per job description.

MCP Toolbox for Databases is an open-source MCP server built specifically for database access. Without it, you would write Python functions that open database connections, manage connection pools, construct parameterized queries to prevent SQL injection, handle errors, and embed all of that code inside your agent. Every agent that needs database access repeats this work. Changing a query means redeploying the agent.

With Toolbox, you write a YAML file. Each tool maps to a parameterized SQL statement. Toolbox handles connection pooling, parameterized queries, authentication, and observability. Tools are decoupled from the agent — update a query by editing tools.yaml and restarting Toolbox, without touching agent code. The same tools work across ADK, LangGraph, LlamaIndex, or any MCP-compatible framework.

Now, we need to create a file called tools.yaml in the Cloud Shell Editor to set up our tools configuration

The file uses multi-document YAML — each block separated by --- is a standalone resource. Every resource has a kind that declares what it is (sources for database connections, tools for agent-callable actions) and a type that specifies the backend (cloud-sql-postgres for the source, postgres-sql for SQL-based tools). A tool references its source by name, which is how Toolbox knows which connection pool to execute against. Environment variables use ${VAR_NAME} syntax and are resolved at startup.
