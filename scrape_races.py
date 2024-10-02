# Scraper file 
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Base URL for the races
base_url = "https://race-find.com/us/races?query=&state=5&city=382&date_from=&date_to=&type=&race-page="

# Initialize an empty list to store all race data
races = []
unique_races = set()  # Track unique races by (name, url)

# Loop through available pages
for page_num in range(1, 5):  # Adjust if necessary
    url = base_url + str(page_num) + "&per-page=15"
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        race_blocks = soup.find_all('tr')  # Adjust if needed
        
        for race_block in race_blocks:
            race_link = race_block.find('a')
            if race_link:
                name = race_link.text.strip()
                race_url = race_link['href']
                
                cells = race_block.find_all('td')
                if len(cells) >= 6:
                    date = cells[2].text.strip()
                    distance = cells[4].text.strip()
                    
                    unique_id = (name, race_url)
                    
                    if unique_id not in unique_races:
                        races.append({
                            'Race': name,            # Set the name to 'Race'
                            'Date': date,            # Set the date to 'Date'
                            'Distance(s)': distance, # Set the distance to 'Distance(s)'
                            'URL': race_url          # Include the race URL
                        })
                        unique_races.add(unique_id)
        
        time.sleep(2)  # Delay between requests
    else:
        print(f"Failed to retrieve data from page {page_num}")

# Save the data to a DataFrame and CSV
df = pd.DataFrame(races)
df.to_csv('data/san_diego_race_data.csv', index=False)  # Save as CSV
print("Data saved to data/san_diego_race_data.csv")
