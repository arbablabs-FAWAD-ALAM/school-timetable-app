# 🏫 School Timetable Management System

A Python & Streamlit web application designed for school administration to assign teachers to classes without scheduling conflicts.

## 🚀 Features

- **Strict Teacher Clash Detection**: Automatically checks if a teacher is already booked during the selected period. If booked, it immediately blocks the assignment and displays an alert indicating which class they are already teaching.
- **Predefined Classes & Teachers**:
  - **Classes**: 1st through 10th, 1st Year, and 2nd Year.
  - **Teachers**: Full list of pre-configured faculty members.
  - Dynamic options to add custom teachers or new classes anytime from the UI.
- **Multiple Live Views**:
  - **Master Grid**: Class vs. Period matrix (with options to show Teacher, Subject, or both).
  - **Teacher Schedule View**: Select any teacher to view their personal weekly schedule and workload.
  - **Interactive Schedule Table**: Filterable and searchable table with entry removal.
  - **Free/Busy Checker**: Check which teachers are available or busy during any period.
- **Data Export & Quick Demo**:
  - One-click **Demo Data Loader** to test out the application instantly.
  - Download timetable in CSV format.

---

## 💻 Terminal Commands to Run the App

Open your terminal or PowerShell inside this folder and run:

### 1. Install Required Libraries
```bash
pip install streamlit pandas
```
*(Or `pip install -r requirements.txt`)*

### 2. Launch the Streamlit App
```bash
streamlit run app.py
```

The app will automatically open in your default browser at `http://localhost:8501`.
