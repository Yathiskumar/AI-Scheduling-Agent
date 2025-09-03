import datetime
import os

def create_ics_file(patient_name, doctor, date, time, duration, save_dir="app/data"):
    """
    Generate an .ics calendar invite file for the appointment.
    """
    dt_start = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    dt_end = dt_start + datetime.timedelta(minutes=duration)

    # ICS datetime format: YYYYMMDDTHHMMSS
    start_str = dt_start.strftime("%Y%m%dT%H%M%S")
    end_str = dt_end.strftime("%Y%m%dT%H%M%S")

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//AI Scheduler//EN
BEGIN:VEVENT
SUMMARY:Doctor Appointment with {doctor}
DTSTART:{start_str}
DTEND:{end_str}
DESCRIPTION:Appointment for {patient_name}
LOCATION:Clinic
END:VEVENT
END:VCALENDAR
"""

    os.makedirs(save_dir, exist_ok=True)
    filename = os.path.join(save_dir, f"{patient_name}_{date}_{time.replace(':','')}.ics")
    with open(filename, "w") as f:
        f.write(ics_content)

    return filename
