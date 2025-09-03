import streamlit as st
from dotenv import load_dotenv
import os
import pandas as pd
import uuid, random

from agent.patient_db import PatientDB
from agent.policy import duration_for_patient_type
from agent.scheduler import Scheduler
from agent.emailer import send_email
from utils.calendar import create_ics_file

load_dotenv()

st.set_page_config(page_title="AI Scheduling Agent", page_icon="📅", layout="wide")

st.title("📅 AI Scheduling Agent")

# Ensure data dir exists
os.makedirs(os.path.join("app", "data"), exist_ok=True)

# Sidebar switch
mode = st.sidebar.radio("Select Mode", ["Patient Portal", "Admin Dashboard"])

# Init DB + Scheduler
db = PatientDB()
scheduler = Scheduler()

# ---------- Session state init ----------
def init_state():
    defaults = {
        "minutes": None,
        "patient_found": False,
        "is_new_patient": None,
        "patient_core": None,
        "patient_details": None,
        "available_slots": [],
        "available_dates": [],
        "selected_date": None,
        "chosen_slot": None,
        "admin_logged_in": False
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# Small helpers
def gen_member_ids():
    member_id = f"MBR-{uuid.uuid4().hex[:6].upper()}"
    group_number = f"GRP-{random.randint(10000,99999)}"
    return member_id, group_number

def require_nonempty(value, label):
    if not value or str(value).strip() == "":
        st.error(f"Please provide {label}.")
        return False
    return True

# ========================
#  PATIENT PORTAL SECTION
# ========================
if mode == "Patient Portal":
    with st.chat_message("assistant"):
        st.write("👋 Hi! I’m your AI Scheduling Assistant. First, check if you’re an existing patient using your name and DOB.")

    # ---------- Step 1: Identify patient ----------
    with st.form("identify_form", clear_on_submit=False):
        st.subheader("Step 1: Identify Patient")
        first_name = st.text_input("First Name", key="first_name_input")
        last_name = st.text_input("Last Name", key="last_name_input")
        dob = st.text_input("Date of Birth (YYYY-MM-DD)", key="dob_input")
        submitted_identify = st.form_submit_button("Check")

    if submitted_identify:
        if not (require_nonempty(first_name, "First Name") and
                require_nonempty(last_name, "Last Name") and
                require_nonempty(dob, "DOB (YYYY-MM-DD)")):
            st.stop()

        patient = db.find_patient(first_name, last_name, dob)

        st.session_state.patient_core = {
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "dob": dob.strip()
        }

        if patient:
            # Existing
            st.session_state.patient_found = True
            st.session_state.is_new_patient = False
            st.session_state.minutes = duration_for_patient_type(False)
            st.session_state.patient_details = {
                "email": patient.get("Email (patient)", ""),
                "phone": patient.get("Phone (patient)", ""),
                "insurance_company": patient.get("Insurance Company (carrier)", ""),
                "member_id": patient.get("Member ID", ""),
                "group_number": patient.get("Group Number", "")
            }
            st.success(f"Returning patient found: {patient['First Name']} {patient['Last Name']}")
        else:
            # New patient
            st.session_state.patient_found = False
            st.session_state.is_new_patient = True
            st.session_state.minutes = duration_for_patient_type(True)
            mbr, grp = gen_member_ids()
            st.session_state.patient_details = {
                "email": "",
                "phone": "",
                "insurance_company": "",
                "member_id": mbr,
                "group_number": grp
            }
            st.warning("New patient. Please fill your contact and insurance details.")

        # Reset scheduling
        st.session_state.available_slots = []
        st.session_state.available_dates = []
        st.session_state.selected_date = None
        st.session_state.chosen_slot = None
        st.rerun()

    # ---------- Step 2: Patient details ----------
    if st.session_state.patient_core:
        st.subheader("Step 2: Patient Details")

        details = st.session_state.patient_details or {}

        col1, col2 = st.columns(2)
        with col1:
            email_val = st.text_input("Email (patient)", value=details.get("email", ""), key="email_input")
            insurance_val = st.text_input("Insurance Company (carrier)", value=details.get("insurance_company", ""), key="insurance_input")
        with col2:
            phone_val = st.text_input("Phone (patient)", value=details.get("phone", ""), key="phone_input")

        id_col1, id_col2 = st.columns(2)
        with id_col1:
            st.text_input("Member ID", value=details.get("member_id", ""), disabled=True, key="member_id_display")
        with id_col2:
            st.text_input("Group Number", value=details.get("group_number", ""), disabled=True, key="group_number_display")

        if st.button("Save Details & Load Available Slots"):
            ok = True
            ok &= require_nonempty(email_val, "Email")
            ok &= require_nonempty(phone_val, "Phone")
            ok &= require_nonempty(insurance_val, "Insurance Company")
            if not ok:
                st.stop()

            st.session_state.patient_details.update({
                "email": email_val.strip(),
                "phone": phone_val.strip(),
                "insurance_company": insurance_val.strip(),
            })

            minutes_needed = st.session_state.minutes or duration_for_patient_type(not st.session_state.patient_found)
            slots = scheduler.get_available_slots(minutes_required=minutes_needed) or []

            # Remove already booked slots
            appt_file = os.path.join("app", "data", "appointments.xlsx")
            if os.path.exists(appt_file) and not slots == []:
                booked_df = pd.read_excel(appt_file)
                booked_keys = set(zip(booked_df["date"], booked_df["time"], booked_df["doctor"]))
                slots = [s for s in slots if (s["date"], s["time"], s["doctor"]) not in booked_keys]

            st.session_state.available_slots = slots

            st.session_state.available_slots = slots
            st.session_state.available_dates = sorted({s["date"] for s in slots})
            if not slots:
                st.error("No available slots found.")
            else:
                st.success(f"Loaded {len(slots)} available slots.")
            st.rerun()

        if st.session_state.minutes:
            st.info(f"Appointment length will be **{st.session_state.minutes} minutes**.")

    # ---------- Step 3: Choose date & time ----------
    if st.session_state.available_slots:
        st.subheader("Step 3: Choose Date & Time")

        # Calendar date picker
        from datetime import date, timedelta
        today = date.today()
        tomorrow = today + timedelta(days=1)

        selected_date = st.date_input(
            "Choose appointment date (only today/tomorrow allowed)",
            value=today,
            min_value=today,
            max_value=tomorrow,
            key="calendar_date"
        )

        st.session_state.selected_date = str(selected_date)

        # Times filtered by selected date
        todays = [s for s in st.session_state.available_slots if s["date"] == st.session_state.selected_date]
        if not todays:
            st.warning("No slots available for this date.")
        else:
            st.session_state.chosen_slot = st.selectbox(
                "Select a time",
                options=todays,
                format_func=lambda s: f"{s['time']} — Dr. {s['doctor']}",
                key="slot_choice"
            )

        # ---------- Book ----------
        if st.button("Book Appointment", key="book_btn"):
            if not st.session_state.chosen_slot:
                st.error("Please choose a slot.")
                st.stop()

            chosen = st.session_state.chosen_slot
            date, time_str, doctor = chosen["date"], chosen["time"], chosen["doctor"]

            success = scheduler.book_slot(date, time_str, doctor)
            if success:
                core = st.session_state.patient_core
                details = st.session_state.patient_details
                minutes_required = st.session_state.minutes

                st.success(f"✅ Appointment booked for {core['first_name']} {core['last_name']} on {date} at {time_str} with Dr. {doctor}")

                # Save appointment
                appt_file = os.path.join("app", "data", "appointments.xlsx")
                record = {
                    "first_name": core["first_name"],
                    "last_name": core["last_name"],
                    "dob": core["dob"],
                    "email": details["email"],
                    "phone": details["phone"],
                    "insurance_company": details["insurance_company"],
                    "member_id": details["member_id"],
                    "group_number": details["group_number"],
                    "date": date,
                    "time": time_str,
                    "doctor": doctor,
                    "duration": minutes_required,
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
                df.to_excel(appt_file, index=False, engine="openpyxl")
                st.info("📄 Appointment saved to appointments.xlsx")

                # Save new patient if needed
                if st.session_state.is_new_patient:
                    patients_file = os.path.join("app", "data", "patients.csv")
                    new_patient = {
                        "First Name": core["first_name"],
                        "Last Name": core["last_name"],
                        "Date of Birth (YYYY-MM-DD)": core["dob"],
                        "Email (patient)": details["email"],
                        "Phone (patient)": details["phone"],
                        "Insurance Company (carrier)": details["insurance_company"],
                        "Member ID": details["member_id"],
                        "Group Number": details["group_number"]
                    }
                    if os.path.exists(patients_file):
                        patients_df = pd.read_csv(patients_file)
                        patients_df = pd.concat([patients_df, pd.DataFrame([new_patient])], ignore_index=True)
                    else:
                        patients_df = pd.DataFrame([new_patient])
                    patients_df.to_csv(patients_file, index=False)
                    st.info("🆕 New patient added to patients.csv")

                # ICS download
                ics_path = create_ics_file(
                    f"{core['first_name']} {core['last_name']}",
                    doctor,
                    date,
                    time_str,
                    minutes_required
                )
                st.download_button(
                    "📅 Download Calendar Invite (.ics)",
                    open(ics_path, "rb"),
                    file_name=os.path.basename(ics_path),
                    mime="text/calendar"
                )

                # Email confirmation
                form_path = os.path.join("app", "assets", "intake_form.pdf")
                to_email = details["email"]
                email_sent = False
                if to_email:
                    subject = f"Appointment Confirmation — {date} {time_str}"
                    body = (
                        f"Hi {core['first_name']},\n\n"
                        f"Your appointment is confirmed on {date} at {time_str} with Dr. {doctor}.\n"
                        f"Please find the intake form attached.\n\nThanks."
                    )
                    attachment_paths = [form_path] if os.path.exists(form_path) else None
                    email_sent = send_email(to_email, subject, body, attachment_paths=attachment_paths)

                if email_sent:
                    st.success("📧 Confirmation email sent to patient.")
                else:
                    st.warning("⚠️ Email sending failed or not configured.")

            else:
                st.error("❌ Failed to book slot. Please try another time or date.")

# ========================
#  ADMIN DASHBOARD SECTION
# ========================
if mode == "Admin Dashboard":
    admin_pass = os.getenv("ADMIN_PASS", "admin123")

    if not st.session_state.admin_logged_in:
        st.subheader("🔐 Admin Login")
        entered_pass = st.text_input("Enter Admin Password", type="password")
        if st.button("Login"):
            if entered_pass == admin_pass:
                st.session_state.admin_logged_in = True
                st.success("✅ Logged in successfully.")
                st.rerun()
            else:
                st.error("❌ Incorrect password.")
    else:
        st.subheader("📑 Admin Dashboard")
        if st.button("Logout"):
            st.session_state.admin_logged_in = False
            st.info("🔒 Logged out successfully.")
            st.rerun()
        else:
            appt_file = os.path.join("app", "data", "appointments.xlsx")

            if os.path.exists(appt_file):
                df = pd.read_excel(appt_file)
                st.dataframe(df, width="stretch")

                idx = st.number_input(
                    "Select appointment row index to manage (0-based)",
                    min_value=0,
                    max_value=max(0, len(df) - 1),
                    step=1,
                )

                if st.button("Load appointment"):
                    st.session_state.selected_idx = int(idx)
                    st.session_state.selected_row = df.iloc[int(idx)].to_dict()
                    st.write("Selected:", st.session_state.selected_row)

                if "selected_idx" in st.session_state:
                    reason = st.text_input("If cancelling, enter reason")

                    if st.button("Cancel Appointment"):
                        df.at[st.session_state.selected_idx, "status"] = f"Cancelled by Doctor - {reason or 'No reason provided'}"
                        df.to_excel(appt_file, index=False, engine="openpyxl")
                        st.success("❌ Appointment Cancelled by Doctor (saved to file)")

                        new_df = pd.read_excel(appt_file)
                        st.dataframe(new_df, width="stretch")

                        updated_row = new_df.iloc[st.session_state.selected_idx].to_dict()
                        st.info(f"Updated Appointment Status: {updated_row['status']}")

                        # Send cancellation email
                        patient_email = updated_row.get("email")
                        if patient_email:
                            subject = f"Appointment Cancelled — {updated_row['date']} {updated_row['time']}"
                            body = (
                                f"Hi {updated_row['first_name']},\n\n"
                                f"Your appointment has been cancelled by the doctor.\n"
                                f"Reason: {reason or 'Not specified'}.\n\n"
                                "Please rebook if needed."
                            )
                            send_email(patient_email, subject, body)
                            st.info("📧 Cancellation email sent to patient.")
            else:
                st.info("No appointments booked yet.")
