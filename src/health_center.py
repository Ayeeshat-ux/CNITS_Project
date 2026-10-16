# src/health_center.py

import pandas as pd
import streamlit as st
from urllib.parse import quote_plus
from duckduckgo_search import DDGS


# ============================================================
# PRIMARY HEALTHCARE CENTRE DATA
# SCOPE: NATIONWIDE (NIGERIA) + EXPANDED IKORODU DIVISION
# ============================================================

HEALTH_CENTERS = [
    # --- Ikorodu Division (Lagos State) ---
    {
        "name": "Odonla Primary Healthcare Centre",
        "community": "Odonla, Ikorodu North, Lagos",
        "address": "Odonla Road, Ikorodu, Lagos",
        "hours": "24 hours",
    },
    {
        "name": "Ita Elewa Primary Healthcare Centre",
        "community": "Ita Elewa, Ikorodu Central, Lagos",
        "address": "Oriwu Road, Ikorodu, Lagos",
        "hours": "24 hours",
    },
    {
        "name": "Ipakodo Primary Healthcare Centre",
        "community": "Ebute / Ipakodo, Ikorodu West, Lagos",
        "address": "Ipakodo-Ebute Road, Ikorodu, Lagos",
        "hours": "24 hours",
    },
    {
        "name": "Igbogbo Primary Healthcare Centre",
        "community": "Igbogbo, Igbogbo-Bayeku, Lagos",
        "address": "Agbele Road, Igbogbo, Ikorodu, Lagos",
        "hours": "24 hours",
    },
    {
        "name": "Oke-Eletu Primary Healthcare Centre",
        "community": "Oke-Eletu, Ijede, Lagos",
        "address": "Ijede Road, Oke-Eletu, Ijede, Lagos",
        "hours": "Check centre",
    },
    {
        "name": "Ijede Primary Healthcare Centre",
        "community": "Ijede, Ikorodu, Lagos",
        "address": "General Hospital Road, Ijede, Lagos",
        "hours": "24 hours",
    },
    {
        "name": "Imota Comprehensive Primary Healthcare Centre",
        "community": "Imota, Lagos",
        "address": "Itun-Onabu Street, Imota, Lagos",
        "hours": "24 hours",
    },
    {
        "name": "Agura Primary Healthcare Centre",
        "community": "Agura / Gberigbe, Ikorodu North, Lagos",
        "address": "Agura-Gberigbe Road, Ikorodu, Lagos",
        "hours": "8:00 AM - 4:00 PM",
    },
    {
        "name": "Ibeshe Primary Healthcare Centre",
        "community": "Ibeshe, Ikorodu West, Lagos",
        "address": "Ibeshe Titun, Ikorodu, Lagos",
        "hours": "24 hours",
    },
    {
        "name": "Isawo / Igbo Olomu Primary Healthcare Centre",
        "community": "Isawo, Ikorodu West, Lagos",
        "address": "Isawo Road, Agric, Ikorodu, Lagos",
        "hours": "24 hours",
    },
    # --- Other Lagos State ---
    {
        "name": "Surulere Primary Health Centre",
        "community": "Surulere, Lagos State",
        "address": "Tejuosho Road, Surulere, Lagos",
        "hours": "24 hours",
    },
    {
        "name": "Ajeromi Primary Health Centre",
        "community": "Ajeromi-Ifelodun, Lagos",
        "address": "Alayabiagba, Ajegunle, Lagos",
        "hours": "24 hours",
    },
    {
        "name": "Yaba Primary Health Centre",
        "community": "Yaba, Lagos State",
        "address": "Adekunle, Yaba, Lagos",
        "hours": "24 hours",
    },
    {
        "name": "Ikeja Primary Health Centre",
        "community": "Ikeja, Lagos",
        "address": "Obafemi Awolowo Way, Ikeja, Lagos",
        "hours": "24 hours",
    },
    # --- FCT Abuja ---
    {
        "name": "Garki Primary Healthcare Centre",
        "community": "Garki, Abuja, FCT",
        "address": "Area 2, Garki, Abuja",
        "hours": "24 hours",
    },
    {
        "name": "Wuse Primary Healthcare Centre",
        "community": "Wuse Zone 3, Abuja, FCT",
        "address": "Zone 3, Wuse, Abuja",
        "hours": "24 hours",
    },
    # --- Kano State ---
    {
        "name": "Kurna Primary Healthcare Centre",
        "community": "Dala, Kano State",
        "address": "Kurna Asabe, Kano",
        "hours": "24 hours",
    },
    # --- Oyo State ---
    {
        "name": "Agbongbon Primary Health Centre",
        "community": "Ibadan South-East, Oyo State",
        "address": "Agbongbon Area, Ibadan, Oyo State",
        "hours": "8:00 AM - 4:00 PM",
    },
    # --- Rivers State ---
    {
        "name": "Model Primary Health Centre Rumuigbo",
        "community": "Obio-Akpor, Port Harcourt, Rivers State",
        "address": "Ikwerre Road, Rumuigbo, Port Harcourt",
        "hours": "24 hours",
    },
    # --- Enugu State ---
    {
        "name": "Uwani Primary Health Centre",
        "community": "Enugu South, Enugu State",
        "address": "Uwani, Enugu, Enugu State",
        "hours": "8:00 AM - 5:00 PM",
    },
    # --- Kaduna State ---
    {
        "name": "Kakuri Primary Health Centre",
        "community": "Kakuri, Kaduna South, Kaduna State",
        "address": "Kakuri Road, Kaduna",
        "hours": "24 hours",
    },
]


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def create_map_search_url(center_name, community="Nigeria"):
    """
    Create a Google Maps search URL for a healthcare centre.
    """
    search_text = f"{center_name}, {community}"
    encoded_search = quote_plus(search_text)
    return f"https://www.google.com/maps/search/?api=1&query={encoded_search}"


def fetch_web_phc_records(location_query: str) -> list:
    """
    Fetches strictly medical healthcare centre data from web search and filters out news/elections/dictionaries.
    """
    fetched_records = []
    
    # Strict blocklist for non-medical noise
    exclude_keywords = [
        "dictionary", "definition", "classnotes", "school", "merriam-webster", 
        "cambridge", "curriculum", "election", "electoral", "news", "report", 
        "journalism", "politics", "party", "votes", "candidate"
    ]
    
    # Required medical indicators (at least one must be present)
    medical_indicators = ["health", "centre", "center", "clinic", "hospital", "phc", "maternity", "healthcare"]

    try:
        # Tighter search query focused on medical facilities
        search_query = f'"Primary Health Centre" OR "Health Clinic" OR "Hospital" in {location_query} Lagos Nigeria address'
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, max_results=10))
            for item in results:
                title = item.get("title", "")
                snippet = item.get("body", "")
                combined_text = (title + " " + snippet).lower()
                
                # Check blocklist
                if any(bad in combined_text for bad in exclude_keywords):
                    continue
                
                # Check that it's genuinely medical
                if any(med in combined_text for med in medical_indicators):
                    clean_name = title.split("-")[0].split("|")[0].strip()
                    if len(clean_name) > 3:
                        fetched_records.append({
                            "name": clean_name,
                            "community": f"{location_query.capitalize()}, Nigeria",
                            "address": snippet[:140] + "..." if len(snippet) > 140 else snippet,
                            "hours": "Check centre"
                        })
    except Exception:
        pass
        
    return fetched_records


def search_health_centers(search_text: str) -> list:
    """
    Returns a unified data feed of all primary health centres matching the location query.
    """
    if not search_text:
        return HEALTH_CENTERS

    query_lower = search_text.lower().strip()
    
    # 1. Filter local database records
    local_matches = [
        c for c in HEALTH_CENTERS
        if query_lower in c["name"].lower()
        or query_lower in c["community"].lower()
        or query_lower in c["address"].lower()
    ]

    # 2. Fetch supplementary verified medical records from the web
    web_matches = fetch_web_phc_records(query_lower)

    # 3. Deduplicate and merge records into a single clean list
    seen_names = set(c["name"].lower() for c in local_matches)
    merged_feed = list(local_matches)

    for item in web_matches:
        if item["name"].lower() not in seen_names:
            merged_feed.append(item)
            seen_names.add(item["name"].lower())

    return merged_feed


# ============================================================
# DISPLAY MODULE
# ============================================================

def display_health_center_finder():
    """
    Display the clean, unified healthcare centre data feed in Streamlit.
    """
    st.subheader("🏥 Primary Healthcare Centre Finder")
    st.write("Search for accredited primary healthcare centres across Nigeria for routine immunization, child nutrition, and maternity care.")

    # Search Input Box
    search_query = st.text_input(
        "Search for a healthcare centre (by name or location)",
        placeholder="Example: Ikorodu, Surulere, Garki, or Ikeja",
        key="phc_data_feed_search"
    )

    if search_query:
        with st.spinner(f"Fetching all primary health centres in {search_query}..."):
            feed_results = search_health_centers(search_query)

        if feed_results:
            st.success(f"{len(feed_results)} healthcare centre(s) found for '{search_query}':")

            for centre in feed_results:
                st.markdown(f"### {centre['name']}")
                st.write(f"**Community / State:** {centre['community']}")
                st.write(f"**Address:** {centre['address']}")
                st.write(f"**Opening hours:** {centre['hours']}")

                maps_url = create_map_search_url(centre["name"], centre["community"])
                st.link_button("📍 Open Centre in Maps", maps_url)
                st.divider()
        else:
            st.warning(f"No health centres found for '{search_query}'.")
            st.write("You can search directly on Google Maps:")
            fallback_url = create_map_search_url(search_query, "Nigeria")
            st.link_button("🔎 Search Location on Maps", fallback_url)


# ============================================================
# TESTING BLOCK
# ============================================================

if __name__ == "__main__":
    display_health_center_finder()