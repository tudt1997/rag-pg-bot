# RAG Pg Bot - Release 0.0.1

## Prerequisites
- Ensure **Docker** is installed and running.
- You can download Docker here: [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)

## Setup Instructions

### Step 1: Run Docker Setup Script

First, make sure Docker is running.

Then execute the following command:

```bash
sh setup.sh
```

This script will:
- Start **Elasticsearch** on port 9200
- Start **Ollama** on port 11434
- Pull the models: `qwen2.5:3b` and `qwen2.5:3b-instruct`

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Launch the Application

### Step 3: Start Backend and Frontend

```bash
sh start_all.sh
```

- The backend will run on port 5001 and log to `backend.txt`.
- The frontend will run on port 3000 and log to `frontend.txt`.

## Verify the Application

- Backend API: [http://localhost:5001](http://localhost:5001)
- Frontend UI: [http://localhost:3000](http://localhost:3000)

## Stopping the Application

Stop the Docker containers:

```bash
docker stop elasticsearch ollama
```

Stop the backend and frontend processes:

```bash
pkill -f app.py
pkill -f load_script.py
```

## Notes

- Ensure ports 9200, 11434, 5001, and 3000 are available.
- Always verify Docker is running before executing the scripts.

