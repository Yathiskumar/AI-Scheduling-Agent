from dataclasses import dataclass

@dataclass
class VisitPolicy:
    NEW_PATIENT_MINUTES: int = 60
    RETURNING_PATIENT_MINUTES: int = 30

def duration_for_patient_type(is_new: bool) -> int:
    return VisitPolicy.NEW_PATIENT_MINUTES if is_new else VisitPolicy.RETURNING_PATIENT_MINUTES
