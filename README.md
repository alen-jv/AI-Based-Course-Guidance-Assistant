# AI-Based Course Guidance Assistant

## Files
- `app.py` — Streamlit application
- `courses.json` — sample course dataset (12 courses)
- `requirements.txt` — dependencies

## Setup
```bash
pip install -r requirements.txt
```

## Run
```bash
streamlit run app.py
```
Then open the local URL shown in the terminal (usually http://localhost:8501).

## Usage
1. Enter interests, existing skills, career goal, and weekly study hours.
2. Click **Get Course Recommendations**.
3. Review the 3–5 recommended courses, reasons, prerequisites, and learning path.
4. Ask follow-up questions (e.g. prerequisites, duration, skills gained) in the chat box.

## Notes
- Works fully offline — no API key required (rule-based keyword matching).
- To add more courses, edit `courses.json` following the existing structure.
