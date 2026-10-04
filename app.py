import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="School Timetable Management",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CUSTOM CSS STYLING
# ==========================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px 16px;
        text-align: center;
    }
    .clash-box {
        background-color: #FEE2E2;
        border-left: 5px solid #EF4444;
        padding: 12px;
        border-radius: 4px;
        color: #991B1B;
        font-weight: 500;
        margin-bottom: 15px;
    }
    .success-box {
        background-color: #ECFDF5;
        border-left: 5px solid #10B981;
        padding: 12px;
        border-radius: 4px;
        color: #065F46;
        font-weight: 500;
        margin-bottom: 15px;
    }
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CONSTANTS & DEFAULT DATA
# ==========================================
DEFAULT_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
PERIODS = [f"Period {i}" for i in range(1, 9)]

DEFAULT_CLASSES = [
    "1st", "2nd", "3rd", "4th", "5th", 
    "6th", "7th", "8th", 
    "9th", "9th Girls", 
    "10th", "10th Girls", 
    "1st Year", "2nd Year"
]

DEFAULT_TEACHERS = [
    "Anum", "Zeenat", "Alishba", "Sadaf", "Mehwish", "Alia", 
    "Shehla", "Musaffa", "Himayat", "Fahad", "Kashif", "Alam Zeb", 
    "Amir", "Raheel", "Haseeba", "Ayesha", "Sumayya", "Nabia", 
    "Haleema", "Niaz", "Atiya", "Sana Ullah", "Shoaib", "Anis", 
    "Zulfiqar", "Jawad"
]

DEFAULT_SUBJECTS = [
    "Mathematics", "English", "Urdu", "General Science", 
    "Physics", "Chemistry", "Biology", "Computer Science", 
    "Islamiat", "Pakistan Studies", "Social Studies", "General"
]

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "assignments" not in st.session_state:
    # Stored as list of dicts: {"id": str, "day": str, "period": str, "class": str, "teacher": str, "subject": str}
    st.session_state.assignments = []

# If classes_list is not set or has the old A/B sections, refresh it to the new list
if "classes_list" not in st.session_state or any(c.endswith(" A") or c.endswith(" B") for c in st.session_state.classes_list):
    st.session_state.classes_list = DEFAULT_CLASSES.copy()

if "teachers_list" not in st.session_state:
    st.session_state.teachers_list = sorted(DEFAULT_TEACHERS.copy())

if "subjects_list" not in st.session_state:
    st.session_state.subjects_list = sorted(DEFAULT_SUBJECTS.copy())

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_assignments_df():
    """Returns assignments as a pandas DataFrame."""
    if not st.session_state.assignments:
        return pd.DataFrame(columns=["Day", "Period", "Class", "Teacher", "Subject"])
    
    df = pd.DataFrame(st.session_state.assignments)
    return df[["Day", "Period", "Class", "Teacher", "Subject"]]

def find_teacher_clash(day, period, teacher, current_class=None):
    """
    Checks if a teacher is already assigned during the same day and period
    to ANY other class.
    Returns: dict of clashing assignment or None
    """
    for item in st.session_state.assignments:
        if item["day"] == day and item["period"] == period and item["teacher"] == teacher:
            # If current_class is specified and it's the exact same class, it's an update, not a clash with another class
            if current_class is None or item["class"] != current_class:
                return item
    return None

def find_class_slot(day, period, class_name):
    """
    Checks if a class already has an assigned teacher in this day & period.
    Returns: dict of existing assignment or None
    """
    for item in st.session_state.assignments:
        if item["day"] == day and item["period"] == period and item["class"] == class_name:
            return item
    return None

def add_or_update_assignment(day, period, class_name, teacher, subject, allow_overwrite=False):
    """
    Strict validation and addition of a timetable slot.
    Returns (status: bool, message: str)
    """
    # 1. STRICT TEACHER CLASH DETECTION
    teacher_clash = find_teacher_clash(day, period, teacher, current_class=class_name)
    if teacher_clash:
        msg = (
            f"❌ STRICT CLASH DETECTED! Teacher **{teacher}** is ALREADY assigned to "
            f"**Class {teacher_clash['class']}** during **{period}** on **{day}** "
            f"(Subject: {teacher_clash.get('subject', 'N/A')}). "
            f"A teacher cannot be in two classrooms at the same time!"
        )
        return False, msg

    # 2. CLASS OVERWRITE CHECK
    existing_class_slot = find_class_slot(day, period, class_name)
    if existing_class_slot:
        if not allow_overwrite:
            msg = (
                f"⚠️ **Class {class_name}** already has **{existing_class_slot['teacher']}** "
                f"assigned for **{period}** ({existing_class_slot['subject']}). "
                f"Check 'Allow Overwrite' if you wish to replace this slot."
            )
            return False, msg
        else:
            # Remove old slot
            st.session_state.assignments = [
                x for x in st.session_state.assignments 
                if not (x["day"] == day and x["period"] == period and x["class"] == class_name)
            ]

    # 3. SAVE NEW ASSIGNMENT
    new_entry = {
        "id": f"{day}_{period}_{class_name}",
        "day": day,
        "period": period,
        "class": class_name,
        "teacher": teacher,
        "subject": subject
    }
    st.session_state.assignments.append(new_entry)
    return True, f"✅ Successfully assigned **{teacher}** to **Class {class_name}** for **{period}** ({subject}) on **{day}**."

def load_demo_data():
    """Pre-populates a few non-clashing entries for quick demonstration."""
    sample_data = [
        {"id": "Monday_Period 1_10th", "day": "Monday", "period": "Period 1", "class": "10th", "teacher": "Fahad", "subject": "Mathematics"},
        {"id": "Monday_Period 1_10th Girls", "day": "Monday", "period": "Period 1", "class": "10th Girls", "teacher": "Mehwish", "subject": "Mathematics"},
        {"id": "Monday_Period 1_9th", "day": "Monday", "period": "Period 1", "class": "9th", "teacher": "Kashif", "subject": "Physics"},
        {"id": "Monday_Period 1_8th", "day": "Monday", "period": "Period 1", "class": "8th", "teacher": "Anum", "subject": "English"},
        {"id": "Monday_Period 2_10th", "day": "Monday", "period": "Period 2", "class": "10th", "teacher": "Anum", "subject": "English"},
        {"id": "Monday_Period 2_9th Girls", "day": "Monday", "period": "Period 2", "class": "9th Girls", "teacher": "Zeenat", "subject": "English"},
        {"id": "Monday_Period 2_9th", "day": "Monday", "period": "Period 2", "class": "9th", "teacher": "Fahad", "subject": "Mathematics"},
        {"id": "Monday_Period 3_1st Year", "day": "Monday", "period": "Period 3", "class": "1st Year", "teacher": "Amir", "subject": "Chemistry"},
        {"id": "Monday_Period 4_2nd Year", "day": "Monday", "period": "Period 4", "class": "2nd Year", "teacher": "Alam Zeb", "subject": "Biology"},
        {"id": "Monday_Period 5_10th Girls", "day": "Monday", "period": "Period 5", "class": "10th Girls", "teacher": "Shoaib", "subject": "Computer Science"},
    ]
    st.session_state.assignments = sample_data

# ==========================================
# SIDEBAR: ASSIGNMENT CONTROLS
# ==========================================
with st.sidebar:
    st.title("⚙️ Allocation Panel")
    st.write("Assign teachers to classes with instant clash detection.")
    
    with st.form("assign_form", clear_on_submit=False):
        st.subheader("📝 New Assignment")
        
        sel_day = st.selectbox("1. Select Day", DEFAULT_DAYS, index=0)
        sel_period = st.selectbox("2. Select Period", PERIODS, index=0)
        sel_class = st.selectbox("3. Select Class", st.session_state.classes_list)
        sel_teacher = st.selectbox("4. Select Teacher", st.session_state.teachers_list)
        sel_subject = st.selectbox("5. Select Subject", st.session_state.subjects_list)
        
        allow_overwrite = st.checkbox("Allow Overwrite if Class already has a teacher", value=False)
        
        submit_btn = st.form_submit_button("➕ Assign Teacher", use_container_width=True, type="primary")

    if submit_btn:
        success, message = add_or_update_assignment(
            sel_day, sel_period, sel_class, sel_teacher, sel_subject, allow_overwrite
        )
        if success:
            st.success(message)
        else:
            st.error(message)

    st.divider()
    
    # Quick Tools
    st.subheader("🛠️ Quick Actions")
    col_demo, col_clear = st.columns(2)
    with col_demo:
        if st.button("📥 Load Demo", use_container_width=True, help="Load sample schedule data to test"):
            load_demo_data()
            st.rerun()
    with col_clear:
        if st.button("🗑️ Clear All", use_container_width=True, help="Remove all schedule data"):
            st.session_state.assignments = []
            st.rerun()

# ==========================================
# MAIN INTERFACE
# ==========================================
st.markdown('<div class="main-header">🏫 School Timetable Management System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Automated clash prevention, interactive schedule matrices, and teacher workload monitoring.</div>', unsafe_allow_html=True)

# Top Key Metrics
total_slots = len(st.session_state.assignments)
unique_teachers = len(set(x["teacher"] for x in st.session_state.assignments)) if total_slots > 0 else 0
unique_classes = len(set(x["class"] for x in st.session_state.assignments)) if total_slots > 0 else 0

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Assigned Slots", total_slots)
with m2:
    st.metric("Active Teachers", unique_teachers, f"of {len(st.session_state.teachers_list)}")
with m3:
    st.metric("Classes Scheduled", unique_classes, f"of {len(st.session_state.classes_list)}")
with m4:
    st.metric("Total Periods/Day", len(PERIODS))

st.write("")

# Main Tabs for Navigation
tab_matrix, tab_teacher, tab_records, tab_clash_checker, tab_manage = st.tabs([
    "📅 Master Grid (Class vs Period)",
    "👨‍🏫 Teacher-wise Timetable",
    "📋 Interactive Schedule Table",
    "🔍 Period Free/Busy Checker",
    "⚙️ Manage Teachers & Classes"
])

# ----------------------------------------------------
# TAB 1: MASTER GRID VIEW (Classes x Periods)
# ----------------------------------------------------
with tab_matrix:
    st.subheader("Weekly Class-wise Timetable Grid")
    
    col_day_sel, col_format = st.columns([1, 2])
    with col_day_sel:
        view_day = st.selectbox("Filter Day for Grid:", DEFAULT_DAYS, key="grid_day_select")
    with col_format:
        cell_display_option = st.radio(
            "Cell Display Format:",
            ["Teacher (Subject)", "Teacher Only", "Subject Only"],
            horizontal=True,
            key="cell_format_radio"
        )
    
    # Filter assignments for selected day
    day_assignments = [x for x in st.session_state.assignments if x["day"] == view_day]
    
    # Build Matrix: Rows = Classes, Columns = Periods
    matrix_data = {period: {cls: "-" for cls in st.session_state.classes_list} for period in PERIODS}
    
    for item in day_assignments:
        cls = item["class"]
        period = item["period"]
        teacher = item["teacher"]
        subj = item["subject"]
        
        if cls in st.session_state.classes_list and period in matrix_data:
            if cell_display_option == "Teacher (Subject)":
                matrix_data[period][cls] = f"{teacher} ({subj})"
            elif cell_display_option == "Teacher Only":
                matrix_data[period][cls] = teacher
            else:
                matrix_data[period][cls] = subj

    matrix_df = pd.DataFrame(matrix_data, index=st.session_state.classes_list)
    matrix_df.index.name = "Class"
    
    st.dataframe(
        matrix_df, 
        use_container_width=True, 
        height=450
    )
    
    # Quick CSV Download
    csv_grid = matrix_df.to_csv().encode('utf-8')
    st.download_button(
        label=f"⬇️ Download {view_day} Timetable as CSV",
        data=csv_grid,
        file_name=f"timetable_{view_day.lower()}.csv",
        mime="text/csv"
    )

# ----------------------------------------------------
# TAB 2: TEACHER-WISE TIMETABLE
# ----------------------------------------------------
with tab_teacher:
    st.subheader("Individual Teacher's Routine")
    selected_teacher = st.selectbox("Select Teacher to View Routine:", st.session_state.teachers_list, key="teacher_view_select")
    
    # Filter for this teacher
    teacher_assignments = [x for x in st.session_state.assignments if x["teacher"] == selected_teacher]
    
    col_t1, col_t2 = st.columns([1, 3])
    with col_t1:
        st.markdown(f"### **{selected_teacher}**")
        st.write(f"**Total Assigned Classes:** {len(teacher_assignments)}")
        
        # Breakdown by Day
        if teacher_assignments:
            t_df = pd.DataFrame(teacher_assignments)
            day_counts = t_df['day'].value_counts().rename("Periods")
            st.write("**Classes per day:**")
            st.dataframe(day_counts, use_container_width=True)
        else:
            st.info("No classes currently assigned to this teacher.")
    
    with col_t2:
        # Build Day x Period schedule table for this teacher
        t_matrix = {period: {day: "-" for day in DEFAULT_DAYS} for period in PERIODS}
        for item in teacher_assignments:
            p = item["period"]
            d = item["day"]
            if p in t_matrix and d in t_matrix[p]:
                t_matrix[p][d] = f"Class {item['class']} ({item['subject']})"
        
        t_matrix_df = pd.DataFrame(t_matrix, index=DEFAULT_DAYS)
        t_matrix_df.index.name = "Day"
        st.write("**Full Week Routine:**")
        st.dataframe(t_matrix_df, use_container_width=True)

# ----------------------------------------------------
# TAB 3: INTERACTIVE SCHEDULE TABLE
# ----------------------------------------------------
with tab_records:
    st.subheader("All Scheduled Records")
    
    if st.session_state.assignments:
        all_df = get_assignments_df()
        
        # Search and filters
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            filter_day = st.multiselect("Filter by Day:", DEFAULT_DAYS, default=DEFAULT_DAYS)
        with f_col2:
            filter_class = st.multiselect("Filter by Class:", st.session_state.classes_list, default=[])
        with f_col3:
            filter_teacher = st.multiselect("Filter by Teacher:", st.session_state.teachers_list, default=[])
        
        filtered_df = all_df.copy()
        if filter_day:
            filtered_df = filtered_df[filtered_df["Day"].isin(filter_day)]
        if filter_class:
            filtered_df = filtered_df[filtered_df["Class"].isin(filter_class)]
        if filter_teacher:
            filtered_df = filtered_df[filtered_df["Teacher"].isin(filter_teacher)]
            
        st.dataframe(filtered_df, use_container_width=True)
        
        st.divider()
        st.subheader("🗑️ Delete / Unassign an Entry")
        del_col1, del_col2, del_col3, del_col4 = st.columns(4)
        with del_col1:
            del_day = st.selectbox("Day", DEFAULT_DAYS, key="del_day")
        with del_col2:
            del_period = st.selectbox("Period", PERIODS, key="del_period")
        with del_col3:
            del_class = st.selectbox("Class", st.session_state.classes_list, key="del_class")
        with del_col4:
            st.write("&nbsp;")
            if st.button("❌ Remove Assignment", use_container_width=True):
                init_len = len(st.session_state.assignments)
                st.session_state.assignments = [
                    x for x in st.session_state.assignments
                    if not (x["day"] == del_day and x["period"] == del_period and x["class"] == del_class)
                ]
                if len(st.session_state.assignments) < init_len:
                    st.success(f"Removed assignment for Class {del_class} on {del_day}, {del_period}.")
                    st.rerun()
                else:
                    st.warning("No assignment found for that specific Day, Period, and Class.")
    else:
        st.info("No timetable records currently stored. Use the sidebar to assign teachers or click 'Load Demo'!")

# ----------------------------------------------------
# TAB 4: PERIOD FREE / BUSY CHECKER
# ----------------------------------------------------
with tab_clash_checker:
    st.subheader("Find Available (Free) Teachers")
    st.write("Need to find a substitute or know who is free during a specific period? Check below.")
    
    chk_col1, chk_col2 = st.columns(2)
    with chk_col1:
        chk_day = st.selectbox("Select Day to Inspect", DEFAULT_DAYS, key="chk_day")
    with chk_col2:
        chk_period = st.selectbox("Select Period to Inspect", PERIODS, key="chk_period")
    
    # Identify busy teachers
    busy_records = [
        x for x in st.session_state.assignments 
        if x["day"] == chk_day and x["period"] == chk_period
    ]
    busy_teachers = {x["teacher"]: f"Class {x['class']} ({x['subject']})" for x in busy_records}
    free_teachers = [t for t in st.session_state.teachers_list if t not in busy_teachers]
    
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.markdown(f"#### 🟢 Free / Available Teachers ({len(free_teachers)})")
        if free_teachers:
            st.success(", ".join(free_teachers))
        else:
            st.warning("No teachers are free during this period.")
            
    with res_col2:
        st.markdown(f"#### 🔴 Busy Teachers ({len(busy_teachers)})")
        if busy_teachers:
            busy_df = pd.DataFrame([
                {"Teacher": t, "Assigned To": details} for t, details in busy_teachers.items()
            ])
            st.dataframe(busy_df, use_container_width=True)
        else:
            st.info("All teachers are free during this period.")

# ----------------------------------------------------
# TAB 5: MANAGE TEACHERS & CLASSES
# ----------------------------------------------------
with tab_manage:
    st.subheader("Customize School Master Data")
    
    col_add_t, col_add_c = st.columns(2)
    
    with col_add_t:
        st.markdown("#### 👨‍🏫 Add New Teacher")
        new_teacher_name = st.text_input("Teacher Name (e.g., 'Mr. Tariq')")
        if st.button("Add Teacher"):
            if new_teacher_name.strip():
                if new_teacher_name.strip() not in st.session_state.teachers_list:
                    st.session_state.teachers_list.append(new_teacher_name.strip())
                    st.session_state.teachers_list.sort()
                    st.success(f"Added teacher: {new_teacher_name.strip()}")
                    st.rerun()
                else:
                    st.warning("Teacher already exists in the list.")
            else:
                st.error("Please enter a valid teacher name.")
                
    with col_add_c:
        st.markdown("#### 🏫 Add New Class")
        new_class_name = st.text_input("Class Name (e.g., '3rd B' or 'O-Levels')")
        if st.button("Add Class"):
            if new_class_name.strip():
                if new_class_name.strip() not in st.session_state.classes_list:
                    st.session_state.classes_list.append(new_class_name.strip())
                    st.success(f"Added class: {new_class_name.strip()}")
                    st.rerun()
                else:
                    st.warning("Class already exists in the list.")
            else:
                st.error("Please enter a valid class name.")
    
    st.divider()
    st.markdown("#### 💾 Backup & Export")
    export_df = get_assignments_df()
    full_csv = export_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Complete Timetable (CSV)",
        data=full_csv,
        file_name="complete_school_timetable.csv",
        mime="text/csv",
        use_container_width=True
    )
