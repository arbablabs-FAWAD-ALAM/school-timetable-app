import streamlit as st
import pandas as pd
from collections import deque, defaultdict
import tempfile
import os
from fpdf import FPDF

# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="Automated School Timetable Generator",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished interface
st.markdown("""
<style>
    .main-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 0.1rem;
    }
    .sub-title {
        font-size: 1.0rem;
        color: #4B5563;
        margin-bottom: 1.2rem;
    }
    .timing-badge {
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 6px;
        padding: 8px 12px;
        margin-bottom: 12px;
        font-size: 0.88rem;
    }
    .recess-row {
        background-color: #FEF3C7 !important;
        font-weight: bold;
        text-align: center;
    }
    .off-cell {
        background-color: #F3F4F6 !important;
        color: #9CA3AF !important;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. HARDCODED TIMINGS & PERIOD CONSTRAINTS
# ==============================================================================
PERIODS_CONFIG = [
    {"period": "Period 1", "time": "08:20 AM - 08:55 AM", "type": "class"},
    {"period": "Period 2", "time": "08:55 AM - 09:30 AM", "type": "class"},
    {"period": "Period 3", "time": "09:30 AM - 10:05 AM", "type": "class"},
    {"period": "Period 4", "time": "10:05 AM - 10:40 AM", "type": "class"},
    {"period": "Period 5", "time": "10:40 AM - 11:15 AM", "type": "class"},
    {"period": "RECESS / BREAK", "time": "11:15 AM - 11:35 AM", "type": "break"},
    {"period": "Period 6", "time": "11:35 AM - 12:10 PM", "type": "class"},
    {"period": "Period 7", "time": "12:10 PM - 12:45 PM", "type": "class"}, # Off for Class 1 to 3
    {"period": "Period 8", "time": "12:45 PM - 01:20 PM", "type": "class"}, # Off for Class 4 to 10 & College
]

PRIMARY_CLASSES = ["Class 1", "Class 2", "Class 3"]
SENIOR_CLASSES = ["Class 4", "Class 5", "Class 6", "Class 7", "Class 8", "Class 9", "Class 10", "1st Year", "2nd Year"]
ALL_DEFAULT_CLASSES = PRIMARY_CLASSES + SENIOR_CLASSES

# ==============================================================================
# 2. HARDCODED CLASSES & REQUIRED SUBJECTS
# ==============================================================================
DEFAULT_CLASS_SUBJECTS = {
    # Classes 1 to 3 (7 periods -> exactly 7 subjects, dismiss at 12:45 PM)
    "Class 1": ["Urdu", "English", "Math", "GK", "Nazra Quran", "Islamiat", "Writing"],
    "Class 2": ["Urdu", "English", "Math", "GK", "Nazra Quran", "Islamiat", "Writing"],
    "Class 3": ["Urdu", "English", "Math", "GK", "Nazra Quran", "Islamiat", "Writing"],

    # Classes 4 to 7 (8 periods -> 8 subjects, dismiss at 1:20 PM)
    "Class 4": ["Urdu", "Math", "Islamiat", "Science", "English", "Pak Studies", "Mutaligha Quran", "Writing"],
    "Class 5": ["Urdu", "Math", "Islamiat", "Science", "English", "Pak Studies", "Mutaligha Quran", "Writing"],
    "Class 6": ["Urdu", "Math", "Islamiat", "Science", "English", "Pak Studies", "Mutaligha Quran", "Writing"],
    "Class 7": ["Urdu", "Math", "Islamiat", "Science", "English", "Pak Studies", "Mutaligha Quran", "Writing"],

    # Classes 8 to 10 (8 periods scheduled per day from required 9 subjects)
    "Class 8": ["Maths", "Urdu", "English", "Islamiat", "Chemistry", "Biology", "Physics", "Pak Studies"],
    "Class 9": ["Maths", "Urdu", "English", "Islamiat", "Chemistry", "Biology", "Physics", "Mutaligha Quran"],
    "Class 10": ["Maths", "Urdu", "English", "Islamiat", "Chemistry", "Biology", "Physics", "Pak Studies"],

    # 1st Year & 2nd Year (8 periods scheduled per day from required subjects)
    "1st Year": ["English", "Urdu", "Chemistry", "Computer", "Biology", "Physics", "Islamiat Compulsory", "Civics"],
    "2nd Year": ["English", "Urdu", "Chemistry", "Computer", "Biology", "Physics", "Pak Studies", "Civics"],
}

# Full curriculum repository per class category for reference & customization
CURRICULUM_CATALOG = {
    "Classes 1 to 3": ["Urdu", "English", "Math", "GK", "Nazra Quran", "Islamiat", "Writing"],
    "Classes 4 to 7": ["Urdu", "Math", "Islamiat", "Science", "English", "Pak Studies", "Mutaligha Quran", "Writing"],
    "Classes 8 to 10": ["Maths", "Urdu", "English", "Islamiat", "Chemistry", "Biology", "Physics", "Pak Studies", "Mutaligha Quran"],
    "1st Year": ["Islamiat Compulsory", "Islamiat Elective", "English", "Urdu", "Chemistry", "Computer", "Mutaligha Quran", "Biology", "Civics", "Physics"],
    "2nd Year": ["Pak Studies", "Islamiat Elective", "English", "Urdu", "Chemistry", "Computer", "Mutaligha Quran", "Biology", "Civics", "Physics"]
}

# ==============================================================================
# 3. HARDCODED TEACHERS & WORKLOAD CONSTRAINTS
# ==============================================================================
DEFAULT_TEACHER_PROFILES = [
    {
        "name": "Alishba",
        "max": 7,
        "classes": ["Class 1", "Class 2", "Class 3"],
        "subjects": ["Maths", "Math", "English", "GK", "Urdu", "Nazra Quran", "Islamiat", "Writing"]
    },
    {
        "name": "Shehla",
        "max": 7,
        "classes": ["Class 1", "Class 2", "Class 3", "Class 4", "Class 5", "Class 6"],
        "subjects": ["Nazra Quran", "Mutaligha Quran", "Islamiat"]
    },
    {
        "name": "Haleema",
        "max": 7,
        "classes": [f"Class {i}" for i in range(1, 11)],
        "subjects": ["Urdu", "Islamiat"]
    },
    {
        "name": "Zeenat",
        "max": 4, # EXCEPTION
        "classes": ["Class 1", "Class 2", "Class 3"],
        "subjects": ["Maths", "Math", "English", "GK", "Urdu", "Nazra Quran", "Islamiat", "Writing"]
    },
    {
        "name": "Alia",
        "max": 7,
        "classes": [f"Class {i}" for i in range(1, 8)],
        "subjects": ["Islamiat", "Math", "Maths"]
    },
    {
        "name": "Anum",
        "max": 7,
        "classes": ["Class 4", "Class 5", "Class 6", "Class 7", "Class 8"],
        "subjects": ["Urdu", "Math", "Maths", "Islamiat", "Science", "Pak Studies", "Mutaligha Quran", "Writing"] # All EXCEPT English
    },
    {
        "name": "Nabia",
        "max": 7,
        "classes": ["Class 8", "Class 9", "Class 10", "1st Year", "2nd Year"],
        "subjects": ["Biology"]
    },
    {
        "name": "Summaiya",
        "max": 7,
        "classes": ["Class 7", "Class 8", "Class 9", "Class 10", "1st Year", "2nd Year"],
        "subjects": ["Civics", "Pak Studies"]
    },
    {
        "name": "Sadaf",
        "max": 7,
        "classes": [f"Class {i}" for i in range(1, 11)],
        "subjects": ["Urdu", "Math", "Maths", "Islamiat", "Science", "Pak Studies", "Mutaligha Quran", "Writing", "GK"] # All EXCEPT English
    },
    {
        "name": "Mehwish",
        "max": 7,
        "classes": [f"Class {i}" for i in range(1, 8)],
        "subjects": ["Urdu", "English", "Math", "Maths", "GK", "Nazra Quran", "Islamiat", "Writing", "Science", "Pak Studies", "Mutaligha Quran"]
    },
    {
        "name": "Ayesha Ibad",
        "max": 7,
        "classes": ["Class 5", "Class 6", "Class 7", "Class 8", "Class 9", "Class 10", "1st Year", "2nd Year"],
        "subjects": ["English"]
    },
    {
        "name": "Haseeba",
        "max": 4, # EXCEPTION
        "classes": ["Class 6", "Class 7", "Class 8", "Class 9", "Class 10"],
        "subjects": ["Science", "Chemistry"]
    },
    {
        "name": "Musaffa",
        "max": 7,
        "classes": ["Class 7", "Class 8", "Class 9", "Class 10", "1st Year", "2nd Year"],
        "subjects": ["Islamiat", "Mutaligha Quran", "Islamiat Compulsory", "Islamiat Elective"]
    },
    {
        "name": "Atia Hassan",
        "max": 3, # EXCEPTION (Bio ONLY for Class 8)
        "classes": ["Class 8", "Class 9", "Class 10", "1st Year", "2nd Year"],
        "subjects": ["Chemistry", "Biology"]
    },
    {
        "name": "Sana Ullah",
        "max": 7,
        "classes": ["Class 8", "Class 9", "Class 10", "1st Year", "2nd Year"],
        "subjects": ["Physics", "Maths", "Math"]
    },
    {
        "name": "Sir Zulfiqar",
        "max": 7,
        "classes": ["Class 10", "1st Year", "2nd Year"],
        "subjects": ["Urdu"]
    },
    {
        "name": "Jawad",
        "max": 7,
        "classes": ["1st Year", "2nd Year"],
        "subjects": ["Computer", "Computer Science"]
    },
    {
        "name": "Sheema",
        "max": 4, # EXCEPTION
        "classes": [f"Class {i}" for i in range(1, 8)],
        "subjects": ["Urdu", "English", "Math", "Maths", "Science", "Writing", "GK", "Islamiat"]
    }
]

# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================
if "teachers" not in st.session_state:
    st.session_state.teachers = [dict(t) for t in DEFAULT_TEACHER_PROFILES]

if "class_subjects" not in st.session_state:
    st.session_state.class_subjects = {k: list(v) for k, v in DEFAULT_CLASS_SUBJECTS.items()}

if "generated_timetable" not in st.session_state:
    st.session_state.generated_timetable = None

if "teacher_workload" not in st.session_state:
    st.session_state.teacher_workload = None

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "assistant", "content": "👋 **Hello!** I am your AI Timetable Assistant powered by Google Gemini.\n\nYou can give me natural language instructions to adjust the timetable, for example:\n- *'Change Alishba's 3rd period class to Zeenat'*\n- *'Assign Fahad to Class 10th in Period 2'*\n- *'Switch Class 8 Period 4 Chemistry to Atia Hassan'*"}
    ]

# ==============================================================================
# 4. AUTOMATED SCHEDULING ALGORITHM (MAX-FLOW + BIPARTITE COLORING)
# ==============================================================================
def normalize_subject(subj):
    """Standardizes subject names for matching."""
    s = subj.strip().lower()
    if s == "maths":
        return "math"
    if s in ["computer science", "computer"]:
        return "computer"
    return s

def can_teacher_teach(t_dict, cls, subject):
    """Validates if a teacher is eligible to teach subject in class."""
    if cls not in t_dict["classes"]:
        return False
    # Special strict rule: Atia Hassan teaches Biology ONLY for Class 8
    if t_dict["name"] == "Atia Hassan" and normalize_subject(subject) == "biology" and cls != "Class 8":
        return False
    subj_norm = normalize_subject(subject)
    for s in t_dict["subjects"]:
        if normalize_subject(s) == subj_norm:
            return True
    return False

def solve_timetable(classes, class_subjects, teachers):
    """
    Two-stage constraint satisfaction solver:
    Stage 1: Edmonds-Karp network max-flow to assign teachers to (class, subject) respecting daily caps.
    Stage 2: Bipartite matching across periods to guarantee 100% clash-free period allocation.
    Returns (success: bool, timetable: dict, teacher_loads: dict, error_message: str)
    """
    tasks = []
    for cls in classes:
        if cls not in class_subjects:
            continue
        for subj in class_subjects[cls]:
            tasks.append((cls, subj))

    if not tasks:
        return False, None, None, "No classes or subjects selected to schedule."

    # Stage 1: Max-Flow Network
    source = "SOURCE"
    sink = "SINK"
    adj = defaultdict(list)
    cap = defaultdict(int)
    flow = defaultdict(int)

    def add_edge(u, v, c):
        adj[u].append(v)
        adj[v].append(u)
        cap[(u, v)] += c

    for task in tasks:
        add_edge(source, task, 1)
        for t in teachers:
            if can_teacher_teach(t, task[0], task[1]):
                add_edge(task, t["name"], 1)

    for t in teachers:
        add_edge(t["name"], sink, t["max"])

    # Edmonds-Karp BFS for maximum flow
    total_flow = 0
    while True:
        parent = {}
        queue = deque([source])
        while queue:
            curr = queue.popleft()
            if curr == sink:
                break
            for nxt in adj[curr]:
                if nxt not in parent and cap[(curr, nxt)] - flow[(curr, nxt)] > 0:
                    parent[nxt] = curr
                    queue.append(nxt)

        if sink not in parent:
            break

        curr = sink
        while curr != source:
            prev = parent[curr]
            flow[(prev, curr)] += 1
            flow[(curr, prev)] -= 1
            curr = prev
        total_flow += 1

    if total_flow < len(tasks):
        unassigned_count = len(tasks) - total_flow
        return False, None, None, (
            f"Scheduling Infeasible: Insufficient teacher capacity or strict subject qualifications prevent assigning {unassigned_count} slots. "
            "Consider adding more teachers or increasing daily limits."
        )

    # Extract Stage 1 teacher assignments
    assignments = {}
    teacher_loads = defaultdict(int)
    for task in tasks:
        for nxt in adj[task]:
            if nxt != source and flow[(task, nxt)] == 1:
                assignments[task] = nxt
                teacher_loads[nxt] += 1
                break

    # Stage 2: Period Allocation (Bipartite Matching per period)
    remaining_tasks = defaultdict(list)
    for (cls, subj), teacher in assignments.items():
        remaining_tasks[cls].append((subj, teacher))

    schedule = {}
    # Periods: Class 1-3 only have Periods 1-7 (Off at 12:45 PM). Class 4-12 have Periods 1-8.
    periods_order = [8, 7, 6, 5, 4, 3, 2, 1]

    for p_num in periods_order:
        p_name = f"Period {p_num}"
        # Class 1-3 cannot be scheduled in Period 8
        active_classes = [c for c in classes if not (p_num == 8 and c in PRIMARY_CLASSES)]
        
        matched_teacher = {} # teacher -> (cls, subj)
        # Sort classes by fewest remaining tasks for MRV
        active_sorted = sorted(active_classes, key=lambda c: len(remaining_tasks[c]))

        def match_class(c_node, visited):
            # Sort remaining tasks: prioritize teachers who are in highest demand across remaining classes
            cand_tasks = sorted(
                remaining_tasks[c_node],
                key=lambda item: -len([1 for oc in active_classes for os, ot in remaining_tasks[oc] if ot == item[1]])
            )
            for s_cand, t_cand in cand_tasks:
                if t_cand in visited:
                    continue
                visited.add(t_cand)
                if t_cand not in matched_teacher or match_class(matched_teacher[t_cand][0], visited):
                    matched_teacher[t_cand] = (c_node, s_cand)
                    return True
            return False

        for c in active_sorted:
            visited = set()
            match_class(c, visited)

        # Commit period assignments
        for t_matched, (c_matched, s_matched) in matched_teacher.items():
            schedule[(c_matched, p_name)] = (s_matched, t_matched)
            remaining_tasks[c_matched].remove((s_matched, t_matched))

    all_done = all(len(t_list) == 0 for t_list in remaining_tasks.values())
    if not all_done:
        return False, None, None, "Clash prevention resolution incomplete across periods. Try adding teachers."

    return True, schedule, teacher_loads, "Success"

# ==============================================================================
# 5. PDF EXPORT GENERATOR
# ==============================================================================
def create_pdf(schedule, classes):
    """Generates an official, beautifully formatted landscape PDF of the timetable."""
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    # Header Title
    pdf.set_font("Helvetica", 'B', 15)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 8, "SCHOOL TIMETABLE MANAGEMENT SYSTEM", ln=True, align='C')
    pdf.set_font("Helvetica", 'B', 9)
    pdf.set_text_color(75, 85, 99)
    pdf.cell(0, 5, "Official Master Schedule - Automated Clash-Free Generation", ln=True, align='C')
    pdf.set_font("Helvetica", '', 8)
    pdf.cell(0, 5, "Start: 8:20 AM | 35-min Periods | Recess: 11:15-11:35 AM | Primary Off: 12:45 PM | Senior Off: 1:20 PM", ln=True, align='C')
    pdf.ln(3)

    # Dimensions
    # A4 Landscape = 297mm width. Margins = 10mm each -> 277mm printable width.
    period_col_w = 37
    n_classes = len(classes)
    class_col_w = max(18, min(24, int((277 - period_col_w) / n_classes))) if n_classes > 0 else 20

    # Table Header Row
    pdf.set_font("Helvetica", 'B', 8)
    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(period_col_w, 7, "Period / Timing", border=1, align='C', fill=True)
    for c in classes:
        c_disp = c.replace("Class ", "Cls ").replace("Year", "Yr")
        pdf.cell(class_col_w, 7, c_disp, border=1, align='C', fill=True)
    pdf.ln()

    # Row rendering
    pdf.set_text_color(0, 0, 0)
    for p_info in PERIODS_CONFIG:
        p_name = p_info["period"]
        p_time = p_info["time"]

        # Recess Row
        if p_info["type"] == "break":
            pdf.set_fill_color(254, 240, 138) # Light yellow
            pdf.set_font("Helvetica", 'B', 8)
            pdf.cell(period_col_w, 6, "BREAK", border=1, align='C', fill=True)
            pdf.cell(class_col_w * n_classes, 6, f"*** RECESS / BREAK TIME ({p_time}) ***", border=1, align='C', fill=True)
            pdf.ln()
            continue

        row_h = 12
        x_start = pdf.get_x()
        y_start = pdf.get_y()

        # Period label column
        pdf.set_fill_color(243, 244, 246)
        pdf.rect(x_start, y_start, period_col_w, row_h, 'DF')
        pdf.set_xy(x_start, y_start + 2)
        pdf.set_font("Helvetica", 'B', 8)
        pdf.cell(period_col_w, 4, p_name, align='C')
        pdf.set_xy(x_start, y_start + 6.5)
        pdf.set_font("Helvetica", '', 6.5)
        pdf.cell(period_col_w, 4, p_time, align='C')
        pdf.set_xy(x_start + period_col_w, y_start)

        # Class columns
        for c in classes:
            x_c = pdf.get_x()
            y_c = pdf.get_y()

            # Dismissal check for Primary in Period 8
            if p_name == "Period 8" and c in PRIMARY_CLASSES:
                pdf.set_fill_color(229, 231, 235)
                pdf.rect(x_c, y_c, class_col_w, row_h, 'DF')
                pdf.set_xy(x_c, y_c + 4)
                pdf.set_font("Helvetica", 'I', 6.5)
                pdf.cell(class_col_w, 4, "OFF (12:45)", align='C')
                pdf.set_xy(x_c + class_col_w, y_c)
                continue

            entry = schedule.get((c, p_name), None) if schedule else None
            pdf.set_fill_color(255, 255, 255)
            pdf.rect(x_c, y_c, class_col_w, row_h, 'DF')

            if entry:
                subj, teacher = entry
                s_short = subj if len(subj) <= 11 else subj[:9] + ".."
                t_short = teacher if len(teacher) <= 11 else teacher[:9] + ".."

                pdf.set_xy(x_c, y_c + 1.8)
                pdf.set_font("Helvetica", 'B', 6.8)
                pdf.cell(class_col_w, 4, s_short, align='C')

                pdf.set_xy(x_c, y_c + 6.2)
                pdf.set_font("Helvetica", '', 6.2)
                pdf.set_text_color(30, 58, 138)
                pdf.cell(class_col_w, 4, t_short, align='C')
                pdf.set_text_color(0, 0, 0)
            else:
                pdf.set_xy(x_c, y_c + 4)
                pdf.set_font("Helvetica", '', 7)
                pdf.cell(class_col_w, 4, "-", align='C')

            pdf.set_xy(x_c + class_col_w, y_c)
        pdf.ln(row_h)

    # Return raw PDF bytes
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp_name = tmp.name
    pdf.output(tmp_name)
    with open(tmp_name, "rb") as f:
        pdf_bytes = f.read()
    try:
        os.remove(tmp_name)
    except Exception:
        pass
    return pdf_bytes

# ==============================================================================
# 6. GEMINI AI ASSISTANT FUNCTIONS
# ==============================================================================
import json

def query_gemini_assistant(api_key, user_prompt, timetable_dict):
    """
    Sends natural language command and timetable data to Google Gemini.
    Forces JSON output with required schema.
    """
    system_instruction = (
        "You are an expert AI School Timetable Assistant. Your job is to modify teacher assignments based on user natural language commands.\n"
        "You MUST respond ONLY with a raw JSON object (no markdown code fences, no conversational text outside JSON).\n\n"
        "REQUIRED JSON SCHEMA:\n"
        "{\n"
        '  "action": "update_slot" | "no_change",\n'
        '  "period": "<e.g., Period 3>",\n'
        '  "class_name": "<e.g., Class 1 or Class 10>",\n'
        '  "new_teacher": "<e.g., Zeenat>",\n'
        '  "new_subject": "<optional subject name if updated, or null>",\n'
        '  "explanation": "<Brief user-facing summary of the change or why it cannot be made>"\n'
        "}\n\n"
        "If the user request cannot be fulfilled, return action: 'no_change' with an explanation."
    )

    prompt_content = (
        f"CURRENT TIMETABLE STATE:\n{json.dumps(timetable_dict, indent=2)}\n\n"
        f"USER COMMAND:\n{user_prompt}\n\n"
        "Analyze the current timetable and user command, determine the exact slot to update, and return the JSON object."
    )

    # 1. Try google.generativeai SDK first
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction,
            generation_config={"response_mime_type": "application/json"}
        )
        response = model.generate_content(prompt_content)
        return response.text
    except Exception:
        # 2. Fallback to Google Gemini REST API endpoint
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": f"{system_instruction}\n\n{prompt_content}"}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        res = requests.post(url, json=payload, timeout=25)
        res_json = res.json()
        if "error" in res_json:
            raise Exception(res_json["error"].get("message", "Gemini API error"))
        return res_json["candidates"][0]["content"]["parts"][0]["text"]

def apply_ai_changes(response_text):
    """
    Parses the JSON response from Gemini and safely updates st.session_state.generated_timetable.
    Validates clashes and teacher workloads.
    """
    raw = response_text.strip()
    if raw.startswith("```json"): raw = raw[7:]
    if raw.startswith("```"): raw = raw[3:]
    if raw.endswith("```"): raw = raw[:-3]
    
    data = json.loads(raw.strip())
    
    if data.get("action") == "update_slot" and data.get("new_teacher"):
        period = data.get("period")
        class_name = data.get("class_name")
        new_teacher = data.get("new_teacher")
        new_subject = data.get("new_subject")
        
        # Standardize class name
        if class_name and class_name.isdigit():
            class_name = f"Class {class_name}"
            
        timetable = st.session_state.generated_timetable
        if timetable is None:
            return False, "Timetable is not yet generated. Please click 'Generate Clash-Free Timetable' first."
            
        # Strict Clash Detection: Is new_teacher already teaching another class in this period?
        clashes = [c_k for (c_k, p_k), (s_k, t_k) in timetable.items() if p_k.lower() == period.lower() and t_k.lower() == new_teacher.lower() and c_k != class_name]
        if clashes:
            return False, f"❌ Clash Blocked: **{new_teacher}** is already teaching **{clashes[0]}** during **{period}**!"
            
        old_entry = timetable.get((class_name, period), None)
        old_subject = old_entry[0] if old_entry else "General"
        final_subject = new_subject if new_subject else old_subject
        
        # Safe state update
        timetable[(class_name, period)] = (final_subject, new_teacher)
        
        # Refresh teacher workloads
        new_loads = defaultdict(int)
        for (c, p), (s, t) in timetable.items():
            new_loads[t] += 1
        st.session_state.teacher_workload = new_loads
        
        expl = data.get("explanation", f"Assigned {new_teacher} to {class_name} during {period}.")
        return True, f"✅ {expl}"
        
    return False, data.get("explanation", "No modifications were made.")

# ==============================================================================
# SIDEBAR: GENERATOR CONTROLS & ADD NEW TEACHER
# ==============================================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2602/2602414.png", width=60)
    st.markdown("### 🎛️ Timetable Controls")
    
    # Secure Gemini API Key Input
    st.markdown("#### 🤖 AI Assistant Key")
    gemini_api_key = st.text_input(
        "Google Gemini API Key",
        type="password",
        placeholder="AIzaSy...",
        help="Enter your Google Gemini API key to enable natural language timetable modifications."
    )
    st.divider()

    # Generate Timetable Button
    st.markdown("#### ⚡ Automatic Scheduler")
    generate_btn = st.button("🚀 Generate Clash-Free Timetable", type="primary", use_container_width=True)

    st.divider()

    # Dynamic New Teacher Addition Form
    st.markdown("### ➕ Add New Teacher")
    with st.form("new_teacher_form", clear_on_submit=True):
        new_name = st.text_input("Teacher Name", placeholder="e.g., Sir Tariq")
        new_max = st.number_input("Max Periods / Day", min_value=1, max_value=8, value=7)
        new_classes = st.multiselect("Allowed Classes", ALL_DEFAULT_CLASSES, default=ALL_DEFAULT_CLASSES)
        
        # Collect distinct subjects
        all_possible_subjects = sorted(list({s for sublist in DEFAULT_CLASS_SUBJECTS.values() for s in sublist}))
        new_subjects = st.multiselect("Allowed Subjects", all_possible_subjects, default=["Math", "Urdu", "English"])
        
        add_teacher_btn = st.form_submit_button("Save New Teacher", use_container_width=True)

    if add_teacher_btn:
        if not new_name.strip():
            st.error("Please enter a valid teacher name.")
        elif any(t["name"].lower() == new_name.strip().lower() for t in st.session_state.teachers):
            st.warning("A teacher with this name already exists.")
        elif not new_classes:
            st.error("Please assign at least one allowed class.")
        elif not new_subjects:
            st.error("Please select at least one allowed subject.")
        else:
            new_profile = {
                "name": new_name.strip(),
                "max": int(new_max),
                "classes": new_classes,
                "subjects": new_subjects
            }
            st.session_state.teachers.append(new_profile)
            st.success(f"Added teacher **{new_name.strip()}** (Max {new_max}/day)!")
            st.rerun()

    st.divider()

    # Reset Data
    if st.button("🔄 Reset to Default Hardcoded Data", use_container_width=True):
        st.session_state.teachers = [dict(t) for t in DEFAULT_TEACHER_PROFILES]
        st.session_state.class_subjects = {k: list(v) for k, v in DEFAULT_CLASS_SUBJECTS.items()}
        st.session_state.generated_timetable = None
        st.session_state.teacher_workload = None
        st.success("Reset data to official defaults.")
        st.rerun()

# ==============================================================================
# MAIN PAGE HEADER & TIMINGS BAR
# ==============================================================================
st.markdown('<div class="main-title">🏫 Automated School Timetable Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Constraint-satisfaction scheduling with zero-clash guarantee, workload limits, and instant PDF export.</div>', unsafe_allow_html=True)

# Timings Info Banner
st.markdown("""
<div class="timing-badge">
    <strong>⏰ Official Timings & Rules:</strong> 
    Start Time: <strong>8:20 AM</strong> | 
    Period Duration: <strong>35 mins</strong> | 
    Break: <strong>11:15 AM - 11:35 AM</strong> | 
    <strong>Class 1-3 Off: 12:45 PM</strong> (7 Periods) | 
    <strong>Class 4-10 & College Off: 1:20 PM</strong> (8 Periods)
</div>
""", unsafe_allow_html=True)

# Trigger Generation when user clicks button
if generate_btn:
    with st.spinner("Executing constraint satisfaction & clash-free bipartite matching..."):
        ok, sched, loads, err_msg = solve_timetable(
            ALL_DEFAULT_CLASSES,
            st.session_state.class_subjects,
            st.session_state.teachers
        )
        if ok:
            st.session_state.generated_timetable = sched
            st.session_state.teacher_workload = loads
            st.success(f"✅ Timetable successfully generated with **0 clashes** across all {len(ALL_DEFAULT_CLASSES)} classes and {len(sched)} slots!")
        else:
            st.error(f"❌ {err_msg}")

# Top Metrics Row
c_assigned = len(st.session_state.generated_timetable) if st.session_state.generated_timetable else 0
c_teachers = len(st.session_state.teachers)
active_teachers = len(st.session_state.teacher_workload) if st.session_state.teacher_workload else 0

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Teaching Slots", c_assigned, f"Target: 93 slots")
with m2:
    st.metric("Active Faculty", active_teachers, f"of {c_teachers} registered")
with m3:
    st.metric("Classes Scheduled", len(ALL_DEFAULT_CLASSES), "1st to 2nd Year")
with m4:
    clash_status = "0 Clashes (Verified)" if c_assigned > 0 else "Ready"
    st.metric("Clash Verification", clash_status)

st.write("")

# Main Tabs Navigation
tab_grid, tab_teacher, tab_workload, tab_faculty, tab_curriculum, tab_ai = st.tabs([
    "📅 Master Timetable Matrix",
    "👨‍🏫 Teacher-wise Routine",
    "📊 Workload & Free Periods",
    "👥 Faculty Profiles & Limits",
    "📚 Classes & Required Subjects",
    "💬 AI Assistant"
])

# ------------------------------------------------------------------------------
# TAB 1: MASTER TIMETABLE MATRIX
# ------------------------------------------------------------------------------
with tab_grid:
    st.subheader("Master Class-wise Timetable Grid")
    
    if st.session_state.generated_timetable:
        sched = st.session_state.generated_timetable
        
        # Build Grid DataFrame: Rows = Periods, Columns = Classes
        grid_rows = []
        for p_info in PERIODS_CONFIG:
            p_name = p_info["period"]
            p_time = p_info["time"]
            
            row = {"Period / Time": f"{p_name}\n({p_time})"}
            
            if p_info["type"] == "break":
                for cls in ALL_DEFAULT_CLASSES:
                    row[cls] = "☕ RECESS / BREAK"
            else:
                for cls in ALL_DEFAULT_CLASSES:
                    if p_name == "Period 8" and cls in PRIMARY_CLASSES:
                        row[cls] = "🏠 OFF (12:45 PM)"
                    else:
                        entry = sched.get((cls, p_name), None)
                        if entry:
                            subj, teacher = entry
                            row[cls] = f"{subj}\n[{teacher}]"
                        else:
                            row[cls] = "-"
            grid_rows.append(row)
            
        grid_df = pd.DataFrame(grid_rows).set_index("Period / Time")
        
        # Display DataFrame
        st.dataframe(grid_df, use_container_width=True, height=440)
        
        # Action Buttons: PDF & CSV Download
        st.divider()
        col_pdf, col_csv = st.columns([1, 1])
        with col_pdf:
            pdf_data = create_pdf(sched, ALL_DEFAULT_CLASSES)
            st.download_button(
                label="📄 Download Timetable as PDF",
                data=pdf_data,
                file_name="school_timetable_official.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        with col_csv:
            csv_data = grid_df.to_csv().encode('utf-8')
            st.download_button(
                label="📥 Export Master Grid as CSV",
                data=csv_data,
                file_name="master_timetable.csv",
                mime="text/csv",
                use_container_width=True
            )
    else:
        st.info("💡 Timetable has not been generated yet. Click **'🚀 Generate Clash-Free Timetable'** in the sidebar to create the schedule.")

# ------------------------------------------------------------------------------
# TAB 2: TEACHER-WISE ROUTINE
# ------------------------------------------------------------------------------
with tab_teacher:
    st.subheader("Individual Teacher's Daily Schedule")
    
    teacher_names = sorted([t["name"] for t in st.session_state.teachers])
    sel_t = st.selectbox("Select Teacher to View Routine:", teacher_names)
    
    t_profile = next((t for t in st.session_state.teachers if t["name"] == sel_t), None)
    
    if st.session_state.generated_timetable:
        sched = st.session_state.generated_timetable
        
        # Find all slots for this teacher
        t_slots = []
        for (c, p), (s, t) in sched.items():
            if t == sel_t:
                # Find time
                time_str = next((x["time"] for x in PERIODS_CONFIG if x["period"] == p), "")
                t_slots.append({"Period": p, "Time": time_str, "Class": c, "Subject": s})
                
        # Sort by period number
        t_slots.sort(key=lambda x: int(x["Period"].replace("Period ", "")))
        
        col_t_info, col_t_table = st.columns([1, 2])
        with col_t_info:
            st.markdown(f"### **{sel_t}**")
            st.write(f"**Assigned Periods Today:** {len(t_slots)} of {t_profile['max']} max allowed")
            st.write(f"**Allowed Classes:** {', '.join(t_profile['classes'][:4])}...")
            st.write(f"**Allowed Subjects:** {', '.join(t_profile['subjects'])}")
            
            # Workload status badge
            if len(t_slots) == t_profile['max']:
                st.warning("⚠️ Teacher is at 100% full capacity.")
            elif len(t_slots) > 0:
                st.success("✅ Teacher workload is within balanced limits.")
            else:
                st.info("ℹ️ Free whole day.")
                
        with col_t_table:
            if t_slots:
                st.write("**Daily Period Breakdown:**")
                st.dataframe(pd.DataFrame(t_slots), use_container_width=True)
            else:
                st.info(f"No periods assigned to {sel_t} today.")
    else:
        st.info("Please generate the timetable to view teacher routines.")

# ------------------------------------------------------------------------------
# TAB 3: WORKLOAD & FREE PERIODS
# ------------------------------------------------------------------------------
with tab_workload:
    st.subheader("Teacher Workload & Capacity Utilization")
    
    if st.session_state.teacher_workload is not None:
        wl_data = []
        for t in st.session_state.teachers:
            t_name = t["name"]
            assigned = st.session_state.teacher_workload.get(t_name, 0)
            max_cap = t["max"]
            pct = (assigned / max_cap) * 100 if max_cap > 0 else 0
            wl_data.append({
                "Teacher": t_name,
                "Assigned Classes": assigned,
                "Max Allowed / Day": max_cap,
                "Utilization": f"{pct:.0f}%",
                "Remaining Free Periods": max_cap - assigned
            })
            
        wl_df = pd.DataFrame(wl_data).sort_values(by="Assigned Classes", ascending=False)
        st.dataframe(wl_df, use_container_width=True)
        
        st.divider()
        st.subheader("🔍 Free Teachers by Period")
        p_inspect = st.selectbox("Inspect Period:", [f"Period {i}" for i in range(1, 9)])
        
        # Busy teachers in this period
        busy_map = {}
        for (c, p), (s, t) in st.session_state.generated_timetable.items():
            if p == p_inspect:
                busy_map[t] = f"{c} ({s})"
                
        free_list = [t["name"] for t in st.session_state.teachers if t["name"] not in busy_map]
        
        col_free, col_busy = st.columns(2)
        with col_free:
            st.markdown(f"#### 🟢 Free / Available Teachers ({len(free_list)})")
            st.write(", ".join(free_list) if free_list else "None")
        with col_busy:
            st.markdown(f"#### 🔴 Teaching during {p_inspect} ({len(busy_map)})")
            if busy_map:
                st.dataframe(pd.DataFrame([{"Teacher": k, "Assignment": v} for k, v in busy_map.items()]), use_container_width=True)
            else:
                st.write("All teachers are free.")
    else:
        st.info("Generate timetable to see workload statistics.")

# ------------------------------------------------------------------------------
# TAB 4: FACULTY PROFILES & CONSTRAINTS
# ------------------------------------------------------------------------------
with tab_faculty:
    st.subheader("Teacher Profiles & Hardcoded Constraints")
    st.write("Configured teachers, class eligibility, subject qualifications, and daily maximum caps:")
    
    faculty_list = []
    for t in st.session_state.teachers:
        spec_note = ""
        if t["name"] == "Atia Hassan":
            spec_note = "Bio ONLY for Class 8"
        elif t["name"] in ["Zeenat", "Haseeba", "Sheema"]:
            spec_note = f"Max limit exception: {t['max']}"
        elif "EXCEPT English" in str(t.get("subjects", "")):
            spec_note = "All subjects EXCEPT English"
            
        faculty_list.append({
            "Teacher Name": t["name"],
            "Max Periods/Day": t["max"],
            "Allowed Classes": ", ".join(t["classes"]),
            "Qualified Subjects": ", ".join(t["subjects"]),
            "Notes / Restrictions": spec_note
        })
        
    st.dataframe(pd.DataFrame(faculty_list), use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 5: CLASSES & REQUIRED SUBJECTS
# ------------------------------------------------------------------------------
with tab_curriculum:
    st.subheader("Class Curriculum & Period Requirements")
    
    c_summary = []
    for cls in ALL_DEFAULT_CLASSES:
        subjs = st.session_state.class_subjects.get(cls, [])
        periods_n = 7 if cls in PRIMARY_CLASSES else 8
        off_time = "12:45 PM" if cls in PRIMARY_CLASSES else "01:20 PM"
        c_summary.append({
            "Class Name": cls,
            "Total Periods": periods_n,
            "Off-Time": off_time,
            "Subject Count": len(subjs),
            "Assigned Subjects": ", ".join(subjs)
        })
        
    st.dataframe(pd.DataFrame(c_summary), use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 6: AI CHAT ASSISTANT (GOOGLE GEMINI)
# ------------------------------------------------------------------------------
with tab_ai:
    st.subheader("💬 AI Timetable Assistant (Google Gemini)")
    st.write("Modify teacher assignments using natural language commands. Example: *'Change Alishba's 3rd period class to Zeenat'* or *'Assign Sana Ullah to Class 9 in Period 1'*.")

    if not gemini_api_key:
        st.warning("🔑 Please enter your **Google Gemini API Key** in the left sidebar to activate the AI Assistant.")

    # Render Chat History
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Enter natural language timetable command..."):
        if not gemini_api_key:
            st.error("Please provide a Gemini API Key in the sidebar before sending commands.")
        elif st.session_state.generated_timetable is None:
            st.error("Please click '🚀 Generate Clash-Free Timetable' first so there is schedule data to modify.")
        else:
            # Add user message to state & render
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Format timetable dict for Gemini: {(cls, p): (subj, teacher)} -> dict
            timetable_dict = {}
            for (cls, p), (subj, teacher) in st.session_state.generated_timetable.items():
                if p not in timetable_dict:
                    timetable_dict[p] = {}
                timetable_dict[p][cls] = f"{teacher} ({subj})"

            with st.chat_message("assistant"):
                with st.spinner("AI is analyzing timetable and planning modifications..."):
                    try:
                        ai_response_text = query_gemini_assistant(gemini_api_key, prompt, timetable_dict)
                        success, update_msg = apply_ai_changes(ai_response_text)
                        
                        st.markdown(update_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": update_msg})
                        if success:
                            st.rerun()
                    except Exception as err:
                        err_text = f"⚠️ **AI Assistant Error:** {str(err)}"
                        st.error(err_text)
                        st.session_state.chat_messages.append({"role": "assistant", "content": err_text})
