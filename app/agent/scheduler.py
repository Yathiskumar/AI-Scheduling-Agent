import pandas as pd
import os

SCHEDULE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "doctor_schedule.xlsx")

class Scheduler:
    def __init__(self, path: str = SCHEDULE_PATH):
        self.path = path
        self.df = pd.read_excel(self.path)

    def get_available_slots(self, minutes_required: int, doctor: str = None):
        # For now, just return first 5 available slots
        df_avail = self.df[self.df['available'] == True]
        if doctor:
            df_avail = df_avail[df_avail['doctor'] == doctor]
        return df_avail.head(5).to_dict(orient="records")

    def book_slot(self, date: str, time: str, doctor: str):
        idx = self.df.index[
            (self.df['date'] == date) & (self.df['time'] == time) & (self.df['doctor'] == doctor)
        ]
        if len(idx) > 0:
            self.df.loc[idx, 'available'] = False
            self.df.to_excel(self.path, index=False)
            return True
        return False
