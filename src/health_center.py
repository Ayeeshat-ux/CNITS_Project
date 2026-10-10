import pandas as pd
import streamlit as st
from urllib.parse import quote_plus


# ============================================================
# PRIMARY HEALTHCARE CENTRE DATA
# CASE STUDY: IKORODU, LAGOS
# ============================================================

HEALTH_CENTERS = [
    {
        "name": "Odonla Primary Healthcare Centre",
        "community": "Odonla, Ikorodu North",
        "address": "Odonla Road, Ikorodu, Lagos",
        "latitude": 6.6712864,
        "longitude": 3.5347337,
        "hours": "24 hours",
    },

    {
        "name": "Ita Elewa Primary Healthcare Centre",
        "community": "Ita Elewa, Ikorodu",
        "address": "Oriwu Road, Ikorodu, Lagos",
        "latitude": 6.60642,
        "longitude": 3.50857,
        "hours": "Check centre",
    },

    {
        "name": "Oke-Eletu Primary Healthcare Centre",
        "community": "Oke-Eletu, Ijede",
        "address": "Ijede Road, Oke-Eletu, Ijede, Lagos",
        "latitude": 6.599722,
        "longitude": 3.583056,
        "hours": "Check centre",
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
    community="Ikorodu, Lagos"
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
    by centre name or community.
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
        "Search for a primary healthcare centre "
        "in or around Ikorodu."
    )

    # --------------------------------------------------------
    # SEARCH BOX
    # --------------------------------------------------------

    search = st.text_input(
        "Search for a healthcare centre",
        placeholder="Example: Odonla PHC"
    )

    # --------------------------------------------------------
    # SEARCH RESULT
    # --------------------------------------------------------

    if search:

        results = search_health_centers(search)

        if not results.empty:

            st.success(
                f"{len(results)} centre(s) found "
                "in our local data."
            )

            for _, centre in results.iterrows():

                st.markdown(
                    f"### {centre['name']}"
                )

                st.write(
                    f"**Community:** "
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
                "Ikorodu, Lagos"
            )

            st.link_button(
                "🔎 Search Centre on Maps",
                web_search_url
            )

    # --------------------------------------------------------
    # INTERACTIVE MAP
    # --------------------------------------------------------

    st.subheader(
        "📍 Primary Healthcare Centres in Ikorodu"
    )

    st.write(
        "The map shows healthcare centres "
        "available in our local project dataset."
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
        zoom=11,
        height=450
    )


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":

    display_health_center_finder()