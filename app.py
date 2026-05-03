import streamlit as st
import sqlite3
from model.patient import Patient
from model.doctor import Doctor
from model.billing import Billing
from model.facility import Facility
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# Page Configuration
st.set_page_config(
    page_title="Medicare Hospital",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Minimal Simple CSS
st.markdown("""
    <style>
    h1, h2, h3 { color: #0066cc; }
    body { font-family: Arial, sans-serif; }
    .stButton>button { background-color: #0066cc; color: white; border: none; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# Header
st.markdown("<h1>🏥 Medicare Hospital</h1>", unsafe_allow_html=True)

# Database Setup
conn = sqlite3.connect('hospital.db')
cursor = conn.cursor()

# Initialize Tables

def get_table_columns(table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def recreate_table_if_needed(table_name, create_sql, expected_columns):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if not cursor.fetchone():
        cursor.execute(create_sql)
        return

    columns = get_table_columns(table_name)
    if set(columns) == set(expected_columns):
        return

    backup_name = f"{table_name}_old"
    cursor.execute(f"ALTER TABLE {table_name} RENAME TO {backup_name}")
    cursor.execute(create_sql)

    old_columns = get_table_columns(backup_name)
    new_columns = get_table_columns(table_name)
    common_columns = [col for col in old_columns if col in new_columns and col != 'id']
    if common_columns:
        cols = ', '.join(common_columns)
        cursor.execute(f"INSERT INTO {table_name} ({cols}) SELECT {cols} FROM {backup_name}")

    cursor.execute(f"DROP TABLE {backup_name}")


def init_db():
    recreate_table_if_needed("patients", """CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY, name TEXT, age INTEGER, gender TEXT, disease TEXT, phone TEXT)""", ['id', 'name', 'age', 'gender', 'disease', 'phone'])
    recreate_table_if_needed("doctors", """CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY, name TEXT, specialization TEXT, phone TEXT, email TEXT)""", ['id', 'name', 'specialization', 'phone', 'email'])
    recreate_table_if_needed("appointments", """CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY, patient_id INTEGER, doctor_id INTEGER, apt_date TEXT, apt_time TEXT, reason TEXT)""", ['id', 'patient_id', 'doctor_id', 'apt_date', 'apt_time', 'reason'])
    recreate_table_if_needed("prescriptions", """CREATE TABLE IF NOT EXISTS prescriptions (
        id INTEGER PRIMARY KEY, patient_id INTEGER, doctor_id INTEGER, medicine TEXT, dosage TEXT, duration TEXT)""", ['id', 'patient_id', 'doctor_id', 'medicine', 'dosage', 'duration'])
    recreate_table_if_needed("departments", """CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY, name TEXT, head TEXT, capacity INTEGER)""", ['id', 'name', 'head', 'capacity'])
    recreate_table_if_needed("bills", """CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY, patient_id INTEGER, amount REAL, bill_date TEXT, status TEXT)""", ['id', 'patient_id', 'amount', 'bill_date', 'status'])
    conn.commit()

init_db()

# Sidebar Navigation
menu = st.sidebar.selectbox("📋 Menu", [
    "Dashboard", "Patients", "Doctors", "Appointments", 
    "Prescriptions", "Departments", "Billing"
])

# ============ DASHBOARD ============
if menu == "Dashboard":
    st.subheader("Dashboard")
    col1, col2, col3, col4 = st.columns(4)
    
    cursor.execute("SELECT COUNT(*) FROM patients")
    col1.metric("Total Patients", cursor.fetchone()[0])
    
    cursor.execute("SELECT COUNT(*) FROM doctors")
    col2.metric("Total Doctors", cursor.fetchone()[0])
    
    cursor.execute("SELECT COUNT(*) FROM appointments")
    col3.metric("Appointments", cursor.fetchone()[0])
    
    cursor.execute("SELECT COUNT(*) FROM departments")
    col4.metric("Departments", cursor.fetchone()[0])
    
    st.markdown("---")
    
    # Quick Stats
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Gender Distribution")
        cursor.execute("SELECT gender, COUNT(*) FROM patients GROUP BY gender")
        data = cursor.fetchall()
        if data:
            fig = px.pie(values=[d[1] for d in data], names=[d[0] for d in data])
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Top Diseases")
        cursor.execute("SELECT disease, COUNT(*) FROM patients WHERE disease != '' GROUP BY disease LIMIT 5")
        data = cursor.fetchall()
        if data:
            fig = px.bar(x=[d[0] for d in data], y=[d[1] for d in data])
            st.plotly_chart(fig, use_container_width=True)

# ============ PATIENTS ============
elif menu == "Patients":
    st.subheader("Patient Management")
    tabs = st.tabs(["Add", "View", "Search"])
    
    with tabs[0]:
        st.write("**Register New Patient**")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name")
            age = st.number_input("Age", min_value=0, max_value=120)
        with col2:
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            phone = st.text_input("Phone")
        
        disease = st.text_input("Disease/Condition")
        
        if st.button("Add Patient"):
            if name and disease:
                cursor.execute("INSERT INTO patients (name, age, gender, disease, phone) VALUES (?, ?, ?, ?, ?)",
                             (name, age, gender, disease, phone))
                conn.commit()
                st.success("Patient added successfully!")
            else:
                st.error("Please fill all fields")
    
    with tabs[1]:
        st.write("**All Patients**")
        cursor.execute("SELECT id, name, age, gender, disease FROM patients")
        patients = cursor.fetchall()
        if patients:
            df = pd.DataFrame(patients, columns=["ID", "Name", "Age", "Gender", "Disease"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No patients found")
    
    with tabs[2]:
        st.write("**Search Patient**")
        search_name = st.text_input("Enter patient name")
        if search_name:
            cursor.execute("SELECT id, name, age, gender, disease FROM patients WHERE name LIKE ?", (f"%{search_name}%",))
            results = cursor.fetchall()
            if results:
                df = pd.DataFrame(results, columns=["ID", "Name", "Age", "Gender", "Disease"])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Patient not found")

# ============ DOCTORS ============
elif menu == "Doctors":
    st.subheader("Doctor Management")
    tabs = st.tabs(["Add", "View", "Search"])
    
    with tabs[0]:
        st.write("**Register New Doctor**")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Doctor Name")
            specialization = st.text_input("Specialization")
        with col2:
            phone = st.text_input("Phone")
            email = st.text_input("Email")
        
        if st.button("Add Doctor"):
            if name and specialization:
                cursor.execute("INSERT INTO doctors (name, specialization, phone, email) VALUES (?, ?, ?, ?)",
                             (name, specialization, phone, email))
                conn.commit()
                st.success("Doctor added successfully!")
            else:
                st.error("Please fill required fields")
    
    with tabs[1]:
        st.write("**All Doctors**")
        cursor.execute("SELECT id, name, specialization, phone FROM doctors")
        doctors = cursor.fetchall()
        if doctors:
            df = pd.DataFrame(doctors, columns=["ID", "Name", "Specialization", "Phone"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No doctors found")
    
    with tabs[2]:
        st.write("**Search Doctor**")
        search_spec = st.text_input("Enter specialization")
        if search_spec:
            cursor.execute("SELECT id, name, specialization FROM doctors WHERE specialization LIKE ?", (f"%{search_spec}%",))
            results = cursor.fetchall()
            if results:
                df = pd.DataFrame(results, columns=["ID", "Name", "Specialization"])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No doctors found")

# ============ APPOINTMENTS ============
elif menu == "Appointments":
    st.subheader("Appointment Management")
    tabs = st.tabs(["Schedule", "View"])
    
    with tabs[0]:
        st.write("**Schedule Appointment**")
        
        cursor.execute("SELECT id, name FROM patients")
        patients = cursor.fetchall()
        patient_dict = {p[1]: p[0] for p in patients}
        
        cursor.execute("SELECT id, name FROM doctors")
        doctors = cursor.fetchall()
        doctor_dict = {d[1]: d[0] for d in doctors}
        
        col1, col2 = st.columns(2)
        with col1:
            patient = st.selectbox("Select Patient", list(patient_dict.keys()) if patient_dict else ["No patients"])
            apt_date = st.date_input("Date")
        with col2:
            doctor = st.selectbox("Select Doctor", list(doctor_dict.keys()) if doctor_dict else ["No doctors"])
            apt_time = st.time_input("Time")
        
        reason = st.text_input("Reason")
        
        if st.button("Schedule"):
            if patient in patient_dict and doctor in doctor_dict and reason:
                cursor.execute("INSERT INTO appointments (patient_id, doctor_id, apt_date, apt_time, reason) VALUES (?, ?, ?, ?, ?)",
                             (patient_dict[patient], doctor_dict[doctor], str(apt_date), str(apt_time), reason))
                conn.commit()
                st.success("Appointment scheduled!")
            else:
                st.error("Please fill all fields")
    
    with tabs[1]:
        st.write("**All Appointments**")
        cursor.execute("""SELECT a.id, p.name, d.name, a.apt_date, a.apt_time 
                         FROM appointments a 
                         JOIN patients p ON a.patient_id = p.id 
                         JOIN doctors d ON a.doctor_id = d.id""")
        appointments = cursor.fetchall()
        if appointments:
            df = pd.DataFrame(appointments, columns=["ID", "Patient", "Doctor", "Date", "Time"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No appointments found")

# ============ PRESCRIPTIONS ============
elif menu == "Prescriptions":
    st.subheader("Prescription Management")
    tabs = st.tabs(["Add", "View"])
    
    with tabs[0]:
        st.write("**Create Prescription**")
        
        cursor.execute("SELECT id, name FROM patients")
        patients = cursor.fetchall()
        patient_dict = {p[1]: p[0] for p in patients}
        
        cursor.execute("SELECT id, name FROM doctors")
        doctors = cursor.fetchall()
        doctor_dict = {d[1]: d[0] for d in doctors}
        
        col1, col2 = st.columns(2)
        with col1:
            patient = st.selectbox("Select Patient", list(patient_dict.keys()) if patient_dict else ["No patients"], key="rx_pat")
            medicine = st.text_input("Medicine")
        with col2:
            doctor = st.selectbox("Select Doctor", list(doctor_dict.keys()) if doctor_dict else ["No doctors"], key="rx_doc")
            dosage = st.text_input("Dosage")
        
        duration = st.text_input("Duration")
        
        if st.button("Add Prescription"):
            if patient in patient_dict and doctor in doctor_dict and medicine:
                cursor.execute("INSERT INTO prescriptions (patient_id, doctor_id, medicine, dosage, duration) VALUES (?, ?, ?, ?, ?)",
                             (patient_dict[patient], doctor_dict[doctor], medicine, dosage, duration))
                conn.commit()
                st.success("Prescription added!")
            else:
                st.error("Please fill all fields")
    
    with tabs[1]:
        st.write("**All Prescriptions**")
        cursor.execute("""SELECT rx.id, p.name, d.name, rx.medicine, rx.dosage 
                         FROM prescriptions rx 
                         JOIN patients p ON rx.patient_id = p.id 
                         JOIN doctors d ON rx.doctor_id = d.id""")
        prescriptions = cursor.fetchall()
        if prescriptions:
            df = pd.DataFrame(prescriptions, columns=["ID", "Patient", "Doctor", "Medicine", "Dosage"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No prescriptions found")

# ============ DEPARTMENTS ============
elif menu == "Departments":
    st.subheader("Department Management")
    tabs = st.tabs(["Add", "View"])
    
    with tabs[0]:
        st.write("**Add Department**")
        col1, col2 = st.columns(2)
        with col1:
            dept_name = st.text_input("Department Name")
            head = st.text_input("Head")
        with col2:
            capacity = st.number_input("Bed Capacity", min_value=1)
        
        if st.button("Add Department"):
            if dept_name:
                cursor.execute("INSERT INTO departments (name, head, capacity) VALUES (?, ?, ?)",
                             (dept_name, head, capacity))
                conn.commit()
                st.success("Department added!")
            else:
                st.error("Please fill required fields")
    
    with tabs[1]:
        st.write("**All Departments**")
        cursor.execute("SELECT id, name, head, capacity FROM departments")
        departments = cursor.fetchall()
        if departments:
            df = pd.DataFrame(departments, columns=["ID", "Department", "Head", "Capacity"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No departments found")

# ============ BILLING ============
elif menu == "Billing":
    st.subheader("Billing Management")
    tabs = st.tabs(["Generate Bill", "View Bills"])
    
    with tabs[0]:
        st.write("**Generate Bill**")
        
        cursor.execute("SELECT id, name FROM patients")
        patients = cursor.fetchall()
        patient_dict = {p[1]: p[0] for p in patients}
        
        col1, col2 = st.columns(2)
        with col1:
            patient = st.selectbox("Select Patient", list(patient_dict.keys()) if patient_dict else ["No patients"], key="bill_pat")
            amount = st.number_input("Amount ($)", min_value=0.0)
        with col2:
            bill_date = st.date_input("Bill Date")
            status = st.selectbox("Status", ["Pending", "Paid"])
        
        if st.button("Generate Bill"):
            if patient in patient_dict and amount > 0:
                cursor.execute("INSERT INTO bills (patient_id, amount, bill_date, status) VALUES (?, ?, ?, ?)",
                             (patient_dict[patient], amount, str(bill_date), status))
                conn.commit()
                st.success("Bill generated!")
            else:
                st.error("Please fill all fields")
    
    with tabs[1]:
        st.write("**All Bills**")
        cursor.execute("""SELECT b.id, p.name, b.amount, b.bill_date, b.status 
                         FROM bills b 
                         JOIN patients p ON b.patient_id = p.id""")
        bills = cursor.fetchall()
        if bills:
            df = pd.DataFrame(bills, columns=["ID", "Patient", "Amount ($)", "Date", "Status"])
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            col1, col2, col3 = st.columns(3)
            cursor.execute("SELECT SUM(amount) FROM bills")
            total = cursor.fetchone()[0] or 0
            col1.metric("Total Revenue", f"${total:.2f}")
            
            cursor.execute("SELECT COUNT(*) FROM bills WHERE status='Pending'")
            pending = cursor.fetchone()[0]
            col2.metric("Pending Bills", pending)
            
            cursor.execute("SELECT COUNT(*) FROM bills WHERE status='Paid'")
            paid = cursor.fetchone()[0]
            col3.metric("Paid Bills", paid)
        else:
            st.info("No bills found")

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'><small>© 2026 Medicare Hospital. All rights reserved.</small></div>", unsafe_allow_html=True)

conn.close()
