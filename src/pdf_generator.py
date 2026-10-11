from io import BytesIO
from datetime import date
import streamlit as st

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.lib.units import mm

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


# ============================================================
# CHILD DIGITAL HEALTH PASSPORT PDF GENERATOR
# ============================================================

def generate_health_passport(
    child_info,
    vaccine_history,
    growth_logs
):
    """
    Generate a Child Digital Health Passport PDF.

    Parameters
    ----------
    child_info : dictionary
        Contains the child's basic information.

    vaccine_history : list of dictionaries
        Contains the child's vaccine records.

    growth_logs : list of dictionaries
        Contains the child's growth records.

    Returns
    -------
    bytes
        The generated PDF file.
    """

    # --------------------------------------------------------
    # CREATE PDF IN MEMORY
    # --------------------------------------------------------

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm
    )

    # --------------------------------------------------------
    # STYLES
    # --------------------------------------------------------

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PassportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        spaceAfter=12
    )

    heading_style = ParagraphStyle(
        "PassportHeading",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=10,
        spaceAfter=6
    )

    normal_style = ParagraphStyle(
        "PassportNormal",
        parent=styles["BodyText"],
        fontSize=9,
        spaceAfter=5
    )

    # Everything that will appear inside the PDF
    story = []

    # ========================================================
    # TITLE
    # ========================================================

    story.append(
        Paragraph(
            "Child Digital Health Passport",
            title_style
        )
    )

    story.append(
        Paragraph(
            "Child Nutrition and Health Support",
            normal_style
        )
    )

    story.append(Spacer(1, 8))

    # ========================================================
    # CHILD INFORMATION
    # ========================================================

    story.append(
        Paragraph(
            "1. Child Information",
            heading_style
        )
    )

    child_rows = [
        [
            "Name",
            child_info.get("name", "")
        ],

        [
            "Date of Birth",
            child_info.get(
                "date_of_birth",
                ""
            )
        ],

        [
            "Sex",
            child_info.get(
                "sex",
                ""
            )
        ],

        [
            "Health ID",
            child_info.get(
                "health_id",
                ""
            )
        ]
    ]

    child_table = Table(
        child_rows,
        colWidths=[
            45 * mm,
            125 * mm
        ]
    )

    child_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.lightgrey
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )
            ]
        )
    )

    story.append(child_table)

    # ========================================================
    # VACCINE HISTORY
    # ========================================================

    story.append(
        Paragraph(
            "2. Vaccine History",
            heading_style
        )
    )

    vaccine_rows = [
        [
            "Vaccine",
            "Date Given",
            "Status"
        ]
    ]

    for vaccine in vaccine_history:

        vaccine_rows.append(
            [
                vaccine.get(
                    "vaccine",
                    ""
                ),

                vaccine.get(
                    "date_given",
                    ""
                ),

                vaccine.get(
                    "status",
                    ""
                )
            ]
        )

    # If there are no vaccine records
    if len(vaccine_rows) == 1:

        vaccine_rows.append(
            [
                "No vaccine records",
                "",
                ""
            ]
        )

    vaccine_table = Table(
        vaccine_rows,
        colWidths=[
            70 * mm,
            50 * mm,
            50 * mm
        ],
        repeatRows=1
    )

    vaccine_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                )
            ]
        )
    )

    story.append(vaccine_table)

    # ========================================================
    # GROWTH LOG
    # ========================================================

    story.append(
        Paragraph(
            "3. Growth Log",
            heading_style
        )
    )

    growth_rows = [
        [
            "Date",
            "Weight (kg)",
            "Height (cm)"
        ]
    ]

    for record in growth_logs:

        growth_rows.append(
            [
                record.get(
                    "date",
                    ""
                ),

                str(
                    record.get(
                        "weight_kg",
                        ""
                    )
                ),

                str(
                    record.get(
                        "height_cm",
                        ""
                    )
                )
            ]
        )

    # If there are no growth records
    if len(growth_rows) == 1:

        growth_rows.append(
            [
                "No growth records",
                "",
                ""
            ]
        )

    growth_table = Table(
        growth_rows,
        colWidths=[
            60 * mm,
            55 * mm,
            55 * mm
        ],
        repeatRows=1
    )

    growth_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                )
            ]
        )
    )

    story.append(growth_table)

    # ========================================================
    # FOOTER / NOTE
    # ========================================================

    story.append(
        Spacer(1, 15)
    )

    story.append(
        Paragraph(
            "This document is a project-generated summary "
            "of the child's recorded health information.",
            normal_style
        )
    )

    story.append(
        Paragraph(
            "This document is not a medical diagnosis.",
            normal_style
        )
    )

    # ========================================================
    # BUILD PDF
    # ========================================================

    document.build(story)

    # Move to beginning of file
    buffer.seek(0)

    # Return the PDF
    return buffer.getvalue()


# ============================================================
# STREAMLIT UI RENDER FUNCTION
# ============================================================

def render_pdf_generator():
    """
    Render the PDF Health Passport generator UI in Streamlit.
    """
    st.subheader("📄 Child Digital Health Passport Generator")
    st.write("Generate and download an official summary report of the child's health, vaccine history, and growth logs.")

    with st.form("pdf_form"):
        st.markdown("### Child Details")
        c_name = st.text_input("Child's Full Name", value="Amina Bello")
        c_dob = st.date_input("Date of Birth", value=date(2026, 1, 1))
        c_sex = st.selectbox("Sex", ["Female", "Male"])
        c_id = st.text_input("Health ID / Registration Number", value="CNITS-2026-001")

        submitted = st.form_submit_button("Generate PDF Passport")

    if submitted:
        child_info = {
            "name": c_name,
            "date_of_birth": str(c_dob),
            "sex": c_sex,
            "health_id": c_id
        }

        sample_vaccines = [
            {"vaccine": "BCG", "date_given": str(c_dob), "status": "Completed"},
            {"vaccine": "OPV 0", "date_given": str(c_dob), "status": "Completed"},
            {"vaccine": "Penta 1", "date_given": "2026-03-01", "status": "Due Now"}
        ]

        sample_growth = [
            {"date": str(c_dob), "weight_kg": 3.2, "height_cm": 50.0},
            {"date": "2026-03-01", "weight_kg": 5.4, "height_cm": 58.2}
        ]

        pdf_bytes = generate_health_passport(child_info, sample_vaccines, sample_growth)

        st.success("Health Passport PDF generated successfully!")
        st.download_button(
            label="📥 Download Health Passport (PDF)",
            data=pdf_bytes,
            file_name=f"{c_name.replace(' ', '_')}_Health_Passport.pdf",
            mime="application/pdf"
        )