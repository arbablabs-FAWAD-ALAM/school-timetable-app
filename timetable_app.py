import streamlit as st
import pandas as pd

st.set_page_config(page_title="Timetable Clash Manager")

# Teachers aur classes ka data
classes = ["1st", "2ND", "3RD", "4th A", "4THB", "5thA", "5th B", "6TH A", "6TH B", "7TH A", "7TH B", "8TH A", "8TH B", "9TH A", "9TH B", "10TH A", "10TH B", "1st year", "2nd year"]
teachers = ["Anum", "Zeenat", "Alishba", "Sadaf", "Mehwish", "Alia", "Shehla", "Musaffa", "Himayat", "Fahad", "Kashif", "Alam Zeb", "Amir", "Raheel", "Haseeba", "Ayesha", "Sumayya", "Nabia", "Haleema", "Niaz", "Atiya", "Sana Ullah", "Shoaib", "Anis", "Zulfiqar", "Jawad"]

# Timetable ka structure memory mein save rakhne ke liye
if "timetable" not in st.session_state:
    st.session_state.timetable = {f"Period {i}": {} for i in range(1, 9)}

st.title("School Timetable Manager")
st.write("Teachers ko manually assign karein baghair kisi clash ke.")

col1, col2, col3 = st.columns(3)
with col1:
    selected_period = st.selectbox("Period Select Karein", list(st.session_state.timetable.keys()))
with col2:
    selected_class = st.selectbox("Class Select Karein", classes)
with col3:
    selected_teacher = st.selectbox("Teacher Select Karein", teachers)

if st.button("Teacher Assign Karein"):
    clash_found = False
    
    # Clash detection logic
    for cls, tchr in st.session_state.timetable[selected_period].items():
        if tchr == selected_teacher:
            st.error(f"❌ CLASH DETECTED! {selected_teacher} pehle hi {selected_period} mein Class {cls} ko padha rahe hain.")
            clash_found = True
            break
    
    if not clash_found:
        st.session_state.timetable[selected_period][selected_class] = selected_teacher
        st.success(f"✅ {selected_teacher} ko {selected_class} ke liye {selected_period} mein assign kar diya gaya.")

st.subheader("Current Live Timetable")
df = pd.DataFrame(st.session_state.timetable)
st.dataframe(df.fillna("-"))