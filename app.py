"""
AI-Based Course Guidance Assistant
A simple Streamlit prototype that recommends courses based on a
student's interests, existing skills, career goal, and available study time.

Run with:  streamlit run app.py
"""

import json
import re
import streamlit as st

# ---------------------------------------------------------------------
# Load course data
# ---------------------------------------------------------------------
@st.cache_data
def load_courses():
    with open("courses.json", "r", encoding="utf-8") as f:
        return json.load(f)

COURSES = load_courses()


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------
def split_terms(text):
    """Split a comma/space separated string into lowercase clean terms."""
    if not text:
        return []
    parts = re.split(r"[,/]", text)
    return [p.strip().lower() for p in parts if p.strip()]


def score_course(course, interests, skills, career_goal, study_hours):
    """
    Simple rule-based scoring (0-100).
    This is not a machine-learning model - it is transparent, explainable
    keyword matching, which is appropriate for a small prototype.
    """
    score = 0
    reasons = []

    # 1. Interest match (highest weight)
    interest_hits = [i for i in interests if i in course["interests"]]
    if interest_hits:
        score += 40
        reasons.append(f"Matches your interest in {', '.join(interest_hits)}")

    # 2. Career goal match
    if career_goal and career_goal in [c.lower() for c in course["career_goals"]]:
        score += 30
        reasons.append(f"Aligned with your career goal of becoming a {career_goal}")

    # 3. Existing skills -> ready for this course (prerequisite satisfied)
    required = course["skills_required"]
    if required:
        have_all = all(r in skills for r in required)
        if have_all:
            score += 15
            reasons.append("You already have the required skills for this course")
        else:
            missing = [r for r in required if r not in skills]
            reasons.append(f"You may need to learn first: {', '.join(missing)}")
    else:
        score += 5
        reasons.append("No prior skills required — good starting point")

    # 4. Study time fit
    if study_hours:
        if study_hours >= course["hours_per_week"]:
            score += 15
            reasons.append("Fits within your available weekly study time")
        else:
            reasons.append(
                f"Needs about {course['hours_per_week']} hrs/week; "
                f"you may need to allocate slightly more time"
            )

    return score, reasons


def recommend_courses(interests, skills, career_goal, study_hours, top_n=5):
    results = []
    for course in COURSES:
        score, reasons = score_course(course, interests, skills, career_goal, study_hours)
        if score > 0:
            results.append({"course": course, "score": score, "reasons": reasons})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]


def build_learning_path(course):
    """Return a simple ordered list of prerequisite course names -> this course."""
    path = list(course["prerequisites"]) + [course["name"]]
    return path


def answer_followup(question, last_recommendations):
    """
    Very simple rule-based follow-up question handler.
    Looks for keywords in the question and answers using the
    already-recommended course data (no external API required).
    """
    q = question.lower()

    if not last_recommendations:
        return "Please get course recommendations first, then ask a follow-up question."

    # Try to find which recommended course the question refers to
    target = None
    for rec in last_recommendations:
        if rec["course"]["name"].lower() in q:
            target = rec
            break

    if "prerequisite" in q or "before" in q:
        if target:
            prereqs = target["course"]["prerequisites"]
            return (f"Prerequisites for {target['course']['name']}: "
                     f"{', '.join(prereqs) if prereqs else 'None'}")
        return "Please mention the exact course name to check its prerequisites."

    if "duration" in q or "how long" in q or "weeks" in q:
        if target:
            c = target["course"]
            return f"{c['name']} takes about {c['duration_weeks']} weeks ({c['hours_per_week']} hrs/week)."
        return "Please mention the exact course name to check its duration."

    if "why" in q:
        if target:
            return "Reasons this was recommended: " + "; ".join(target["reasons"])
        return "Please mention the exact course name you're asking about."

    if "skill" in q or "learn" in q:
        if target:
            gained = target["course"]["skills_gained"]
            return f"Skills you'll gain from {target['course']['name']}: {', '.join(gained)}"
        return "Please mention the exact course name to check the skills covered."

    if "path" in q or "order" in q or "sequence" in q:
        if target:
            path = build_learning_path(target["course"])
            return "Suggested learning path: " + " -> ".join(path)
        return "Please mention the exact course name to see its learning path."

    return ("I can answer questions about prerequisites, duration, skills gained, "
            "or the reason a course was recommended. Please mention the course name, "
            "e.g. \"What are the prerequisites for Machine Learning Basics?\"")


# ---------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------
st.set_page_config(page_title="AI Course Guidance Assistant", page_icon="🎓", layout="centered")

st.title("🎓 AI-Based Course Guidance Assistant")
st.caption("A simple prototype that recommends courses based on your interests, skills, career goal, and available time.")

if "recommendations" not in st.session_state:
    st.session_state.recommendations = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.form("student_form"):
    st.subheader("Tell us about yourself")
    interests_input = st.text_input(
        "Your interests (comma separated)",
        placeholder="e.g. machine learning, web development"
    )
    skills_input = st.text_input(
        "Skills you already have (comma separated, or leave blank)",
        placeholder="e.g. python, html"
    )
    career_goal_input = st.text_input(
        "Career goal",
        placeholder="e.g. data scientist"
    )
    study_hours_input = st.slider(
        "Study time available per week (hours)", min_value=1, max_value=15, value=5
    )
    submitted = st.form_submit_button("Get Course Recommendations")

if submitted:
    interests = split_terms(interests_input)
    skills = split_terms(skills_input)
    career_goal = career_goal_input.strip().lower()

    if not interests and not career_goal:
        st.warning("Please enter at least your interests or a career goal.")
    else:
        recs = recommend_courses(interests, skills, career_goal, study_hours_input)
        st.session_state.recommendations = recs
        st.session_state.chat_history = []  # reset chat for new recommendations

if st.session_state.recommendations:
    st.subheader("Recommended Courses")
    for rec in st.session_state.recommendations:
        c = rec["course"]
        with st.container(border=True):
            st.markdown(f"### {c['name']}  \n*{c['level']} · {c['field']}*")
            st.write(c["description"])
            st.markdown("**Why recommended:**")
            for r in rec["reasons"]:
                st.markdown(f"- {r}")
            path = build_learning_path(c)
            st.markdown(f"**Suggested learning path:** {' → '.join(path)}")
            st.markdown(f"**Duration:** {c['duration_weeks']} weeks · {c['hours_per_week']} hrs/week")

    st.divider()
    st.subheader("💬 Ask a follow-up question")
    st.caption('Example: "What are the prerequisites for Machine Learning Basics?"')

    followup = st.text_input("Your question", key="followup_input")
    if st.button("Ask"):
        if followup.strip():
            answer = answer_followup(followup, st.session_state.recommendations)
            st.session_state.chat_history.append((followup, answer))

    for q, a in reversed(st.session_state.chat_history):
        st.markdown(f"**You:** {q}")
        st.markdown(f"**Assistant:** {a}")

st.divider()
st.info(
    "⚠️ **Limitations:** Recommendations are based on a small, fixed sample dataset and "
    "simple keyword matching — not a trained AI model. Course information may become "
    "outdated, and matches may not always be accurate. Please confirm final course "
    "choices with an academic advisor before enrolling."
)
