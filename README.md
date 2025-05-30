# HireAI

HireAI is an intelligent recruitment assistant that helps streamline the hiring process through AI-powered features.

## Features

- Resume Parsing: Extract and structure information from resumes (PDF, DOCX)
- Candidate Ranking: AI-powered ranking of candidates based on job requirements
- Natural Language Job Search: Search through job descriptions using natural language
- Outreach Email Generation: Generate personalized outreach emails to candidates
- Gradio UI: User-friendly interface for all features
- Supabase Integration: Secure storage of candidate profiles and job data

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your credentials:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   OPENAI_API_KEY=your_openai_api_key
   ```
5. Download spaCy model:
   ```bash
   python -m spacy download en_core_web_sm
   ```

## Project Structure

```
hireai/
├── app/
│   ├── __init__.py
│   ├── main.py              # Gradio UI implementation
│   ├── config.py            # Configuration settings
│   └── utils.py             # Utility functions
├── core/
│   ├── __init__.py
│   ├── parser.py            # Resume parsing logic
│   ├── ranker.py            # Candidate ranking logic
│   ├── search.py            # Job search functionality
│   └── email.py             # Email generation
├── database/
│   ├── __init__.py
│   ├── models.py            # Database models
│   └── supabase_client.py   # Supabase integration
├── tests/
│   └── __init__.py
├── .env.example
├── requirements.txt
└── README.md
```

## Usage

Run the application:
```bash
python -m app.main
```

## License

MIT License 