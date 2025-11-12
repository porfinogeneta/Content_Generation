from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
from pathlib import Path

# If modifying these scopes, delete the token.json file
SCOPES = ['https://www.googleapis.com/auth/drive']


ROOT_SRC = Path(__file__).resolve().parent.parent
BASE_VIDEOS_PATH = ROOT_SRC / "data" / "videos"

def authenticate():
    """Authenticate and return the Drive service."""
    creds = None
    
    # Token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('drive', 'v3', credentials=creds)

def upload_video(file_path, folder_id=None):
    """Upload an MP4 file to Google Drive."""
    service = authenticate()
    
    file_metadata = {
        'name': os.path.basename(file_path),
        'mimeType': 'video/mp4'
    }
    
    # If you want to upload to a specific folder
    if folder_id:
        file_metadata['parents'] = [folder_id]
    
    media = MediaFileUpload(file_path, mimetype='video/mp4', resumable=True)
    
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, webViewLink'
    ).execute()
    
    print(f"File uploaded successfully!")
    print(f"File ID: {file.get('id')}")
    print(f"File Name: {file.get('name')}")
    print(f"View Link: {file.get('webViewLink')}")
    
    return file

# Example usage
if __name__ == '__main__':
    upload_video(BASE_VIDEOS_PATH / Path("hello.mp4"))
    
    # Or upload to a specific folder
    # upload_video('path/to/your/video.mp4', folder_id='YOUR_FOLDER_ID')