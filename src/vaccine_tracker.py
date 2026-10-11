from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import Optional

from src.vaccine_data import HPV_SCHEDULE, VACCINE_SCHEDULE


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
    month = value.month - 1 + months
    year = value.year + month // 12
    month = month % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


def calculate_age(dob, as_of: Optional[date] = None) -> dict:
    """Calculate age in days, weeks, months, and years relative to a reference date."""
    dob_date = _to_date(dob)
    ref_date = _to_date(as_of) if as_of else date.today()

    if dob_date > ref_date:
        raise ValueError("Date of birth cannot be after the reference date.")

    total_days = (ref_date - dob_date).days
    total_weeks = total_days // 7

    years = ref_date.year - dob_date.year
    months = ref_date.month - dob_date.month
    days = ref_date.day - dob_date.day

    if days < 0:
        months -= 1
    if months < 0:
        years -= 1
        months += 12

    total_months = (years * 12) + months

    return {
        "years": years,
        "months_remainder": months,
        "total_months": total_months,
        "total_weeks": total_weeks,
        "total_days": total_days,
    }


def calculate_due_date(dob, unit: str, value: int) -> date:
    """Calculate target due date for a specific milestone."""
    dob_date = _to_date(dob)

    if unit == "days":
        return dob_date + timedelta(days=value)
    elif unit == "weeks":
        return dob_date + timedelta(weeks=value)
    elif unit == "months":
        return add_months(dob_date, value)
    elif unit == "years":
        return add_months(dob_date, value * 12)
    else:
        raise ValueError(f"Unsupported time unit: {unit}")


def determine_status(due_date: date, as_of: date) -> str:
    """Determine vaccination status based on due date vs current reference date."""
    if due_date < as_of:
        return "overdue"
    elif due_date == as_of:
        return "due_now"
    else:
        return "upcoming"


def build_vaccine_schedule(dob, as_of: Optional[date] = None) -> list:
    """Build the full NPHCDA vaccine schedule with calculated due dates and status."""
    dob_date = _to_date(dob)
    ref_date = _to_date(as_of) if as_of else date.today()

    schedule = []
    for entry in VACCINE_SCHEDULE:
        due_date = calculate_due_date(dob_date, entry["age_unit"], entry["age_value"])
        status = determine_status(due_date, ref_date)

        record = entry.copy()
        record["due_date"] = due_date
        record["due_date_label"] = due_date.strftime("%d %b %Y")
        record["status"] = status
        schedule.append(record)

    return schedule


def group_vaccines_by_status(schedule_records: list) -> dict:
    """Categorize schedule records by status for UI summary metrics."""
    grouped = {
        "overdue": [],
        "due_now": [],
        "upcoming": [],
        "completed": [],
    }

    for record in schedule_records:
        status = record.get("status", "upcoming")
        if status in grouped:
            grouped[status].append(record)

    return grouped