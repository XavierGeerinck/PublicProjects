import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from schema import Trends, Trend
from google import genai
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Tuple
import json
import argparse

# Load environment variables
load_dotenv()

# Retrieve API key and model name from environment variables
LLM_MODEL = os.getenv("LLM_MODEL")
LLM_API_KEY = os.getenv("LLM_API_KEY")

# Ensure LLM_MODEL and LLM_API_KEY are properly loaded
if not LLM_MODEL or not LLM_API_KEY:
    raise ValueError("LLM_MODEL or LLM_API_KEY not found in environment variables")

def _html_remove_all_attrs(soup, exclude_els=[]):
    """Remove all attributes from all elements in the html"""
    for tag in soup.find_all(True):
        if tag.name in exclude_els:
            continue

        tag.attrs = {}

    return soup

def _html_remove_el(soup, el_name):
    for tag in soup.find_all(el_name):
        tag.decompose()
    return soup

# Function to take a screenshot using Playwright
def grab_data(browser, url):
    page = browser.new_page()
    page.goto(url)

    # Wait for it to load
    page.wait_for_load_state("networkidle")

    # Extract the Table HTML
    html_table = page.query_selector("table").inner_html()

    page.close()
    
    return "<html>" + html_table + "</html>"

def analyze_data(path_out, geos, hours, date, date_time) -> Tuple[str, str, List[Trend]]:
    data_all = []

    for geo in geos:
        for hour in hours:
            name = f"{date}-{geo}-{hour}"

            # Read the data
            with open(f"{name}.html", "r") as f:
                data = f.read()

            # Analyze the data
            print(f"Analyzing {name}")
            data_analyzed = analyze_data_single(data, date_time)

            # Save to file
            with open(f"{path_out}/{name}.json", "w") as f:
                f.write(data_analyzed.model_dump_json())

            # Merge into data_all
            data_all.append((
                geo,
                hour,
                data_analyzed.trends
            ))

    return data_all

def analyze_data_single(data, date_time) -> Trends:
    data_prepared = BeautifulSoup(data, "html.parser")

    # Remove all SVG elements
    data_prepared = _html_remove_el(data_prepared, "svg")

    # Remove all html attributes from the tags
    data_prepared = _html_remove_all_attrs(data_prepared)

    prompt = f"""Convert the data to the provided JSON Schema. Also perform the following tasks:
    - Add the categories of the trend (minimal one, default to 'other')
    - Parse the volume in absolute numbers (i.e., 2K becomes 2000, 1M becomes 1000000)
    - Remove special characters (e.g., \u00b7)
    - Start date is the date as indicated, or the time now - x hours ago (e.g., 4 hours ago and now is 2021-10-10 12:00:00, then start_date is 2021-10-10 08:00:00)
    - if End Date, it is the start_date + the "X hours ago" (e.g., 4 hours ago and start_date is 2021-10-10 12:00:00, then end_date is 2021-10-10 16:00:00)
    - The other trends should be comma separated
    - The volume_over_time comes from the SVG element, its points

    Current Time: {date_time}

    Schema:
    ```json
    {Trends.model_json_schema()}
    ```

    HTML: 
    ```html
    {data_prepared}
    ```
    """

    client = genai.Client(api_key=LLM_API_KEY)
    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=prompt,
        config={
            'response_mime_type': 'application/json',
            'response_schema': Trends
        },
    )

    # Extract the response and parse as JSON
    response = response.text

    # Parse the response as JSON
    response_json = json.loads(response)
    
    return response_json

def download_data(path_out, geos, hours, date):
    with sync_playwright() as p:
        browser = p.chromium.launch()

        for geo in geos:
            for hour in hours:
                name = f"{date}-{geo}-{hour}.html"
                trends_url = f"https://trends.google.com/trending?geo={geo}&hours={hour}&sort=recency"

                print(f"Downloading {trends_url}")
                data = grab_data(browser, trends_url)

                # Get the date in the format YYYY-MM-DD
                date = datetime.now().strftime("%Y-%m-%d")

                with open(f"{path_out}/{name}", "w") as f:
                    f.write(data)

        browser.close()

# Main process
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=str, default="/tmp", help="The path to save the output files in")
    parser.add_argument("--geos", type=str, default="US", help="The geos to fetch, comma-separated")
    parser.add_argument("--hours", type=str, default="4", help="The hours to fetch, comma-separated")

    args = parser.parse_args()

    config_geos = args.geos.split(",")
    config_hours = args.hours.split(",")

    date = datetime.now().strftime("%Y-%m-%d")
    date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    download_data(args.out, config_geos, config_hours, date)
    data_analyzed = analyze_data(args.out, config_geos, config_hours, date, date_time)

    # Print the data
    print(data_analyzed)