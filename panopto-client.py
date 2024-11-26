import requests
import json
import csv
from datetime import datetime
from panopto_oauth2 import PanoptoOAuth2

class PanoptoClient:
    def __init__(self, server_url, client_id, client_secret, ssl_verify=True):
        self.server_url = server_url.rstrip('/')
        self.server = server_url.replace('https://', '').rstrip('/')
        self.oauth2 = PanoptoOAuth2(
            server=self.server,
            client_id=client_id,
            client_secret=client_secret,
            ssl_verify=ssl_verify
        )
        self.access_token = None
        print(f"Initialized client for {server_url}")

    def _ensure_authenticated(self):
        if not self.access_token:
            print("\nGetting OAuth2 access token...")
            self.access_token = self.oauth2.get_access_token_authorization_code_grant()
        return self.access_token

    def _get_headers(self):
        token = self._ensure_authenticated()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def get_folder_contents(self, folder_id):
        print(f"\nAttempting to get contents of folder: {folder_id}")
        headers = self._get_headers()
    
        endpoint = f"{self.server_url}/Panopto/api/v1/folders/{folder_id}/sessions"
        print(f"Making request to: {endpoint}")
    
        all_recordings = []
        page_number = 0
        page_size = 50  # Fixed to Panopto's default page size
        last_page_size = page_size
    
        while True:
            params = {
                'sortField': 'CreatedDate',
                'sortOrder': 'Desc',
                'pageNumber': page_number,
                'pageSize': page_size
            }
    
            try:
                print(f"\nRequesting page {page_number + 1}")
                print(f"Current total recordings retrieved: {len(all_recordings)}")
                
                response = requests.get(
                    endpoint,
                    headers=headers,
                    params=params,
                    timeout=30
                )
    
                if response.status_code != 200:
                    print(f"Error response content: {response.text}")
                    response.raise_for_status()
    
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    print(f"JSON Decode Error: {e}")
                    print(f"Raw response text: {response.text}")
                    break
                
                results = data.get('Results', [])
                
                if not results:
                    print("No more recordings found in this page")
                    break
                
                new_recordings = len(results)
                print(f"Retrieved {new_recordings} recordings from page {page_number + 1}")
                
                # For each session, get additional details
                for session in results:
                    session_id = session.get('Id')
                    # Get detailed session info including viewer data
                    try:
                        session_endpoint = f"{self.server_url}/Panopto/api/v1/sessions/{session_id}/viewers"
                        session_response = requests.get(
                            session_endpoint,
                            headers=headers,
                            timeout=30
                        )
                        if session_response.status_code == 200:
                            viewer_data = session_response.json()
                            session['viewer_details'] = viewer_data
                        else:
                            print(f"Failed to get viewer data for session {session_id}")
                            session['viewer_details'] = []
                    except Exception as e:
                        print(f"Error getting viewer data for session {session_id}: {str(e)}")
                        session['viewer_details'] = []
                
                all_recordings.extend(results)
                
                last_page_size = new_recordings
                
                if new_recordings < page_size:
                    print(f"Retrieved partial page ({new_recordings} < {page_size}), reached end of results")
                    break
                
                page_number += 1
    
            except requests.exceptions.RequestException as e:
                print(f"Request Error: {str(e)}")
                break
            except Exception as e:
                print(f"Unexpected Error: {str(e)}")
                break
            
        print(f"\nSuccessfully retrieved {len(all_recordings)} total recordings")
        return all_recordings

    def export_recordings_to_csv(self, folder_id, output_file):
        print(f"\nStarting export to {output_file}")
        try:
            recordings = self.get_folder_contents(folder_id)
            
            if not recordings:
                print("No recordings found in the folder")
                return
            
            fieldnames = [
                'Name',
                'ID',
                'Duration',
                'Folder',
                'URL'
            ]
            
            print(f"Writing {len(recordings)} recordings to CSV...")
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for recording in recordings:
                    duration_secs = recording.get('Duration', 0)
                    hours = int(duration_secs // 3600)
                    minutes = int((duration_secs % 3600) // 60)
                    seconds = int(duration_secs % 60)
                    duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    
                    recording_url = f"{self.server_url}/Panopto/Pages/Viewer.aspx?id={recording['Id']}"
                    
                    writer.writerow({
                        'Name': recording.get('Name', ''),
                        'ID': recording.get('Id', ''),
                        'Duration': duration,
                        'Folder': recording.get('Folder', ''),
                        'URL': recording_url
                    })
            
            print(f"Successfully exported recordings to {output_file}")
            
        except Exception as e:
            print(f"Error during export: {str(e)}")
            raise

# Main execution block
if __name__ == "__main__":
    try:
        # Configuration
        SERVER_URL = "https://southampton.cloud.panopto.eu"
        CLIENT_ID = "22d8c2d6-0c58-4398-81b9-b23300ab7e06"
        CLIENT_SECRET = "IEsOQsglWORDm6OIDiiioCQeG3v3pyFZMEx0PoppXLM="
        FOLDER_ID = "fe0aa3a2-51e5-4231-becf-1306400b593b"
        OUTPUT_FILE = "panopto_recordings.csv"

        # Initialize and run
        client = PanoptoClient(
            server_url=SERVER_URL,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )

        client.export_recordings_to_csv(FOLDER_ID, OUTPUT_FILE)
        print("Script completed successfully!")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
