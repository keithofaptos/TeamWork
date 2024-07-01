import requests
import csv
import tqdm
import re
import termcolor
import geocoder
import psutil
from bs4 import BeautifulSoup
import branding

branding.print_title()

print(termcolor.colored("The script will scrape Google Maps for businesses near your location and create a CSV file with up to 60 business listings. It will use the Google Maps Places API key and custom search engine ID that you provide. Google Maps Places API has a daily limit of 2000 requests per day. If you exceed this limit, your requests will be throttled.", "magenta", attrs=["bold"]))

def get_website_from_google_search(business_name, api_key, cse_id):
    try:
        response = requests.get(
            f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cse_id}&q={business_name}"
        )
        response.raise_for_status()  # Check for HTTP request errors
        data = response.json()
        website = data.get("items", [{}])[0].get("link", "")
    except Exception as e:
        # Handle the error
        print(f"Error getting website address for {business_name}: {e}")
        website = ""
    return website

def get_email_address(business_name, api_key, cse_id):
    try:
        response = requests.get(
            f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cse_id}&q={business_name}",
            timeout=30  # Add a timeout of 30 seconds
        )
        response.raise_for_status()  # Check for HTTP request errors
        data = response.json()
        items = data.get("items", [])
        email = ""

        # Check if there are search results
        if items:
            # Define a more robust email regex pattern
            email_regex = r'[\w\.-]+@[\w\.-]+'

            # Iterate through the search results and find an email address
            for item in items:
                snippet = item.get("snippet", "")
                email_match = re.search(email_regex, snippet)
                if email_match:
                    email = email_match.group()
                    break  # Stop searching after finding the first email address

        # If no email found using the previous method, try web scraping
        if not email:
            website = get_website_from_google_search(business_name, api_key, cse_id)
            if website:
                response = requests.get(website, timeout=30)  # Add a timeout here as well
                soup = BeautifulSoup(response.text, 'html.parser')

                # Look for email addresses in the page's text content
                email_tags = soup.find_all('a', href=True)
                for tag in email_tags:
                    if 'mailto:' in tag['href']:
                        email = tag['href'][7:]
                        break

    except Exception as e:
        print(f"Error getting email address for {business_name}: {e}")
        email = ""

    return email

def get_phone_number(business_name, api_key):

    try:
        response = requests.get(
            f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={business_name}&inputtype=textquery&key={api_key}"
        )
        data = response.json()
        candidates = data.get("candidates", [])
        if candidates:
            place_id = candidates[0].get("place_id", "")
            if place_id:
                details_response = requests.get(
                    f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={api_key}"
                )
                details_data = details_response.json()
                phone_number = details_data.get("result", {}).get("formatted_phone_number", "")
            else:
                phone_number = ""
        else:
            phone_number = ""
    except Exception as e:
        print(f"Error getting phone number for {business_name}: {e}")
        phone_number = ""
    return phone_number

def get_rating(business_name, api_key):

    try:
        response = requests.get(
            f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={business_name}&inputtype=textquery&key={api_key}"
        )
        data = response.json()
        candidates = data.get("candidates", [])
        if candidates:
            place_id = candidates[0].get("place_id", "")
            if place_id:
                details_response = requests.get(
                    f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={api_key}"
                )
                details_data = details_response.json()
                rating = details_data.get("result", {}).get("rating", "")
            else:
                rating = ""
        else:
            rating = ""
    except Exception as e:
        print(f"Error getting rating for {business_name}: {e}")
        rating = ""
    return rating

def get_lat_long_from_city_state(city, state):
    try:
        response = requests.get(
            f"https://nominatim.openstreetmap.org/search?city={city}&state={state}&format=json"
        )
        data = response.json()
        if data:
            latitude = data[0].get("lat", "")
            longitude = data[0].get("lon", "")
            return f"{latitude},{longitude}"
        else:
            print("Location not found. Using auto-geocoding.")
            return None
    except Exception as e:
        print(f"Error getting latitude and longitude for {city}, {state}: {e}")
        return None

def get_location_from_user():
    location_type = input("Enter '1' to enter your location as city and state, '2' to enter latitude and longitude, or press Enter to use auto-geocoding: ")
    if location_type == '1':
        city = input("Enter your city: ")
        state = input("Enter your state: ")
        lat_long = get_lat_long_from_city_state(city, state)
        if lat_long:
            return lat_long
        else:
            return None
    elif location_type == '2':
        location = input("Enter your location as latitude,longitude: ")
        return location
    else:
        return None

def get_user_location():
    location = get_location_from_user()
    if location:
        return location
    try:
        # Use the geocoder module to get the user's current location
        user_location = geocoder.ip('me')
        if user_location.latlng:
            latitude, longitude = user_location.latlng
            return f"{latitude},{longitude}"
        else:
            print("Unable to determine user's location.")
    except Exception as e:
        print(f"Error while getting user location: {e}")

    print("Using default location.")
    return "40.1740,-80.2462"  # Default to Washington, PA if all else fails
    #return "40.440624,-79.995888"  # Default to Pittsburgh if all else fails

location = get_user_location()

if __name__ == "__main__":
    # Get the Google Maps Places API key and custom search engine ID
    API_KEY = "AIzaSyC14WbUBVkpQka1t6YQ9z_HwRsXAJyN81k"
    CSE_ID = "633c1ded6ed1f4838"
    radius = 50000

    print(termcolor.colored("Type in one of these Business Types exactly as it appears here, into the prompt below, or just hit enter to ignore it. Using this can greatly limit the results and should be used accurately and sparingly. You will get more results by hitting enter here, skipping the Type, and just entering a keyword on the next prompt.", "yellow", attrs=["bold"]))
    print(termcolor.colored("accounting, airport, amusement_park, aquarium, art_gallery, atm, bakery, bank, bar, beauty_salon, bicycle_store, book_store, bowling_alley, bus_station, cafe, car_dealership, car_rental, car_repair, car_wash, casino, cemetery, child_care, clothing_store, convenience_store, courthouse, dentist, department_store, doctor, electrician, electronics_store, embassy, employment_agency, entertainment_complex, event_space, financial_advisor, florist, food_court, funeral_home, furniture_store, gas_station, general_contractor, grocery_or_supermarket, gym, hair_salon, hardware_store, health_spa, home_goods_store, hospital, hotel, insurance_agency, jewelry_store, laundry_mat, lawyer, library, liquor_store, local_government_office, locksmith, lodging, meal_delivery, meal_takeaway, mechanic, movie_theater, museum, night_club, painter, park, pharmacy, physiotherapist, plumber, police_station, post_office, primary_school, real_estate_agency, restaurant, roofer, school, secondary_school, shopping_mall, spa, stadium, storage, store, subway_station, supermarket, taxi_stand, tourist_attraction, train_station, university, veterinarian, zoo", "green", attrs=["bold"]))
    business_type = input("Enter a type of business to search for: ")

    print(termcolor.colored("Type in a search keyword here. If you don't see what you're looking for in the Types list, then this field will prove more useful. Or, you can also use both for something like... Type: restaurant / Keyword: pizza", "yellow", attrs=["bold"]))
    print(termcolor.colored("Keyword Examples: pizza, sushi, tarot, art, records, bookstore, shoes, etc.", "green", attrs=["bold"]))
    keyword = input("Enter a keyword to search for: ")
    pbar = tqdm.tqdm(total=60)
    # Determine the filename based on the user's input
    if keyword:
        filename = f"data/google_maps_listings_{keyword}.csv"
    else:
        filename = f"data/google_maps_listings_{business_type}.csv"

    results_written = 0  # To keep track of the number of results written
    next_page_token = None  # To keep track of the next page token

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Address", "Types", "Website", "Email", "Phone Number", "Rating", "Business Type", "Keyword"])

    while results_written < 60:  # Adjust this number as needed
            # Build the request URL with the next_page_token if available
            request_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={radius}&type={business_type}&keyword={keyword}&key={API_KEY}"
            if next_page_token:
                request_url += f"&pagetoken={next_page_token}"

            response = requests.get(request_url)
            data = response.json()
            
            results = data.get("results", [])
            
            for result in results:
                
                website = get_website_from_google_search(result.get("name", ""), API_KEY, CSE_ID)
                
                pbar.update(1)
                
                email = get_email_address(result.get("name", ""), API_KEY, CSE_ID)

                phone_number = get_phone_number(result.get("name", ""), API_KEY)

                rating = get_rating(result.get("name", ""), API_KEY)

                with open(filename, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                    result.get("name", ""),
                    result.get("vicinity", ""),
                    result.get("types", []),
                    website,
                    email,
                    phone_number,
                    rating,
                    business_type,
                    keyword
            ])
            results_written += 1
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            print(f"\033[92mBatch Completed: {results_written}/3 | CPU: {cpu_percent:.2f}% | RAM: {memory_percent:.2f}%")
            print('\033[0m')
            # Check if there is a next page token
            next_page_token = data.get("next_page_token", None)

            if not next_page_token:
                break

    print(f"CSV file saved as 'data/{filename}'")