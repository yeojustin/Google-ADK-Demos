# Deploying ADK Agents to Cloud Run

This project demonstrates how to build and deploy an Agent Development Kit (ADK) agent to Google Cloud Run. It is based on the official Google Codelabs guide.

## Codelab Reference
For the full interactive tutorial, see:
[Build and deploy an ADK agent on Cloud Run Codelab](https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/5-deploying-agents/deploy-an-adk-agent-to-cloud-run#0)

---

## Step-by-Step Deployment Instructions

Follow these steps from your terminal inside the [zoo_guide_agent](file:///Users/jy/Documents/GitHub/Google-ADK-Demos/deploy-adk-agents-to-cloudrun/zoo_guide_agent) directory to deploy the agent:

### 1. Set terminal environment variables
Configure your shell with the target project information:
```bash
PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
SA_NAME=lab2-cr-service
```

### 2. Enable Required APIs
Enable the necessary Google Cloud APIs for Cloud Run, container building, registry hosting, and Vertex AI:
```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  aiplatform.googleapis.com \
  compute.googleapis.com
```

### 3. Create a Custom Service Account
Create a dedicated Service Account for the agent to follow the principle of least privilege:
```bash
gcloud iam service-accounts create ${SA_NAME} \
    --display-name="Service Account for zoo guide agent"
```

Resolve and set the service account email variable:
```bash
SERVICE_ACCOUNT=${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
```

### 4. Grant Vertex AI Access Permissions
Grant the Service Account the "Vertex AI User" role so that the deployed agent can invoke Gemini models:
```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/aiplatform.user"
```

### 5. Create the `.env` Configuration File
Generate the `.env` file containing local configurations and Cloud Run container settings:
```bash
cat <<EOF > .env
PROJECT_ID=$PROJECT_ID
PROJECT_NUMBER=$PROJECT_NUMBER
SA_NAME=$SA_NAME
SERVICE_ACCOUNT=$SERVICE_ACCOUNT
MODEL="gemini-2.5-flash"
EOF
```

### 6. Deploy the Agent
Run the deployment command using the ADK CLI via `uvx`. This command packages your code, builds a container, registers it in Artifact Registry, and deploys it to Cloud Run:
```bash
uvx --from google-adk==1.14.0 \
adk deploy cloud_run \
  --project=$PROJECT_ID \
  --region=europe-west1 \
  --service_name=zoo-tour-guide \
  --with_ui \
  . \
  -- \
  --labels=dev-tutorial=codelab-adk \
  --service-account=$SERVICE_ACCOUNT
```

*Note: When prompted to allow unauthenticated invocations, select `y` if you want the developer web UI to be publicly accessible for testing.*

---

## Testing the Deployed Agent
1. Open the service URL returned by the deploy command (e.g., `https://zoo-tour-guide-xxxxx.europe-west1.run.app`).
2. Toggle on **Token Streaming** in the top-right corner.
3. Chat with the agent (e.g., say `hello` or ask `"Where can I find the polar bears and what is their diet?"`).

---

## Clean Up Resources
To avoid ongoing charges, clean up the deployed service and container registry repository:
```bash
gcloud run services delete zoo-tour-guide --region=europe-west1 --quiet
gcloud artifacts repositories delete cloud-run-source-deploy --location=europe-west1 --quiet
```
