import pandas as pd
import requests
import re
import os
import glob
from datetime import datetime

def download_latest_report(force_download=False):
    """
    Downloads the most recent check-links-report file from the GitHub repository
    only if it's newer than the local version.
    
    Args:
        force_download (bool): If True, downloads regardless of local version
        
    Returns:
        str: Path to the latest report file (downloaded or existing)
        bool: True if a new file was downloaded, False if using existing file
    """
    try:
        # Create reports directory if it doesn't exist
        os.makedirs('reports', exist_ok=True)

        # Check local files first
        local_files = glob.glob('reports/check-links-report-*.csv')
        local_latest = None
        local_latest_date = None

        for file in local_files:
            match = re.search(r'check-links-report-(\d{4}-\d{2}-\d{2})\.csv', file)
            if match:
                file_date = match.group(1)
                try:
                    parsed_date = datetime.strptime(file_date, '%Y-%m-%d')
                    if local_latest_date is None or parsed_date > local_latest_date:
                        local_latest = file
                        local_latest_date = parsed_date
                except ValueError:
                    continue

        # Get GitHub repository contents
        api_url = "https://api.github.com/repos/ab604/link-crawler/contents/reports"
        raw_url_template = "https://raw.githubusercontent.com/ab604/link-crawler/main/reports/{filename}"
        
        headers = {'Accept': 'application/vnd.github.v3+json'}
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        files = response.json()

        # Find the most recent report file on GitHub
        remote_latest = None
        remote_latest_date = None
        pattern = r'check-links-report-(\d{4}-\d{2}-\d{2})\.csv'

        for file in files:
            file_name = file['name']
            match = re.match(pattern, file_name)
            if match:
                file_date = match.group(1)
                try:
                    parsed_date = datetime.strptime(file_date, '%Y-%m-%d')
                    if remote_latest_date is None or parsed_date > remote_latest_date:
                        remote_latest = file_name
                        remote_latest_date = parsed_date
                except ValueError:
                    continue

        if not remote_latest:
            print("No check-links-report files found in the repository")
            return None, False

        # Compare dates and decide whether to download
        if not force_download and local_latest_date and remote_latest_date <= local_latest_date:
            print(f"Latest report already downloaded: {local_latest}")
            return local_latest, False

        # Download the latest file
        download_url = raw_url_template.format(filename=remote_latest)
        response = requests.get(download_url)
        response.raise_for_status()

        # Save the file
        output_path = os.path.join('reports', remote_latest)
        with open(output_path, 'wb') as f:
            f.write(response.content)

        print(f"Successfully downloaded new report: {remote_latest}")
        print(f"File saved to: {output_path}")
        return output_path, True

    except requests.exceptions.RequestException as e:
        print(f"Error accessing GitHub: {str(e)}")
        if local_latest:
            print(f"Using latest local file: {local_latest}")
            return local_latest, False
        return None, False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        if local_latest:
            print(f"Using latest local file: {local_latest}")
            return local_latest, False
        return None, False

def process_learning_objects(libguides_file, panopto_file):
    """
    Process learning object data from LibGuides and Panopto files.
    
    Args:
        libguides_file (str): Path to the LibGuides CSV file
        panopto_file (str): Path to the Panopto recordings CSV file
        
    Returns:
        tuple: (summary_df, other_lo_df, panopto_joined_df)
    """
    # Create tables directory if it doesn't exist
    os.makedirs('tables', exist_ok=True)
    
    # Read input files
    df = pd.read_csv(libguides_file)
    panopto_df = pd.read_csv(panopto_file)
    
    # Get unique Panopto sessions
    panopto_sessions = panopto_df[['Name', 'ID', 'Folder']].drop_duplicates(subset='ID', keep='first')
    
    # Filter LibGuides data for types of Learning Objects
    dfm = df[
        df['URL'].str.contains('[Aa]rticulate|[Tt]hinglink|[Ww]ordpress|[Pp]anopto|[Pp]owtoon', case=False)
    ]
    
    # Create learning object type column
    dfm['lo'] = dfm['URL'].apply(lambda x: 
        'Panopto' if re.search('[Pp]anopto', x) else
        'ThingLink' if re.search('[Tt]hinglink', x) else
        'Articulate' if re.search('[Ar]ticulate', x) else
        'Wordpress' if re.search('[Ww]ordpress', x) else
        'Powtoon' if re.search('[Pp]owtoon', x) else
        'Other'
    )
    
    # Count unique learning objects
    summary_df = dfm.drop_duplicates(subset='URL', keep='first').groupby('lo').size().reset_index(name='n')
    
    # Rename dfm
    all_lo_df = dfm
    
    # Process Panopto data
    panopto_data = dfm[dfm['lo'] == 'Panopto'].copy()
    panopto_data['ID'] = panopto_data['URL'].apply(lambda x: re.search(r'(?<=id=)[^&=]+', x).group())
    
    # Join Panopto data
    panopto_joined_df = panopto_data.merge(panopto_sessions, how='inner', on='ID')
    
    # Save processed data
    summary_df.to_csv('tables/lo_summary_table.csv', index=False)
    all_lo_df.to_csv('tables/all_lo_table.csv', index=False)
    panopto_joined_df.to_csv('tables/panopto_table.csv', index=False)
    
    return summary_df, all_lo_df, panopto_joined_df

def main():
    """Main function to run the data processing pipeline."""
    # Download latest report
    libguides_file, was_downloaded = download_latest_report()
    
    if not libguides_file:
        print("Error: Could not obtain LibGuides report")
        return
    
    # Process data if Panopto file exists
    panopto_file = 'reports/panopto_recordings.csv'
    if not os.path.exists(panopto_file):
        print(f"Error: Panopto recordings file not found at {panopto_file}")
        return
        
    try:
        summary_df, all_lo_df, panopto_joined_df = process_learning_objects(libguides_file, panopto_file)
        print("\nData processing completed successfully:")
        print(f"Summary table shape: {summary_df.shape}")
        print(f"All LO table shape: {all_lo_df.shape}")
        print(f"Panopto table shape: {panopto_joined_df.shape}")
    except Exception as e:
        print(f"Error processing data: {str(e)}")

if __name__ == "__main__":
    main()
