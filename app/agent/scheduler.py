import pandas as pd
import os
from datetime import datetime, timedelta

SCHEDULE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "doctor_schedule.xlsx")

class Scheduler:
    def __init__(self, path: str = SCHEDULE_PATH):
        self.path = path
        # If doctor schedule file doesn’t exist → create dummy schedule
        if not os.path.exists(self.path):
            self._create_default_schedule()
        self.df = pd.read_excel(self.path)

    def _create_default_schedule(self):
        doctors = ["Smith", "Johnson"]
        today = datetime.today().date()
        slots = []
        for d in range(7):  # next 7 days
            day = today + timedelta(days=d)
            for doctor in doctors:
                for hour in range(9, 17):  # 9 AM - 5 PM
                    slot_time = f"{hour:02d}:00"
                    slots.append({
                        "date": day.strftime("%Y-%m-%d"),
                        "time": slot_time,
                        "doctor": doctor,
                        "available": True
                    })
        df = pd.DataFrame(slots)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        df.to_excel(self.path, index=False)

    def get_available_slots(self, minutes_required: int, chosen_date: str = None, doctor: str = None):
        """Return available slots for a specific date (default: today)."""
        df_avail = self.df[self.df['available'] == True]
        if chosen_date:
            df_avail = df_avail[df_avail['date'] == chosen_date]
        if doctor:
            df_avail = df_avail[df_avail['doctor'] == doctor]

        # Remove already booked from appointments.xlsx
        appt_file = os.path.join("app", "data", "appointments.xlsx")
        if os.path.exists(appt_file) and not df_avail.empty:
            booked_df = pd.read_excel(appt_file)
            booked_keys = set(zip(booked_df["date"], booked_df["time"], booked_df["doctor"]))
            df_avail = df_avail[~df_avail.apply(
                lambda r: (r["date"], r["time"], r["doctor"]) in booked_keys, axis=1
            )]

        return df_avail.to_dict(orient="records")

    def book_slot(self, date: str, time: str, doctor: str):
        """Book a slot if available and not already booked."""
        idx = self.df.index[
            (self.df['date'] == date) & (self.df['time'] == time) & (self.df['doctor'] == doctor)
        ]
        if len(idx) > 0 and self.df.loc[idx, 'available'].all():
            # Double-booking check against appointments.xlsx
            appt_file = os.path.join("app", "data", "appointments.xlsx")
            if os.path.exists(appt_file):
                booked_df = pd.read_excel(appt_file)
                conflict = booked_df[
                    (booked_df['date'] == date) &
                    (booked_df['time'] == time) &
                    (booked_df['doctor'] == doctor)
                ]
                if not conflict.empty:
                    return False  # already taken

            # Mark unavailable in doctor schedule
            self.df.loc[idx, 'available'] = False
            self.df.to_excel(self.path, index=False)
            return True
        return False
