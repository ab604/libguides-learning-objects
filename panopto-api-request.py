import requests
from datetime import datetime, timedelta
import base64

def get_panopto_sessions(server_name, client_id, client_secret, folder_id):
    """
    Retrieve sessions from a specific Panopto folder using the REST API.
    
    Args:
        server_name (str): Your Panopto server (e.g., 'yourschool.hosted.panopto.com')
        client_id (str): Your OAuth2 client ID
        client_secret (str): Your OAuth2 client secret
        folder_id (str): The Panopto folder ID to query
    
    Returns:
        dict: JSON response containing session data
    """
    # OAuth2 token endpoint
    token_url = f"https://{server_name}/Panopto/oauth2/connect/token"
    
    # Encode credentials
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    
    # Get access token
    token_headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    token_data = {
        'grant_type': 'client_credentials'
    }
    
    token_response = requests.post(token_url, headers=token_headers, data=token_data)
    access_token = token_response.json()['access_token']
    
    # Make API request for sessions
    api_url = f"https://{server_name}/Panopto/api/v1/folders/{folder_id}/sessions"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Optional parameters for the request
    params = {
        'sortField': 'CreatedDate',
        'sortOrder': 'Desc',
        'pageNumber': 0,
        'pageSize': 100  # Adjust based on your needs
    }
    
    response = requests.get(api_url, headers=headers, params=params)
    return response.json()

# Example usage
if __name__ == "__main__":
    # Replace these with your actual credentials
    SERVER_NAME = "southampton.cloud.panopto.eu"
    CLIENT_ID = "d32d0d2b-5854-4bf3-b9ce-b22e00a2bb50"
    CLIENT_SECRET = "5BmTDqss18hpG+QmJHzRME31cDk8YQE986zf9GzZtMQ="
    FOLDER_ID = "fe0aa3a2-51e5-4231-becf-1306400b593b"
    
    try:
        sessions = get_panopto_sessions(SERVER_NAME, CLIENT_ID, CLIENT_SECRET, FOLDER_ID)
        
        # Process the results
        for session in sessions.get('Results', []):
            print(f"Session Name: {session.get('Name')}")
            print(f"Created: {session.get('CreatedDate')}")
            print(f"Duration: {session.get('Duration')} seconds")
            print("---")
            
    except Exception as e:
        print(f"Error: {str(e)}")
