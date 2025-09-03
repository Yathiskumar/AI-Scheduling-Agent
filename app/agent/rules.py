# app/agent/rules.py
import os
import json

RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "rules.json")

def ensure_rules_file():
    d = os.path.dirname(RULES_PATH)
    os.makedirs(d, exist_ok=True)
    if not os.path.exists(RULES_PATH):
        with open(RULES_PATH, "w") as f:
            json.dump([], f)

def load_rules():
    ensure_rules_file()
    with open(RULES_PATH, "r") as f:
        return json.load(f)

def save_rule(rule_obj, raw_text=None):
    """
    Append rule_obj (dict) to rules.json; optionally store raw natural text.
    """
    ensure_rules_file()
    rules = load_rules()
    # store both parsed and raw text for traceability
    entry = {"rule": rule_obj}
    if raw_text:
        entry["raw"] = raw_text
    rules.append(entry)
    with open(RULES_PATH, "w") as f:
        json.dump(rules, f, indent=2)
    return True

def delete_rule(index):
    rules = load_rules()
    if 0 <= index < len(rules):
        rules.pop(index)
        with open(RULES_PATH, "w") as f:
            json.dump(rules, f, indent=2)
        return True
    return False

# Simple rule applier (keeps logic small & deterministic)
def apply_rules(patient_core, patient_details, slots, rules):
    """
    patient_core: {"first_name","last_name","dob","patient_type":"new"/"returning" optional}
    patient_details: {"email","phone","insurance_company","member_id","group_number"}
    slots: list of slot dicts: {"date","time","doctor",...}
    rules: list loaded from load_rules() -> entries with "rule"
    Returns: (filtered_slots, duration_override or None)
    """
    duration_override = None
    filtered_slots = slots[:]  # start with all available

    for entry in rules:
        rule = entry.get("rule", {})
        condition = rule.get("condition", {})
        action = rule.get("action", {})

        # Evaluate condition — simplistic equals/contains check
        match = True
        for k, v in condition.items():
            if k == "patient_type":
                ptype = "new" if patient_core and patient_core.get("is_new") else "returning"
                if ptype != v:
                    match = False; break
            else:
                # check patient_details first then patient_core
                val = patient_details.get(k) if patient_details and k in patient_details else patient_core.get(k) if patient_core else None
                if val is None:
                    match = False; break
                # case-insensitive compare if strings
                if isinstance(v, str) and isinstance(val, str):
                    if v.lower() not in val.lower():
                        match = False; break
                else:
                    if val != v:
                        match = False; break

        if not match:
            continue

        # Apply action
        if "assign_doctor" in action:
            doc = action["assign_doctor"]
            filtered_slots = [s for s in filtered_slots if doc.lower() in s.get("doctor", "").lower()]

        if "block_doctor" in action:
            doc = action["block_doctor"]
            filtered_slots = [s for s in filtered_slots if doc.lower() not in s.get("doctor", "").lower()]

        if "prefer_doctor" in action:
            doc = action["prefer_doctor"].lower()
            # sort so preferred doctor appears first
            filtered_slots = sorted(filtered_slots, key=lambda s: 0 if doc in s.get("doctor","").lower() else 1)

        if "duration" in action:
            try:
                duration_override = int(action["duration"])
            except Exception:
                pass

        # other actions can be added as needed

    return filtered_slots, duration_override
