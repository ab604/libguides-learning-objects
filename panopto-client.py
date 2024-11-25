import requests
import base64
import uuid
from datetime import datetime, timedelta
import hmac
import hashlib
import csv
import os
import json

class PanoptoClient:
    def __init__(self, server_url, client_id, client_secret, username):
        self.server_url = server_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        print(f"Initialized client for {server_url} with username {username}")
        
    def _generate_auth_params(self):
        """Generate authentication parameters for API requests"""
        # Create timestamp in ISO format
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        # Generate UUID for nonce
        nonce = str(uuid.uuid4())
        
        # Create the auth string to sign
        auth_string = f"{self.username}\n{timestamp}\n{nonce}"
        
        # Create HMAC signature using SHA256
        hmac_obj = hmac.new(
            self.client_secret.encode('utf-8'),
            auth_string.encode('utf-8'),
            hashlib.sha256
        )
        signature = base64.b64encode(hmac_obj.digest()).decode('utf-8')
        
        # Return complete auth header
        auth_value = (f'UsernameToken Username="{self.username}", '
                     f'Timestamp="{timestamp}", '
                     f'Nonce="{nonce}", '
                     f'ClientId="{self.client_id}", '
                     f'Signature="{signature}"')
        
        return {
            'Authorization': auth_value,
            'Content-Type': 'application/json'
        }
    
    def get_folder_contents(self, folder_id):
        """Get list of recordings in a folder"""
        print(f"\nAttempting to get contents of folder: {folder_id}")
        headers = self._generate_auth_params()
        
        endpoint = f"{self.server_url}/Panopto/api/v1/folders/{folder_id}/sessions"
        print(f"Making request to: {endpoint}")
        print(f"Using authorization header: {headers['Authorization']}")
        
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
        SERVER_URL = "https://southampton.cloud.panopto.eu"  # Already set to Southampton's URL
        CLIENT_ID = "02ea900c-db3c-4fe0-bc66-b233009a4c60"        # Replace with your client ID
        CLIENT_SECRET = "" # Replace with your client secret
        USERNAME = "ab604"           # Replace with your username
        FOLDER_ID = "fe0aa3a2-51e5-4231-becf-1306400b593b"        # Replace with your folder ID
        OUTPUT_FILE = "panopto_recordings.csv"

        # Initialize and run
        client = PanoptoClient(
            server_url=SERVER_URL,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            username=USERNAME
        )

        client.export_recordings_to_csv(FOLDER_ID, OUTPUT_FILE)
        print("Script completed successfully!")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
