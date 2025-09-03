import streamlit as st
from dotenv import load_dotenv
import os
import pandas as pd

from agent.patient_db import PatientDB
from agent.policy import duration_for_patient_type
from agent.scheduler import Scheduler
from agent.emailer import send_email

load_dotenv()

st.set_page_config(page_title="AI Scheduling Agent", page_icon="📅", layout="wide")

st.title("📅 AI Scheduling Agent")

# Sidebar switch
mode = st.sidebar.radio("Select Mode", ["Patient Portal", "Admin Dashboard"])

# Init DB + Scheduler
db = PatientDB()
scheduler = Scheduler()

# ========================
#  PATIENT PORTAL SECTION
# ========================
if mode == "Patient Portal":
    with st.chat_message("assistant"):
        st.write("👋 Hi! I’m your AI Scheduling Assistant. Please enter your details below to check or book an appointment.")

    # --- Patient Form ---
    with st.form("patient_form"):
        st.subheader("Patient Info")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        dob = st.text_input("Date of Birth (YYYY-MM-DD)")

        email = st.text_input("Email (patient)")
        phone = st.text_input("Phone (patient)")

        # Insurance info (assignment requires this)
        insurance_company = st.text_input("Insurance Company (carrier)")
        member_id = st.text_input("Member ID")
        group_number = st.text_input("Group Number")

        submitted = st.form_submit_button("Check")

    if submitted:
        if not (first_name and last_name and dob):
            st.error("Please fill at least First Name, Last Name, and DOB.")
        else:
            patient = db.find_patient(first_name, last_name, dob)
            if patient:
                st.success(f"Returning patient found: {patient['first_name']} {patient['last_name']}")
                st.session_state.minutes = duration_for_patient_type(False)
                email = email or patient.get("email")
                phone = phone or patient.get("phone")
            else:
                st.warning("New patient, no record found.")
                st.session_state.minutes = duration_for_patient_type(True)

            st.info(f"Appointment length will be {st.session_state.minutes} minutes.")

            slots = scheduler.get_available_slots(minutes_required=st.session_state.minutes)
            st.session_state.slots = slots if slots else []
            if not slots:
                st.error("No available slots found.")

    # --- Show available slots persistently ---
    if st.session_state.get("slots"):
        st.subheader("Available Slots")
        slot_options = [f"{s['date']} {s['time']} with {s['doctor']}" for s in st.session_state.slots]
        chosen_slot = st.selectbox("Select a slot", slot_options, key="slot_select")

        if st.button("Book Appointment", key="book_btn"):
            date, time, _, doctor = chosen_slot.split(" ", 3)
            doctor = doctor.replace("with ", "").strip()

            success = scheduler.book_slot(date, time, doctor)
            if success:
                st.success(f"✅ Appointment booked for {first_name} {last_name} on {date} at {time} with {doctor}")

                # Save appointment
                appt_file = os.path.join("app", "data", "appointments.xlsx")
                record = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "dob": dob,
                    "email": email or "",
                    "phone": phone or "",
                    "insurance_company": insurance_company or "",
                    "member_id": member_id or "",
                    "group_number": group_number or "",
                    "date": date,
                    "time": time,
                    "doctor": doctor,
                    "duration": st.session_state.minutes,
                    "form_sent": True,
                    "form_filled": False,
                    "status": "Scheduled",
                    "notes": ""
                }
                if os.path.exists(appt_file):
                    df = pd.read_excel(appt_file)
                    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
                else:
                    df = pd.DataFrame([record])
                df.to_excel(appt_file, index=False)
                st.info("📄 Appointment exported to `appointments.xlsx`")

                # Send intake form (real if SMTP configured, else simulate)
                form_path = os.path.join("app", "assets", "intake_form.pdf")
                to_email = record["email"]
                email_sent = False
                if to_email:
                    subject = f"Appointment Confirmation — {record['date']} {record['time']}"
                    body = f"Hi {first_name},\n\nYour appointment is confirmed on {date} at {time} with {doctor}.\nPlease find the intake form attached.\n\nThanks."
                    email_sent = send_email(to_email, subject, body, attachment_path=form_path)
                else:
                    st.info("No patient email available — intake form available for download below.")

                if email_sent:
                    st.success("📧 Intake form emailed to patient (or simulated).")
                else:
                    st.warning("⚠️ Email sending failed or not configured; patient can download below.")

                if os.path.exists(form_path):
                    with open(form_path, "rb") as f:
                        st.download_button("⬇️ Download Intake Form (PDF)", f, file_name="intake_form.pdf")

                # 🔔 Reminders (simulated toasts)
                from agent.reminder import ReminderSystem
                reminder = ReminderSystem()
                reminder.schedule_reminders(
                    {"first_name": first_name, "last_name": last_name, "email": to_email, "phone": phone},
                    {"date": date, "time": time, "doctor": doctor}
                )
                st.info("🔔 Reminders scheduled (simulated).")

            else:
                st.error("❌ Failed to book slot. Please try another.")


# ========================
#  ADMIN DASHBOARD SECTION
# ========================
if mode == "Admin Dashboard":
    st.subheader("📑 All Booked Appointments")
    appt_file = os.path.join("app", "data", "appointments.xlsx")

    if os.path.exists(appt_file):
        df = pd.read_excel(appt_file)
        st.dataframe(df, use_container_width=True)

        idx = st.number_input("Select appointment row index to manage (0-based)", min_value=0, max_value=max(0, len(df)-1), step=1)
        if st.button("Load appointment"):
            row = df.iloc[int(idx)].to_dict()
            st.write("Selected:", row)

            if st.button("Mark form as filled"):
                df.at[int(idx), "form_filled"] = True
                df.at[int(idx), "status"] = "Form Submitted"
                df.to_excel(appt_file, index=False)
                st.success("Marked form_filled = True")

            reason = st.text_input("If cancelling, enter reason")
            if st.button("Confirm Appointment"):
                df.at[int(idx), "status"] = "Confirmed"
                df.to_excel(appt_file, index=False)
                st.success("Appointment Confirmed")

            if st.button("Cancel Appointment"):
                df.at[int(idx), "status"] = f"Cancelled - {reason or 'No reason'}"
                df.to_excel(appt_file, index=False)
                st.success("Appointment Cancelled")
    else:
        st.info("No appointments booked yet.")
