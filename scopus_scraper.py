import time
import os
import json
import argparse
import pandas as pd # Import pandas for advanced CSV handling
from datetime import datetime # To get the current date
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- Configuration ---
TARGET_URL = 'https://www.scopus.com/authid/detail.uri?authorId=57201649539'
HOME_URL = 'https://www.scopus.com'
BASE_DOMAIN_URL = 'https://www.scopus.com'
LOGIN_CONFIRMATION_ELEMENT_ID = 'user-menu'
SIGN_IN_BUTTON_ID = 'signin_link_move'
COOKIES_FILE = 'scopus_cookies.json'
LOCAL_STORAGE_FILE = 'scopus_local_storage.json'
CSV_OUTPUT_FILE = 'scopus_publications.csv'

# (The save_session and load_session functions are unchanged, so they are included here for completeness)
def save_session(driver):
    """Guides user through login and saves session data."""
    print("Starting session saving process...")
    driver.get(HOME_URL)
    try:
        sign_in_button = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, SIGN_IN_BUTTON_ID)))
        sign_in_button.click()
        print("Sign-in button clicked.")
    except TimeoutException:
        print("Could not find a 'Sign In' button. Assuming we are on the login page.")
    print("="*60)
    print("Please complete the login in the browser window.")
    print(f"The script will save your session once it detects the element with ID: '{LOGIN_CONFIRMATION_ELEMENT_ID}'")
    print("="*60)
    try:
        WebDriverWait(driver, 300).until(EC.visibility_of_element_located((By.ID, LOGIN_CONFIRMATION_ELEMENT_ID)))
        print("\nLogin successful! Saving session data...")
        with open(COOKIES_FILE, 'w') as f:
            json.dump(driver.get_cookies(), f)
        print(f"-> Cookies saved to {COOKIES_FILE}")
        local_storage = driver.execute_script("return window.localStorage;")
        with open(LOCAL_STORAGE_FILE, 'w') as f:
            json.dump(local_storage, f)
        print(f"-> Local Storage saved to {LOCAL_STORAGE_FILE}")
        print("\nSession saved successfully! You can now run the script without the --save-session flag.")
    except TimeoutException:
        print("\nLogin timed out. Session not saved. Please try again.")

def load_session(driver):
    """Loads session data from files into the browser using a robust method."""
    print("Loading session from files...")
    driver.get(BASE_DOMAIN_URL)
    with open(COOKIES_FILE, 'r') as f:
        cookies = json.load(f)
    with open(LOCAL_STORAGE_FILE, 'r') as f:
        local_storage = json.load(f)
    driver.delete_all_cookies()
    for key, value in local_storage.items():
        driver.execute_script(f"window.localStorage.setItem('{key}', {json.dumps(value)});")
    print("-> Local Storage injected.")
    for cookie in cookies:
        if 'domain' in cookie and 'scopus.com' in cookie['domain']:
            driver.add_cookie(cookie)
    print("-> Cookies injected.")
    print("Navigating to homepage to validate the restored session...")
    driver.get(HOME_URL)
    try:
        WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.ID, LOGIN_CONFIRMATION_ELEMENT_ID)))
        print("Session successfully restored and validated.")
        return True
    except TimeoutException:
        print("Failed to restore session. The saved session might be expired or invalid.")
        print("Please try running the script with '--save-session' again.")
        return False

def scrape_data(driver):
    """Navigates to target and scrapes all required data."""
    print(f"\nNavigating to the target author page: {TARGET_URL}")
    driver.get(TARGET_URL)

    # --- Change to 200 results per page ---
    print("\n--- Setting publications to 200 per page ---")
    try:
        results_dropdown_xpath = "//span[text()='Display']/following-sibling::select"
        dropdown_element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, results_dropdown_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown_element)
        time.sleep(1)
        select = Select(dropdown_element)
        select.select_by_value("200")
        print("Selected '200 results'. Waiting for page to update...")
        time.sleep(5)
    except Exception as e:
        print(f"Could not set results to 200: {e}")
        return

    # --- Step 1: Collect all publication URLs from the list ---
    print("\n--- Step 1: Collecting Publication URLs ---")
    publications_to_visit = []
    try:
        publication_list_ul = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.ViewType-module__nDSGx")))
        publications = publication_list_ul.find_elements(By.CSS_SELECTOR, "li[data-testid='results-list-item']")
        for pub in publications:
            try:
                link_element = pub.find_element(By.CSS_SELECTOR, "h4 a")
                title = link_element.text.strip()
                url = link_element.get_attribute('href')
                if url:
                    publications_to_visit.append({'title': title, 'url': url})
            except NoSuchElementException:
                continue
        print(f"Successfully collected {len(publications_to_visit)} publication URLs.")
    except Exception as e:
        print(f"An error occurred while collecting publication URLs: {e}")

    # --- Step 2: Load existing CSV or create a new DataFrame ---
    if os.path.exists(CSV_OUTPUT_FILE):
        print(f"\nLoading existing data from {CSV_OUTPUT_FILE}...")
        df = pd.read_csv(CSV_OUTPUT_FILE)
    else:
        print(f"\nCreating a new data set...")
        df = pd.DataFrame(columns=['Publication Name', 'URL'])

    # --- Step 3: Visit each URL, scrape FWCI, and update the DataFrame ---
    print("\n--- Step 2: Visiting each publication to scrape FWCI ---")
    
    # Get today's date for the column header
    today_str = datetime.now().strftime('%d/%m/%y')
    fwci_col_name = f"FWCI ({today_str})"

    for index, pub_data in enumerate(publications_to_visit):
        print("-" * 50)
        print(f"Scraping {index + 1}/{len(publications_to_visit)}: {pub_data['title']}")
        
        driver.get(pub_data['url'])
        fwci_value = "Not found"
        try:
            fwci_selector = "div[data-testid='fwci-in-scopus'] span[data-testid='unclickable-count']"
            fwci_element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, fwci_selector)))
            fwci_value = fwci_element.text.strip()
        except TimeoutException:
            pass
        
        print(f"   FWCI: {fwci_value}")

        # --- Update DataFrame Logic ---
        # Check if the publication URL already exists in our DataFrame
        if pub_data['url'] in df['URL'].values:
            # Update existing row
            df.loc[df['URL'] == pub_data['url'], fwci_col_name] = fwci_value
        else:
            # Add a new row
            new_row = {'Publication Name': pub_data['title'], 'URL': pub_data['url'], fwci_col_name: fwci_value}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # --- Step 4: Save the updated DataFrame back to CSV ---
    print(f"\n--- Step 3: Saving updated data to {CSV_OUTPUT_FILE} ---")
    try:
        df.to_csv(CSV_OUTPUT_FILE, index=False, encoding='utf-8')
        print("Successfully saved CSV file.")
    except Exception as e:
        print(f"An error occurred while saving the CSV: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Scopus author data after handling login.")
    parser.add_argument('--save-session', action='store_true', help='Run this once to log in and save your session.')
    args = parser.parse_args()

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()

    if args.save_session:
        save_session(driver)
    else:
        if not os.path.exists(COOKIES_FILE) or not os.path.exists(LOCAL_STORAGE_FILE):
            print("Session files not found!")
            print("Please run the script with the '--save-session' flag first to log in and create them.")
        else:
            if load_session(driver):
                scrape_data(driver)

    print("\nProcess finished. Closing the browser in 5 seconds.")
    time.sleep(5)
    driver.quit()