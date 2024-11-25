import requests
import json
import csv
from datetime import datetime
from panopto_oauth2 import PanoptoOAuth2

class PanoptoClient:
    def __init__(self, server_url, client_id, client_secret, ssl_verify=True):
        """
        Initialize PanoptoClient with OAuth2 authentication
        
        Args:
            server_url: Panopto server URL
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            ssl_verify: Whether to verify SSL certificates (default True)
        """
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
        """Ensure we have a valid access token"""
        if not self.access_token:
            print("\nGetting OAuth2 access token...")
            self.access_token = self.oauth2.get_access_token_authorization_code_grant()
        return self.access_token

    def _get_headers(self):
        """Get headers for API requests with OAuth2 token"""
        token = self._ensure_authenticated()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def get_folder_contents(self, folder_id):
        """Get list of recordings in a folder"""
        print(f"\nAttempting to get contents of folder: {folder_id}")
        headers = self._get_headers()
        
        endpoint = f"{self.server_url}/Panopto/api/v1/folders/{folder_id}/sessions"
        print(f"Making request to: {endpoint}")
        
        params = {
            'sortField': 'CreatedDate',
            'sortOrder': 'Desc',
            'maxResults': 100
        }
        
        try:
            response = requests.get(
                endpoint,
                headers=headers,
                params=params
            )
            
            print(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error response content: {response.text}")
                response.raise_for_status()
            
            data = response.json()
            results = data.get('Results', [])
            print(f"Successfully retrieved {len(results)} recordings")
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {str(e)}")
            print(f"Raw response: {response.text}")
            raise

    def export_recordings_to_csv(self, folder_id, output_file):
        """Export folder recordings to CSV file"""
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
                'Created',
                'Folder',
                'Views',
                'Status',
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
                        'Created': recording.get('CreatedDate', ''),
                        'Folder': recording.get('ParentFolderId', ''),
                        'Views': recording.get('ViewerCount', 0),
                        'Status': recording.get('State', ''),
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
        CLIENT_SECRET = "IEsOQsglWORDm6OIDiiioCQeG3v3pyFZMEx0PoppXLM="  # Replace with your client secret
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
