# AI Prompt Library Manager

A Streamlit app for managing and exploring a collection of AI prompts.

## Features

- View all available prompts
- Search prompts by category or AI tool
- Add a new prompt
- Display the highest-rated prompt
- Count prompts available per category
- View a summary of the prompt library

## Project Structure

- `prompt_library.py` – core logic (data loading/saving, search, stats), independent of the UI
- `app.py` – Streamlit interface
- `prompts.json` – prompt data (seeded with sample prompts)
- `requirements.txt` – Python dependencies

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment

Deployed on Streamlit Community Cloud: _add your app URL here after deploying_.
