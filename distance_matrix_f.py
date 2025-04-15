import streamlit as st
import pandas as pd
import googlemaps
from datetime import datetime, date

# Title of the app
st.title("Travel Time & Distance Calculator Using Google Maps API")

# File uploader for CSV
uploaded_file = st.file_uploader(
    "Upload a CSV file",
    type="csv",
    help=("CSV should contain columns: 'OriginLat', 'OriginLon', "
          "'DestLat', 'DestLon', and 'endTime'. The 'endTime' column "
          "should have datetime strings from which only the time-of-day will be used.")
)

# Select travel mode
mode = st.selectbox("Select travel mode:", options=["driving", "walking", "bicycling", "transit"])

# Input for Google API Key
api_key = st.text_input("Enter your Google API key:")

# Button to trigger calculation
if st.button("Calculate"):
    if not uploaded_file:
        st.error("Please upload a CSV file.")
    elif api_key.strip() == "":
        st.error("Please provide a valid Google API key.")
    else:
        # Create Google Maps client
        try:
            gmaps = googlemaps.Client(key=api_key)
        except Exception as e:
            st.error(f"Error creating Google Maps client: {e}")
        
        try:
            # Read the CSV file into a DataFrame
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Error reading CSV file: {e}")

        # Check for required columns
        required_cols = ['OriginLat', 'OriginLon', 'DestLat', 'DestLon', 'endTime']
        if not all(col in df.columns for col in required_cols):
            st.error(f"CSV file must contain columns: {', '.join(required_cols)}")
        else:
            results = []
            
            # Iterate through each row of the DataFrame
            for idx, row in df.iterrows():
                # Format the origin and destination as "lat,lon"
                origin = f"{row['OriginLat']},{row['OriginLon']}"
                destination = f"{row['DestLat']},{row['DestLon']}"
                
                # Parse 'endTime' column to extract the time-of-day, then combine with today’s date.
                try:
                    # Extract time-of-day from 'endTime'
                    end_time = pd.to_datetime(row['endTime']).time()
                    # Combine the extracted time with today's date
                    departure_datetime = datetime.combine(date.today(), end_time)
                except Exception as e:
                    st.error(f"Error parsing 'endTime' for row {idx}: {e}")
                    continue
                
                # Call the Google Distance Matrix API
                try:
                    response = gmaps.distance_matrix(
                        origins=origin, 
                        destinations=destination, 
                        mode=mode, 
                        departure_time=departure_datetime
                    )
                except Exception as e:
                    st.error(f"Error fetching data from Google API for row {idx}: {e}")
                    continue
                
                # Extract relevant information from the response
                try:
                    element = response['rows'][0]['elements'][0]
                    if element.get('status') != 'OK':
                        st.warning(f"Row {idx}: API response status not OK. Skipping.")
                        continue
                    
                    distance_text = element['distance']['text'] if 'distance' in element else "N/A"
                    distance_value = element['distance']['value'] if 'distance' in element else None
                    
                    # For driving mode with departure time, the API may return 'duration_in_traffic'
                    if mode == "driving" and 'duration_in_traffic' in element:
                        duration_text = element['duration_in_traffic']['text']
                        duration_value = element['duration_in_traffic']['value']
                    else:
                        duration_text = element['duration']['text']
                        duration_value = element['duration']['value']
                    
                    results.append({
                        "Origin": origin,
                        "Destination": destination,
                        "Departure_Time": departure_datetime,
                        "Distance (text)": distance_text,
                        "Distance (meters)": distance_value,
                        "Duration (text)": duration_text,
                        "Duration (seconds)": duration_value
                    })
                except Exception as e:
                    st.error(f"Error processing API response for row {idx}: {e}")
            
            # Display results if any are available
            if results:
                result_df = pd.DataFrame(results)
                st.write("### Travel Time & Distance Results", result_df)
                
                # Create CSV for download
                csv = result_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download results as CSV",
                    data=csv,
                    file_name='distance_matrix.csv',
                    mime='text/csv'
                )
            else:
                st.info("No valid results to display.")
