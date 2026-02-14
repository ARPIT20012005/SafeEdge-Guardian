import requests
import json
import os
from datetime import datetime

class FirebaseUploader:
    def __init__(self, config_path="scripts/google-services.json"):
        """Initialize Firebase uploader with config"""
        self.enabled = False
        self.error_shown = False
        
        try:
            if not os.path.exists(config_path):
                print(f"⚠️ Firebase config not found: {config_path}")
                print("   Firebase integration disabled.")
                return
                
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            self.database_url = config["project_info"]["firebase_url"]
            self.api_key = config["client"][0]["api_key"][0]["current_key"]
            self.device_id = "MEM001"  # Device ID as shown in screenshot
            self.enabled = True
            
            print(f"✅ Firebase initialized: {self.database_url}")
            print(f"   Device ID: {self.device_id}")
            
        except Exception as e:
            print(f"⚠️ Firebase initialization failed: {e}")
            print("   Firebase integration disabled.")
        
    def update_status(self, status, status_data=None):
        """
        Update device status in Firebase Realtime Database
        Args:
            status: str - "safe", "warning", or "danger"
            status_data: dict - Optional additional data to send
        """
        if not self.enabled:
            return False
            
        # Convert to lowercase
        status = status.lower()
        
        # Prepare data
        data = {
            "status": status,
            "lastUpdate": int(datetime.now().timestamp() * 1000),  # milliseconds
            "model": "MOMENTO Demo Device",
            "serial": "MEM001"
        }
        
        # Add additional status data if provided
        if status_data:
            data.update(status_data)
        
        # Firebase REST API endpoint (try without auth first)
        url = f"{self.database_url}/devices/{self.device_id}.json"
        
        try:
            response = requests.patch(url, json=data, timeout=5)
            if response.status_code == 200:
                if not self.error_shown:
                    print(f"✅ Firebase: Status updated to '{status}'")
                return True
            else:
                # Try with auth if no-auth failed
                url_with_auth = f"{self.database_url}/devices/{self.device_id}.json?auth={self.api_key}"
                response = requests.patch(url_with_auth, json=data, timeout=5)
                if response.status_code == 200:
                    if not self.error_shown:
                        print(f"✅ Firebase: Status updated to '{status}'")
                    return True
                else:
                    if not self.error_shown:
                        print(f"❌ Firebase update failed: {response.status_code}")
                        print(f"   Response: {response.text}")
                        print(f"   Run 'python test_firebase.py' to diagnose")
                        self.error_shown = True
                    return False
        except requests.exceptions.Timeout:
            if not self.error_shown:
                print(f"❌ Firebase timeout - check network connection")
                self.error_shown = True
            return False
        except Exception as e:
            if not self.error_shown:
                print(f"❌ Firebase error: {e}")
                print(f"   Run 'python test_firebase.py' to diagnose")
                self.error_shown = True
            return False
    
    def send_alert(self, child_id, alert_type, timestamp):
        """
        Send danger zone crossing alert to Firebase
        Args:
            child_id: int - ID of child who crossed
            alert_type: str - Type of alert (e.g., "danger_zone_entry")
            timestamp: float - Time of alert
        """
        if not self.enabled:
            return False
            
        alert_data = {
            "childId": child_id,
            "alertType": alert_type,
            "timestamp": int(timestamp * 1000),  # milliseconds
            "deviceId": self.device_id
        }
        
        # Send to alerts node (try without auth first)
        url = f"{self.database_url}/alerts.json"
        
        try:
            response = requests.post(url, json=alert_data, timeout=5)
            if response.status_code == 200:
                print(f"✅ Firebase Alert: Child {child_id} - {alert_type}")
                return True
            else:
                # Try with auth
                url_with_auth = f"{self.database_url}/alerts.json?auth={self.api_key}"
                response = requests.post(url_with_auth, json=alert_data, timeout=5)
                if response.status_code == 200:
                    print(f"✅ Firebase Alert: Child {child_id} - {alert_type}")
                    return True
                else:
                    if not self.error_shown:
                        print(f"❌ Firebase alert failed: {response.status_code}")
                        print(f"   Response: {response.text}")
                        self.error_shown = True
                    return False
        except Exception as e:
            if not self.error_shown:
                print(f"❌ Firebase alert error: {e}")
                self.error_shown = True
            return False
