# Scopus FWCI Tracker & Dashboard

## Overview

This project provides a set of tools to automatically track and visualize the Field-Weighted Citation Impact (FWCI) of publications for a specific Scopus author. It consists of a Python-based web scraper to collect the data and a Flask-based web application to display it in a user-friendly dashboard.

## Features

- **Automated Data Scraping**: Uses Selenium to automate the process of collecting publication data from Scopus.
- **Session Management**: Saves and loads browser session data (cookies and local storage) to avoid the need for repeated manual logins.
- **Historical FWCI Tracking**: The scraper is designed to add new FWCI data as new columns in the output CSV, allowing for historical comparison.
- **Web-Based Dashboard**: A simple and clean web interface to visualize the scraped data.
- **Change Indicators**: The dashboard clearly indicates whether the FWCI for a publication has gone up, down, remained the same, or is a new entry since the last scrape.

## How It Works

The project is composed of two main Python scripts:

1.  **The Scraper (`scopus_scraper.py`)**:
    - This script uses the Selenium library to control a Chrome browser.
    - It can be run in one of two modes:
        - `--save-session`: This mode guides the user to log into Scopus manually. Once logged in, the script saves the session cookies and local storage to `scopus_cookies.json` and `scopus_local_storage.json`.
        - **Default mode**: The script loads the saved session data to bypass the login process, navigates to the hardcoded author's publication page, and scrapes the name, URL, and FWCI for each publication.
    - The scraped data is saved to `scopus_publications.csv`. Each time the script runs, it updates the FWCI for existing publications and adds new ones. The FWCI value is stored in a column named with the date of the scrape (e.g., `FWCI (DD/MM/YY)`).

2.  **The Dashboard (`dashboard.py`)**:
    - This is a Flask web application that reads the `scopus_publications.csv` file.
    - It processes the data to determine the latest FWCI, compares it with the previous value to determine the change, and compiles a history of FWCI values for each publication.
    - It then renders the `templates/index.html` template, passing the processed data to it.
    - When run, it automatically generates a `result.html` file and opens a new tab in your web browser to display the dashboard.

## Setup & Installation

### Prerequisites

- Python 3.x
- pip (Python package installer)

### Installation Steps

1.  **Clone the repository or download the files:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```
    Or simply download the project files into a directory.

2.  **Install the required Python packages:**
    Open your terminal or command prompt in the project directory and run:
    ```bash
    pip install -r requirements.txt
    ```

## Usage Instructions

Follow these steps to get the dashboard up and running:

### Step 1: Initial Session Setup

You only need to do this once. This step saves your Scopus login session so the scraper can run automatically in the future.

1.  Run the scraper with the `--save-session` flag:
    ```bash
    python scopus_scraper.py --save-session
    ```
2.  A Chrome browser window will open. Follow the instructions in the terminal and log into your Scopus account in the browser.
3.  Once you have successfully logged in, the script will detect it, save your session files (`scopus_cookies.json` and `scopus_local_storage.json`), and close.

### Step 2: Running the Scraper

To collect the latest publication and FWCI data, run the scraper without any flags:

```bash
python scopus_scraper.py
```

The script will use your saved session to log in, scrape the data, and update `scopus_publications.csv`. You can run this script periodically to keep your data up-to-date.

### Step 3: Viewing the Dashboard

To view the data, run the dashboard application:

```bash
python dashboard.py
```

This will start a local web server, generate the `result.html` file, and automatically open the dashboard in your default web browser.

## Output CSV Structure (`scopus_publications.csv`)

The scraper generates and updates a CSV file named `scopus_publications.csv`, which serves as the database for the dashboard. The structure of this file is designed to track FWCI values over time.

-   **`Publication Name`**: The title of the publication.
-   **`URL`**: The direct Scopus link to the publication's page.
-   **`FWCI (DD/MM/YY)`**: A column representing the FWCI value on a specific date. Each time the scraper runs, it adds a new column with the current date if it doesn't already exist for that day, or updates the values if it does. This allows for historical tracking.

### Example:

```csv
Publication Name,URL,FWCI (20/07/24),FWCI (27/07/24)
"A study on advanced AI models","https://scopus.com/record/display.uri?eid=2-s2.0-12345",1.52,1.58
"The impact of climate change on marine life","https://scopus.com/record/display.uri?eid=2-s2.0-67890",2.10,2.10
"New methods in quantum computing","https://scopus.com/record/display.uri?eid=2-s2.0-11223",Not found,3.45
```

## Project Structure

-   `scopus_scraper.py`: The main script for scraping data from Scopus.
-   `dashboard.py`: The Flask application for displaying the data dashboard.
-   `requirements.txt`: A list of the Python packages required for the project.
-   `templates/index.html`: The HTML template for the dashboard.
-   `scopus_publications.csv`: The CSV file where the scraped publication data is stored.
-   `result.html`: The final HTML output file generated by the dashboard script.
-   `scopus_cookies.json`: Stores the session cookies after a successful login.
-   `scopus_local_storage.json`: Stores the session local storage data.
-   `chrome_profile/`: Directory created by Selenium/webdriver-manager to manage the browser driver.
