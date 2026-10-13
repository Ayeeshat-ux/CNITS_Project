# src/health_center.py

import pandas as pd
import streamlit as st
from urllib.parse import quote_plus


# ============================================================
# PRIMARY HEALTHCARE CENTRE DATA
# SCOPE: NATIONWIDE (NIGERIA)
# ============================================================

HEALTH_CENTERS = [
    # Lagos State
    {
        "name": "Surulere Primary Health Centre",
        "community": "Surulere, Lagos State",
        "address": "Tejuosho Road, Surulere, Lagos",
        "latitude": 6.5059,
        "longitude": 3.3610,
        "hours": "24 hours",
    },
    {
        "name": "Odonla Primary Healthcare Centre",
        "community": "Odonla, Ikorodu North, Lagos",
        "address": "Odonla Road, Ikorodu, Lagos",
        "latitude": 6.6712864,
        "longitude": 3.5347337,
        "hours": "24 hours",
    },
    {
        "name": "Ita Elewa Primary Healthcare Centre",
        "community": "Ita Elewa, Ikorodu, Lagos",
        "address": "Oriwu Road, Ikorodu, Lagos",
        "latitude": 6.60642,
        "longitude": 3.50857,
        "hours": "Check centre",
    },
    {
        "name": "Oke-Eletu Primary Healthcare Centre",
        "community": "Oke-Eletu, Ijede, Lagos",
        "address": "Ijede Road, Oke-Eletu, Ijede, Lagos",
        "latitude": 6.599722,
        "longitude": 3.583056,
        "hours": "Check centre",
    },
    {
        "name": "Ikeja Primary Health Centre",
        "community": "Ikeja, Lagos",
        "address": "Obafemi Awolowo Way, Ikeja, Lagos",
        "latitude": 6.5965,
        "longitude": 3.3421,
        "hours": "24 hours",
    },
    # FCT Abuja
    {
        "name": "Garki Primary Healthcare Centre",
        "community": "Garki, Abuja, FCT",
        "address": "Area 2, Garki, Abuja",
        "latitude": 9.0333,
        "longitude": 7.4833,
        "hours": "24 hours",
    },
    # Kano State
    {
        "name": "Kurna Primary Healthcare Centre",
        "community": "Dala, Kano State",
        "address": "Kurna Asabe, Kano",
        "latitude": 12.0300,
        "longitude": 8.5100,
        "hours": "24 hours",
    },
    # Oyo State
    {
        "name": "Agbongbon Primary Health Centre",
        "community": "Ibadan South-East, Oyo State",
        "address": "Agbongbon Area, Ibadan, Oyo State",
        "latitude": 7.3775,
        "longitude": 3.9059,
        "hours": "8:00 AM - 4:00 PM",
    },
    # Rivers State
    {
        "name": "Model Primary Health Centre Rumuigbo",
        "community": "Obio-Akpor, Port Harcourt, Rivers State",
        "address": "Ikwerre Road, Rumuigbo, Port Harcourt",
        "latitude": 4.8500,
        "longitude": 6.9833,
        "hours": "24 hours",
    },
    # Enugu State
    {
        "name": "Uwani Primary Health Centre",
        "community": "Enugu South, Enugu State",
        "address": "Uwani, Enugu, Enugu State",
        "latitude": 6.4333,
        "longitude": 7.4833,
        "hours": "8:00 AM - 5:00 PM",
    },
    # Kaduna State
    {
        "name": "Kakuri Primary Health Centre",
        "community": "Kakuri, Kaduna South, Kaduna State",
        "address": "Kakuri Road, Kaduna",
        "latitude": 10.4828,
        "longitude": 7.4223,
        "hours": "24 hours",
    },
]


# ============================================================
# FUNCTION 1: GET HEALTH CENTRE DATA
# ============================================================

def get_health_centers():
    """
    Convert the healthcare centre data into
    a pandas DataFrame.
    """
    return pd.DataFrame(HEALTH_CENTERS)


# ============================================================
# FUNCTION 2: CREATE WEB SEARCH LINK
# ============================================================

def create_map_search_url(
    center_name,
    community="Nigeria"
):
    """
    Create a Google Maps search URL for a
    healthcare centre.
    """
    search_text = f"{center_name}, {community}"
    encoded_search = quote_plus(search_text)
    url = (
        "https://www.google.com/maps/search/"
        "?api=1&query="
        + encoded_search
    )
    return url


# ============================================================
# FUNCTION 3: SEARCH HEALTH CENTRES
# ============================================================

def search_health_centers(search_text):
    """
    Search the local healthcare centre data
    by centre name, community, or address.
    """
    df = get_health_centers()

    if not search_text:
        return df

    results = df[
        df["name"].str.contains(
            search_text,
            case=False,
            na=False
        )
        |
        df["community"].str.contains(
            search_text,
            case=False,
            na=False
        )
        |
        df["address"].str.contains(
            search_text,
            case=False,
            na=False
        )
    ]

    return results


# ============================================================
# FUNCTION 4: DISPLAY HEALTH CENTRE FINDER
# ============================================================

def display_health_center_finder():
    """
    Display the healthcare centre search,
    map and web search option in Streamlit.
    """

    st.subheader(
        "🏥 Primary Healthcare Centre Finder"
    )

    st.write(
        "Search for primary healthcare centres "
        "across Nigeria for routine immunization and nutrition support."
    )

    # --------------------------------------------------------
    # SEARCH BOX
    # --------------------------------------------------------

    search = st.text_input(
        "Search for a healthcare centre (by name or location)",
        placeholder="Example: Surulere PHC or Garki Abuja"
    )

    # --------------------------------------------------------
    # SEARCH RESULT
    # --------------------------------------------------------

    if search:

        results = search_health_centers(search)

        if not results.empty:

            st.success(
                f"{len(results)} centre(s) found "
                "in our national database."
            )

            for _, centre in results.iterrows():

                st.markdown(
                    f"### {centre['name']}"
                )

                st.write(
                    f"**Community / State:** "
                    f"{centre['community']}"
                )

                st.write(
                    f"**Address:** "
                    f"{centre['address']}"
                )

                st.write(
                    f"**Opening hours:** "
                    f"{centre['hours']}"
                )

                # Create Google Maps search link
                maps_url = create_map_search_url(
                    centre["name"],
                    centre["community"]
                )

                st.link_button(
                    "📍 Open Centre in Maps",
                    maps_url
                )

                st.divider()

        else:

            st.warning(
                "This centre is not available "
                "in our local list."
            )

            st.write(
                "You can search for it directly "
                "on Google Maps."
            )

            web_search_url = create_map_search_url(
                search,
                "Nigeria"
            )

            st.link_button(
                "🔎 Search Centre on Maps",
                web_search_url
            )

    # --------------------------------------------------------
    # INTERACTIVE MAP
    # --------------------------------------------------------

    st.subheader(
        "📍 Primary Healthcare Centres across Nigeria"
    )

    st.write(
        "The map shows accredited healthcare centres "
        "available in our national project database."
    )

    df = get_health_centers()

    map_data = df[
        [
            "latitude",
            "longitude"
        ]
    ]

    st.map(
        map_data,
        latitude="latitude",
        longitude="longitude",
        zoom=6,
        height=450
    )


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":

    display_health_center_finder()