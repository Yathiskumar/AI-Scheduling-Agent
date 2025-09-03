# app/agent/patient_db.py
import pandas as pd
import os

class PatientDB:
    def __init__(self, path=None):
        if path is None:
            path = os.path.join("app", "data", "patients.csv")
        self.path = path

    def load_patients(self):
        if os.path.exists(self.path):
            return pd.read_csv(self.path)
        return pd.DataFrame(columns=[
            "First Name", "Last Name", "Date of Birth (YYYY-MM-DD)",
            "Email (patient)", "Phone (patient)",
            "Insurance Company (carrier)", "Member ID", "Group Number"
        ])

    def find_patient(self, first_name, last_name, dob):
        df = self.load_patients()
        match = df[
            (df["First Name"].str.lower() == first_name.lower()) &
            (df["Last Name"].str.lower() == last_name.lower()) &
            (df["Date of Birth (YYYY-MM-DD)"] == dob)
        ]
        if not match.empty:
            return match.iloc[0].to_dict()
        return None
