from datetime import date

from src.vaccine_tracker import add_months, build_vaccine_schedule, calculate_age, group_vaccines_by_status


def test_add_months_end_of_month():
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)


def test_calculate_age():
    age = calculate_age("2026-01-01", "2026-03-01")
    assert age["total_days"] == 59
    assert age["total_weeks"] == 8


def test_fixed_milestone_dates():
    records = build_vaccine_schedule("2026-01-01", as_of="2026-02-12")
    by_id = {record["id"]: record for record in records}
    assert by_id["bcg_birth"]["due_date"] == date(2026, 1, 1)
    assert by_id["pentavalent1_6w"]["due_date"] == date(2026, 2, 12)
    assert by_id["pentavalent1_6w"]["status"] == "Due Now"


def test_history_marks_completed():
    records = build_vaccine_schedule(
        "2026-01-01",
        vaccination_history={"bcg_birth": "2026-01-01"},
        as_of="2026-02-12",
    )
    by_id = {record["id"]: record for record in records}
    assert by_id["bcg_birth"]["status"] == "Completed"


def test_grouping_contains_requested_buckets():
    records = build_vaccine_schedule("2026-01-01", as_of="2026-05-01")
    grouped = group_vaccines_by_status(records)
    assert set(grouped) == {"overdue", "due_now", "upcoming", "completed"}
    assert grouped["overdue"]
    assert grouped["upcoming"]


def test_hpv_dose_1_is_windowed():
    records = build_vaccine_schedule("2018-06-01", as_of="2027-06-01")
    hpv1 = next(record for record in records if record["id"] == "hpv1")
    assert hpv1["status"] == "Due Now"
    assert hpv1["is_windowed"] is True
    assert hpv1["due_date"] is None
    assert hpv1["window_start"] == date(2027, 6, 1)
    assert hpv1["window_end"] == date(2031, 6, 1)


def test_hpv_dose_2_uses_recorded_dose_1_date():
    records = build_vaccine_schedule(
        "2018-06-01",
        vaccination_history={"hpv1": "2027-07-15"},
        as_of="2027-12-01",
    )
    hpv2 = next(record for record in records if record["id"] == "hpv2")
    assert hpv2["due_date"] == date(2028, 1, 15)
    assert hpv2["status"] == "Upcoming"
