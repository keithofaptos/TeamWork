import streamlit as st
import requests
import csv
import re
import geocoder
import psutil
import os
import json
from bs4 import BeautifulSoup
import time
import pandas as pd
from io import StringIO
import matplotlib.pyplot as plt
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
import folium
from streamlit_folium import st_folium

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "data/compiled_business_listing_data.csv")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            config = json.load(file)
        return config
    return {}

def save_config(api_key, cse_id):
    config = {
        "API_KEY": api_key,
        "CSE_ID": cse_id
    }
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file)

def show_instructions():
    st.markdown("""
    ## How to get your Google API Key and Custom Search Engine ID (CSE ID)
    
    ### Step 1: Get a Google API Key
    1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
    2. Click on the project drop-down and select or create the project for which you want to add an API key.
    3. Use the navigation menu to navigate to **APIs & Services > Credentials**.
    4. Click on **Create credentials**, then select **API key**.
    5. An API key will be generated and displayed. Copy this key to use in the application.

    ### Step 2: Enable the required APIs
    1. In the Google Cloud Console, navigate to **APIs & Services > Library**.
    2. Search for and enable the **Places API**.
    3. Search for and enable the **Custom Search JSON API**.

    ### Step 3: Get a Custom Search Engine ID (CSE ID)
    1. Go to the [Custom Search Engine](https://cse.google.com/cse/) page.
    2. Click on **Add** to create a new search engine.
    3. In the **Sites to search** box, enter any valid URL (you can change this later).
    4. Click **Create**.
    5. Once created, click on **Control Panel**.
    6. Copy the **Search engine ID** displayed at the top right corner of the page.

    ### Step 4: Save the API Key and CSE ID in the application
    1. Enter the API Key and CSE ID in the sidebar of this application.
    2. Click the **Save API Settings** button to store your settings.
    """)

def load_existing_data(output_file):
    if os.path.exists(output_file):
        return pd.read_csv(output_file)
    return pd.DataFrame(columns=["Name", "Address", "Types", "Website", "Email", "Phone Number", "Rating", "Business Type", "Keyword"])

def plot_keywords(data):
    keywords_count = data['Keyword'].value_counts()
    fig, ax = plt.subplots()
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#0e1117')
    keywords_count.plot(kind='barh', ax=ax, color='green')
    ax.set_title('Keywords Distribution', color='white')
    ax.set_xlabel('Count', color='white')
    ax.set_ylabel('Keywords', color='white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    st.pyplot(fig)

def get_lat_long_from_city_state(city, state):
    if not city or not state:
        st.warning("City and State must be provided.")
        return None

    headers = {
        'User-Agent': 'MyApp/1.0 (myemail@example.com)',
        'Referer': 'http://yourwebsite.com'
    }
    
    try:
        response = requests.get(
            f"https://nominatim.openstreetmap.org/search?city={city}&state={state}&format=json&email=myemail@example.com",
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        if data:
            latitude = data[0].get("lat", "")
            longitude = data[0].get("lon", "")
            return float(latitude), float(longitude)
        else:
            st.warning("Location not found. Using auto-geocoding.")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"HTTP error occurred: {e}")
        return None
    except json.decoder.JSONDecodeError:
        st.error(f"Error decoding JSON response: {response.text}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None

def get_user_location(location_type, city=None, state=None, location=None):
    if location_type == "Auto-geocoding":
        try:
            user_location = geocoder.ip('me')
            if user_location.latlng:
                latitude, longitude = user_location.latlng
                return latitude, longitude
            else:
                st.warning("Unable to determine user's location.")
        except Exception as e:
            st.error(f"Error while getting user location: {e}")
    elif location_type == "City and State":
        return get_lat_long_from_city_state(city, state)
    elif location_type == "Latitude and Longitude":
        try:
            latitude, longitude = map(float, location.split(","))
            return latitude, longitude
        except ValueError:
            st.warning("Invalid latitude and longitude format.")
            return None
    
    st.warning("Using default location: Washington, PA")
    return 40.1740, -80.2462  # Default to Washington, PA if all else fails

def get_website_from_google_search(business_name, API_KEY, CSE_ID):
    try:
        response = requests.get(
            f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={CSE_ID}&q={business_name}"
        )
        response.raise_for_status()
        data = response.json()
        website = data.get("items", [{}])[0].get("link", "")
    except Exception as e:
        st.warning(f"Error getting website address for {business_name}: {e}")
        website = ""
    return website

def get_email_address(business_name, API_KEY, CSE_ID):
    try:
        response = requests.get(
            f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={CSE_ID}&q={business_name}",
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])
        email = ""

        email_regex = r'[\w\.-]+@[\w\.-]+'

        for item in items:
            snippet = item.get("snippet", "")
            email_match = re.search(email_regex, snippet)
            if email_match:
                email = email_match.group()
                break

        if not email:
            website = get_website_from_google_search(business_name, API_KEY, CSE_ID)
            if website:
                response = requests.get(website, timeout=30)
                soup = BeautifulSoup(response.text, 'html.parser')

                email_tags = soup.find_all('a', href=True)
                for tag in email_tags:
                    if 'mailto:' in tag['href']:
                        email = tag['href'][7:]
                        break

    except Exception as e:
        st.warning(f"Error getting email address for {business_name}: {e}")
        email = ""

    return email

def get_phone_number(business_name, API_KEY):
    try:
        response = requests.get(
            f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={business_name}&inputtype=textquery&key={API_KEY}"
        )
        data = response.json()
        candidates = data.get("candidates", [])
        if candidates:
            place_id = candidates[0].get("place_id", "")
            if place_id:
                details_response = requests.get(
                    f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={API_KEY}"
                )
                details_data = details_response.json()
                phone_number = details_data.get("result", {}).get("formatted_phone_number", "")
            else:
                phone_number = ""
        else:
            phone_number = ""
    except Exception as e:
        st.warning(f"Error getting phone number for {business_name}: {e}")
        phone_number = ""
    return phone_number

def get_rating(business_name, API_KEY):
    try:
        response = requests.get(
            f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={business_name}&inputtype=textquery&key={API_KEY}"
        )
        data = response.json()
        candidates = data.get("candidates", [])
        if candidates:
            place_id = candidates[0].get("place_id", "")
            if place_id:
                details_response = requests.get(
                    f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={API_KEY}"
                )
                details_data = details_response.json()
                rating = details_data.get("result", {}).get("rating", "")
            else:
                rating = ""
        else:
            rating = ""
    except Exception as e:
        st.warning(f"Error getting rating for {business_name}: {e}")
        rating = ""
    return rating

def generate_keywords(seed_keyword, num_keywords):
    prompt = f"Remember you are writing keywords into a CSV file format. Without numbering or extra quotes, one keyword per line. Only generate the list of words. Do NOT include a title or any kind of label, or definition, or explanation, just the list. You are generating keywords for a business lead search. So be mindful that the user expects results that would be related to their seed keyword in relation to local businesses. Generate {num_keywords} keyword variations for: {seed_keyword}"
    
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={'model': 'llama3:8b-instruct-fp16', 'prompt': prompt, 'context': []},
            stream=True
        )
        response.raise_for_status()
        
        full_response = ""
        for line in response.iter_lines():
            body = json.loads(line)
            response_part = body.get('response', '')
            full_response += response_part

            if 'error' in body:
                raise Exception(body['error'])

            if body.get('done', False):
                break
        
        keywords = full_response.strip().split("\n")
        return [keyword.strip() for keyword in keywords if keyword.strip()]
    except Exception as e:
        st.error(f"Error generating keywords: {e}")
        return []

def generate_leads(keywords, location, API_KEY, CSE_ID, business_type, radius, max_results):
    all_results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, keyword in enumerate(keywords):
        results_written = 0
        next_page_token = None

        while results_written < max_results:
            request_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={radius}&type={business_type}&keyword={keyword}&key={API_KEY}"
            if next_page_token:
                request_url += f"&pagetoken={next_page_token}"

            response = requests.get(request_url)
            data = response.json()
            
            results = data.get("results", [])
            
            for result in results:
                website = get_website_from_google_search(result.get("name", ""), API_KEY, CSE_ID)
                email = get_email_address(result.get("name", ""), API_KEY, CSE_ID)
                phone_number = get_phone_number(result.get("name", ""), API_KEY)
                rating = get_rating(result.get("name", ""), API_KEY)

                all_results.append([
                    result.get("name", ""),
                    result.get("vicinity", ""),
                    tuple(result.get("types", [])),  # Convert list to tuple
                    website,
                    email,
                    phone_number,
                    rating,
                    business_type,
                    keyword
                ])
                results_written += 1

                progress = min((idx * max_results + results_written) / (len(keywords) * max_results), 1.0)
                progress_bar.progress(progress)
                status_text.text(f"Processing: Keyword {idx+1}/{len(keywords)}, Result {results_written}/{max_results}")

                cpu_percent = psutil.cpu_percent()
                memory_percent = psutil.virtual_memory().percent
                st.sidebar.text(f"CPU: {cpu_percent:.2f}% | RAM: {memory_percent:.2f}%")

                if results_written >= max_results:
                    break

            next_page_token = data.get("next_page_token", None)
            if not next_page_token:
                break

            time.sleep(2)  # To avoid hitting API rate limits

    status_text.text("Processing complete!")
    return all_results

def append_to_csv(new_results, output_file):
    if os.path.exists(output_file):
        existing_data = pd.read_csv(output_file)
        new_data = pd.DataFrame(new_results, columns=existing_data.columns)
        # Convert 'Types' column to tuple for deduplication
        existing_data['Types'] = existing_data['Types'].apply(eval).apply(tuple)
        new_data['Types'] = new_data['Types'].apply(tuple)
        combined_data = pd.concat([existing_data, new_data]).drop_duplicates().reset_index(drop=True)
        combined_data.to_csv(output_file, index=False)
    else:
        new_data = pd.DataFrame(new_results, columns=["Name", "Address", "Types", "Website", "Email", "Phone Number", "Rating", "Business Type", "Keyword"])
        new_data.drop_duplicates().to_csv(output_file, index=False)

def run_lead_generator():
    # Load existing configuration
    config = load_config()

    # Sidebar for API keys and configuration
    with st.sidebar.expander("API Configuration", expanded=False):
        if st.button("❓"):
            show_instructions()
        API_KEY = st.text_input("Enter Google Maps API Key", value=config.get("API_KEY", ""), type="password")
        CSE_ID = st.text_input("Enter Custom Search Engine ID", value=config.get("CSE_ID", ""), type="password")

        if st.button("Save API Settings"):
            save_config(API_KEY, CSE_ID)
            st.success("API settings saved!")

    # Main app layout
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        location_type = st.radio("Choose location input method:", 
                                 ["Auto-geocoding", "City and State", "Latitude and Longitude"])

        city = state = location = None  # Initialize variables

        if location_type == "City and State":
            city = st.text_input("Enter your city:")
            state = st.text_input("Enter your state:")
        elif location_type == "Latitude and Longitude":
            location = st.text_input("Enter your location as latitude,longitude:")
        seed_keyword = st.text_input("Enter a seed keyword for variations:")
        num_keywords = st.number_input("Number of keyword variations", min_value=1, max_value=50, value=10)

    with col2:
        radius = st.slider("Search radius (in meters)", 1000, 50000, 50000, 1000)
        business_type = st.selectbox("Select a type of business (Optional):", 
            ["", "accounting", "airport", "amusement_park", "aquarium", "art_gallery", "atm", "bakery", "bank", "bar", "beauty_salon", "bicycle_store", "book_store", "bowling_alley", "bus_station", "cafe", "car_dealership", "car_rental", "car_repair", "car_wash", "casino", "cemetery", "child_care", "clothing_store", "convenience_store", "courthouse", "dentist", "department_store", "doctor", "electrician", "electronics_store", "embassy", "employment_agency", "entertainment_complex", "event_space", "financial_advisor", "florist", "food_court", "funeral_home", "furniture_store", "gas_station", "general_contractor", "grocery_or_supermarket", "gym", "hair_salon", "hardware_store", "health_spa", "home_goods_store", "hospital", "hotel", "insurance_agency", "jewelry_store", "laundry_mat", "lawyer", "library", "liquor_store", "local_government_office", "locksmith", "lodging", "meal_delivery", "meal_takeaway", "mechanic", "movie_theater", "museum", "night_club", "painter", "park", "pharmacy", "physiotherapist", "plumber", "police_station", "post_office", "primary_school", "real_estate_agency", "restaurant", "roofer", "school", "secondary_school", "shopping_mall", "spa", "stadium", "storage", "store", "subway_station", "supermarket", "taxi_stand", "tourist_attraction", "train_station", "university", "veterinarian", "zoo"])
        max_results = st.number_input("Maximum number of results per keyword", min_value=1, max_value=60, value=1)

    with col3:
        location = get_user_location(location_type, city, state, location)
        if location:
            m = folium.Map(location=location, zoom_start=12)
            folium.Marker(location=location).add_to(m)
            st_folium(m, width=500, height=300)

    if st.button("Generate Leads"):
        if not API_KEY or not CSE_ID:
            st.error("Please enter all required API keys in the sidebar.")
        else:
            with st.spinner("Generating keywords..."):
                keywords = generate_keywords(seed_keyword, num_keywords)
                st.write("Generated Keywords:", keywords)

            with st.spinner("Generating leads..."):
                all_results = generate_leads(keywords, f"{location[0]},{location[1]}", API_KEY, CSE_ID, business_type, radius, max_results)
                append_to_csv(all_results, OUTPUT_FILE)
                st.success("Leads generated successfully!")  # Add a success message instead of rerunning

    # Load existing data
    existing_data = load_existing_data(OUTPUT_FILE)

    # Display existing data
    st.subheader("Leads List")
    grid_options = GridOptionsBuilder.from_dataframe(existing_data)
    grid_options.configure_default_column(editable=True)
    grid_options = grid_options.build()
    
    # Use st.empty() to create a placeholder for the AgGrid
    grid_placeholder = st.empty()
    
    # Display the AgGrid in the placeholder
    with grid_placeholder:
        edited_data = AgGrid(existing_data, gridOptions=grid_options, update_mode="value_changed", columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS)

    # Save edited data
    if st.button("Save Changes"):
        if edited_data['data'].equals(existing_data):
            st.write("No changes to save.")
        else:
            edited_df = pd.DataFrame(edited_data['data'])
            edited_df.to_csv(OUTPUT_FILE, index=False)
            st.success("Changes saved!")

    # Plot keywords
    plot_keywords(existing_data)

# Run the lead generator application
if __name__ == "__main__":
    run_lead_generator()
