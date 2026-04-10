# Front Streamlit

## Installation

1. Go to the frontend folder:

   cd front-streamlit

2. Install dependencies with Poetry:

   poetry install

## Run dashboard

1. Start FastAPI first (port 8888 by default).
2. Start Streamlit from this folder:

   poetry run streamlit run dashboard/dashboard_app.py

No FASTAPI_BASE_URL is required on the command line when FastAPI runs on http://localhost:8888.

## Optional custom API URL

You can configure a different API URL once with an environment variable in a .env file.

Example in repository .env or front-streamlit/.env:

FASTAPI_BASE_URL=http://localhost:8888
FASTAPI_TIMEOUT_SECONDS=25
FASTAPI_PAGE_LIMIT=1000
