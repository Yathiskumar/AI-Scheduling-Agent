import time
import threading
import streamlit as st

class ReminderSystem:
    def __init__(self):
        self.reminders = []

    def schedule_reminders(self, patient, appointment):
        """
        Simulate 3 reminders for the booked appointment.
        In real deployment, you'd use email/SMS APIs + proper scheduling.
        """
        self.reminders = [
            f"📧 Reminder 1: Hello {patient['first_name']}, "
            f"your appointment is on {appointment['date']} at {appointment['time']} with {appointment['doctor']}.",

            f"📧 Reminder 2: Hi {patient['first_name']}, "
            f"please confirm you filled your intake form before your appointment.",

            f"📧 Reminder 3: Final reminder! Please confirm your visit or reply with reason for cancellation."
        ]

        # Run in background (simulated delays)
        def send_all():
            for r in self.reminders:
                time.sleep(2)  # simulate delay
                st.toast(r)

        threading.Thread(target=send_all, daemon=True).start()
