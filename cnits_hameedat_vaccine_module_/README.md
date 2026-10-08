# CNITS - Hameedat Vaccine Module

## Files

- `src/vaccine_data.py` - NPHCDA routine immunization schedule data.
- `src/vaccine_tracker.py` - age calculation, due dates, vaccine status grouping, and calendar export.
- `notebooks/hameedat_vaccine_tracker_test.ipynb` - prototype notebook for testing the logic before integration.
- `tests/test_vaccine_tracker.py` - automated checks for the date/status logic.

## Install for calendar export

Use the `ics` package:

```bash
pip install ics
```

Do **not** use the unrelated package named `python-ics`; the calendar library is `ics`.

## Important design choice

The NPHCDA source provides routine target ages. It does not provide a catch-up vaccination schedule. Therefore the tracker compares routine milestone dates against the child's recorded history and does not invent catch-up intervals.

For HPV, the source provides a 9-13 year age window and two doses 6 months apart, but no exact first-dose date. The tracker therefore treats dose 1 as window-based and calculates dose 2 from the recorded dose-1 administration date.
