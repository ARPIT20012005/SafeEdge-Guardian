import requests
import json
import os
from datetime import datetime

class FirebaseUploader:
    def __init__(self, config_path="scripts/google-services.json"):
        """Initialize Firebase uploader with config"""
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.database_url = config["project_info"]["firebase_url"]
        self.api_key = config["client"][0]["api_key"][0]["current_key"]
        self.device_id = "MEM001"  # Device ID as shown in screenshot
        
    def update_status(self, status):
        """
        Update device status in Firebase Realtime Database
        Args:
            status: str - "safe", "warning", or "danger"
        """
        # Convert to lowercase
        status = status.lower()
        
        # Prepare data
        data = {
            "status": status,
            "lastUpdate": int(datetime.now().timestamp() * 1000),  # milliseconds
            "model": "MOMENTO Demo Device",
            "serial": "MEM001"
        }
        
        # Firebase REST API endpoint
        url = f"{self.database_url}/devices/{self.device_id}.json?auth={self.api_key}"
        
        try:
            response = requests.patch(url, json=data)
            if response.status_code == 200:
                return True
            else:
                print(f"Firebase update failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"Firebase error: {e}")
            return False
