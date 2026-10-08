from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import Optional

from .vaccine_data import HPV_SCHEDULE, VACCINE_SCHEDULE


def _to_date(value) -> date:
    """Convert a date-like value to a date object."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def add_months(value, months: int) -> date:
    """Add calendar months while safely handling month-end dates."""
    value = _to_date(value)

    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1

    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


def calculate_age(date_of_birth, as_of=None) -> dict:
    """Calculate a child's age using the supplied reference date."""
    dob = _to_date(date_of_birth)
    reference_date = _to_date(as_of) if as_of else date.today()

    if reference_date < dob:
        raise ValueError("as_of date cannot be earlier than date of birth.")

    total_days = (reference_date - dob).days

    total_weeks = total_days // 7

    years = reference_date.year - dob.year
    if (reference_date.month, reference_date.day) < (dob.month, dob.day):
        years -= 1

    months = (
        (reference_date.year - dob.year) * 12
        + reference_date.month
        - dob.month
    )
    if reference_date.day < dob.day:
        months -= 1

    return {
        "date_of_birth": dob,
        "as_of": reference_date,
        "total_days": total_days,
        "total_weeks": total_weeks,
        "total_months": months,
        "years": years,
    }


def _milestone_due_date(date_of_birth, entry) -> date:
    """Calculate the routine milestone date for a vaccine."""
    dob = _to_date(date_of_birth)

    if entry["age_unit"] == "days":
        return dob + timedelta(days=entry["age_value"])

    if entry["age_unit"] == "weeks":
        return dob + timedelta(weeks=entry["age_value"])

    if entry["age_unit"] == "months":
        return add_months(dob, entry["age_value"])

    raise ValueError(f"Unsupported age unit: {entry['age_unit']}")


def _status_for_fixed_date(due_date, as_of, completed_date=None) -> str:
    """Return vaccine status based on due date and vaccination history."""
    if completed_date:
        return "Completed"

    if due_date < as_of:
        return "Overdue"

    if due_date == as_of:
        return "Due Now"

    return "Upcoming"


def _build_fixed_schedule(date_of_birth, vaccination_history, as_of):
    records = []

    for entry in VACCINE_SCHEDULE:
        due_date = _milestone_due_date(date_of_birth, entry)

        completed_date = vaccination_history.get(entry["id"])
        if completed_date:
            completed_date = _to_date(completed_date)

        status = _status_for_fixed_date(
            due_date,
            as_of,
            completed_date,
        )

        records.append(
            {
                **entry,
                "due_date": due_date,
                "due_date_label": due_date.strftime("%d %b %Y"),
                "status": status,
                "is_windowed": False,
                "window_start": None,
                "window_end": None,
                "completed_date": completed_date,
            }
        )

    return records


def _build_hpv_schedule(date_of_birth, vaccination_history, as_of):
    """Build HPV records using the 9-13 year window and 6-month interval."""
    dob = _to_date(date_of_birth)

    window_start = add_months(dob, HPV_SCHEDULE["minimum_age_years"] * 12)
    window_end = add_months(dob, HPV_SCHEDULE["maximum_age_years"] * 12)

    hpv1_completed = vaccination_history.get("hpv1")
    hpv2_completed = vaccination_history.get("hpv2")

    hpv1_completed = _to_date(hpv1_completed) if hpv1_completed else None
    hpv2_completed = _to_date(hpv2_completed) if hpv2_completed else None

    if hpv1_completed:
        hpv1_status = "Completed"
    elif as_of < window_start:
        hpv1_status = "Upcoming"
    elif as_of <= window_end:
        hpv1_status = "Due Now"
    else:
        hpv1_status = "Overdue"

    hpv1 = {
        "id": "hpv1",
        "series": HPV_SCHEDULE["series"],
        "dose_number": 1,
        "target_age_label": HPV_SCHEDULE["target_age_label"],
        "age_unit": "years",
        "age_value": HPV_SCHEDULE["minimum_age_years"],
        "vaccine": "HPV 1",
        "dosage": HPV_SCHEDULE["dosage"],
        "route": HPV_SCHEDULE["route"],
        "site": HPV_SCHEDULE["site"],
        "due_date": None,
        "due_date_label": (
            f"{window_start.strftime('%d %b %Y')} - "
            f"{window_end.strftime('%d %b %Y')}"
        ),
        "status": hpv1_status,
        "is_windowed": True,
        "window_start": window_start,
        "window_end": window_end,
        "completed_date": hpv1_completed,
    }

    hpv2_due_date = (
        add_months(hpv1_completed, HPV_SCHEDULE["interval_months"])
        if hpv1_completed
        else None
    )

    if hpv2_completed:
        hpv2_status = "Completed"
    elif hpv2_due_date is None:
        hpv2_status = "Pending Dose 1"
    elif hpv2_due_date < as_of:
        hpv2_status = "Overdue"
    elif hpv2_due_date == as_of:
        hpv2_status = "Due Now"
    else:
        hpv2_status = "Upcoming"

    hpv2 = {
        "id": "hpv2",
        "series": HPV_SCHEDULE["series"],
        "dose_number": 2,
        "target_age_label": "6 months after HPV 1",
        "age_unit": "months",
        "age_value": HPV_SCHEDULE["interval_months"],
        "vaccine": "HPV 2",
        "dosage": HPV_SCHEDULE["dosage"],
        "route": HPV_SCHEDULE["route"],
        "site": HPV_SCHEDULE["site"],
        "due_date": hpv2_due_date,
        "due_date_label": (
            hpv2_due_date.strftime("%d %b %Y")
            if hpv2_due_date
            else "After HPV 1"
        ),
        "status": hpv2_status,
        "is_windowed": False,
        "window_start": None,
        "window_end": None,
        "completed_date": hpv2_completed,
    }

    return [hpv1, hpv2]


def build_vaccine_schedule(
    date_of_birth,
    vaccination_history=None,
    as_of=None,
):
    """Build the complete routine vaccination schedule for a child."""
    vaccination_history = vaccination_history or {}

    dob = _to_date(date_of_birth)
    reference_date = _to_date(as_of) if as_of else date.today()

    if reference_date < dob:
        raise ValueError("as_of date cannot be earlier than date of birth.")

    records = _build_fixed_schedule(
        dob,
        vaccination_history,
        reference_date,
    )

    records.extend(
        _build_hpv_schedule(
            dob,
            vaccination_history,
            reference_date,
        )
    )

    return records


def group_vaccines_by_status(records):
    """Group vaccine records into standard status buckets."""
    grouped = {
        "overdue": [],
        "due_now": [],
        "upcoming": [],
        "completed": [],
    }

    for record in records:
        status = record["status"]

        if status == "Overdue":
            grouped["overdue"].append(record)
        elif status == "Due Now":
            grouped["due_now"].append(record)
        elif status == "Completed":
            grouped["completed"].append(record)
        else:
            grouped["upcoming"].append(record)

    return grouped


def generate_ics_calendar(records, filename="vaccine_schedule.ics"):
    """Export vaccine schedule records to an ICS calendar file."""
    from ics import Calendar, Event

    calendar = Calendar()

    for record in records:
        due_date = record.get("due_date")

        if due_date is None:
            continue

        event = Event()
        event.name = f"{record['vaccine']} - {record['status']}"
        event.begin = due_date
        event.make_all_day()

        calendar.events.add(event)

    with open(filename, "w", encoding="utf-8") as file:
        file.writelines(calendar)

    return filename
