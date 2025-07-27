import pandas as pd
from flask import Flask, render_template
from datetime import datetime
import json
import webbrowser
import os
from urllib.parse import urljoin
from urllib.request import pathname2url

app = Flask(__name__)

def process_fwci_data(df):
    """Processes the DataFrame to prepare it for the dashboard template."""
    
    # Find all columns that are for FWCI tracking
    fwci_cols = sorted([col for col in df.columns if 'FWCI' in col], 
                       key=lambda x: datetime.strptime(x.split('(')[1].split(')')[0], '%d/%m/%y'))
    
    if not fwci_cols:
        # If no FWCI columns, just return basic info
        df['latest_fwci'] = 'N/A'
        df['change'] = 'none'
        df['history'] = ''
        return df.to_dict('records')

    latest_fwci_col = fwci_cols[-1]
    previous_fwci_col = fwci_cols[-2] if len(fwci_cols) > 1 else None

    processed_data = []
    for _, row in df.iterrows():
        # Get latest FWCI, fill missing values with 'N/A'
        latest_fwci = row.get(latest_fwci_col)
        try:
            latest_fwci_str = f"{float(latest_fwci):.2f}"
        except (ValueError, TypeError):
            latest_fwci_str = "Not found"

        change = 'new' # Default status
        
        if previous_fwci_col:
            previous_fwci = row.get(previous_fwci_col)
            
            # Convert to numbers for comparison, handling 'Not found'
            try:
                latest_val = float(latest_fwci)
                prev_val = float(previous_fwci)
                if latest_val > prev_val:
                    change = 'up'
                elif latest_val < prev_val:
                    change = 'down'
                else:
                    change = 'same'
            except (ValueError, TypeError):
                # If values are not numbers (e.g., 'Not found'), they are the same
                if str(latest_fwci) == str(previous_fwci):
                    change = 'same'
                else:
                    change = 'changed' # For non-numeric changes

        # Create the history as a list of dicts for the tooltip table
        history = []
        for col in reversed(fwci_cols):  # Show most recent first
            date_str = col.split('(')[1].split(')')[0]
            value = row.get(col)
            try:
                # Try to convert to float and format
                value_str = f"{float(value):.2f}"
            except (ValueError, TypeError):
                # If conversion fails, it's 'Not found' or NaN
                value_str = "Not found"
            history.append({'date': date_str, 'value': value_str})

        processed_data.append({
            'name': row['Publication Name'],
            'url': row['URL'],
            'latest_fwci': latest_fwci_str,
            'change': change,
            'history': json.dumps(history)
        })
        
    return processed_data

@app.route('/')
def index():
    try:
        df = pd.read_csv('scopus_publications.csv')
        publication_data = process_fwci_data(df)
        
        # Get the latest date from column headers for display
        fwci_cols = [col for col in df.columns if 'FWCI' in col]
        latest_date_str = ""
        if fwci_cols:
            latest_col = sorted(fwci_cols, key=lambda x: datetime.strptime(x.split('(')[1].split(')')[0], '%d/%m/%y'))[-1]
            latest_date_str = latest_col.split('(')[1].split(')')[0]

        # Render the template
        html_output = render_template('index.html', publications=publication_data, latest_date=latest_date_str)
        
        # Save the rendered HTML to a file
        with open('result_html/result.html', 'w', encoding='utf-8') as f:
            f.write(html_output)
            
        return html_output
    except FileNotFoundError:
        return "<h2>scopus_publications.csv not found.</h2><p>Please run the scopus_scraper.py script first to generate the data file.</p>"

if __name__ == '__main__':
    # Generate the file by calling the index function logic directly
    try:
        df = pd.read_csv('scopus_publications.csv')
        publication_data = process_fwci_data(df)
        
        fwci_cols = [col for col in df.columns if 'FWCI' in col]
        latest_date_str = ""
        if fwci_cols:
            latest_col = sorted(fwci_cols, key=lambda x: datetime.strptime(x.split('(')[1].split(')')[0], '%d/%m/%y'))[-1]
            latest_date_str = latest_col.split('(')[1].split(')')[0]

        # Manually create a request context to use render_template
        with app.test_request_context():
            html_output = render_template('index.html', publications=publication_data, latest_date=latest_date_str)
        
        # Save the rendered HTML to a file
        output_filename = 'result_html/scopus_dashboard.html'
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(html_output)
        
        print(f"Dashboard successfully generated: {output_filename}")
        
        # Open the generated HTML file in the browser
        file_path = os.path.abspath(output_filename)
        try:
            # Construct a file:// URL and open it
            file_url = urljoin('file:', pathname2url(file_path))
            webbrowser.open_new_tab(file_url)
            print(f"Attempting to open {file_url} in your browser.")
        except Exception as e:
            print(f"Could not automatically open the file in a browser: {e}")
            print(f"Please open the file manually: {file_path}")

    except FileNotFoundError:
        print("Error: scopus_publications.csv not found.")
        print("Please run the scopus_scraper.py script first to generate the data file.")
    except Exception as e:
        print(f"An error occurred: {e}")
