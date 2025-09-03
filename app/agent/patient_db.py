import pandas as pd
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "patients.csv")

class PatientDB:
    def __init__(self, path: str = DATA_PATH):
        self.path = path
        self.df = pd.read_csv(self.path)

    def find_patient(self, first_name: str, last_name: str, dob: str):
        match = self.df[
            (self.df['first_name'].str.lower() == first_name.strip().lower()) &
            (self.df['last_name'].str.lower() == last_name.strip().lower()) &
            (self.df['dob'] == dob.strip())
        ]
        if len(match) > 0:
            return match.iloc[0].to_dict()
        return None

    def is_new_patient(self, first_name: str, last_name: str, dob: str) -> bool:
        return self.find_patient(first_name, last_name, dob) is None
