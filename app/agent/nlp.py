import re

def valid_name(s: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z\s\-']{1,49}", s.strip()))

def valid_dob(s: str) -> bool:
    # Accept YYYY-MM-DD or DD/MM/YYYY basic checks (Step 2 we'll harden this)
    return bool(re.fullmatch(r"(\d{4}-\d{2}-\d{2})|(\d{2}/\d{2}/\d{4})", s.strip()))
