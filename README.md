# AI Scheduling Agent — Starter (Step 1)

This starter packs the project structure and a minimal Streamlit app so you can install and run quickly.
You’ll add features in the next steps.

## 1) Create environment

### Windows (PowerShell)
```pwsh
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -r requirements.txt
```

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## 2) Configure env
Copy `.env.example` to `.env` and fill if you want real email/SMS. If you leave blank, the app will simulate sending.

## 3) Run the app
From the project root:
```bash
streamlit run app/main.py
```
Open the local URL shown in the terminal.

## Project layout
```
ai-scheduler/
├─ app/
│  ├─ main.py              # Streamlit UI (chat skeleton)
│  ├─ agent/
│  │  ├─ policy.py         # Business rules placeholder
│  │  ├─ scheduler.py      # Scheduling placeholder
│  │  └─ nlp.py            # Simple validation placeholder
│  ├─ data/                # Will hold patients.csv & doctor_schedule.xlsx (next step)
│  └─ assets/
│     └─ intake_form.pdf   # Intake form you uploaded
├─ scripts/
│  └─ generate_mock_data.py  # To be completed in Step 2
├─ .env.example
├─ requirements.txt
└─ README.md
```

Next step will add: synthetic data generation, patient lookup, scheduling logic, Excel export, and reminders.
