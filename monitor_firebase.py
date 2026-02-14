"""
Monitor Firebase updates in real-time
Shows current device status and alerts from Firebase Realtime Database
"""
import requests
import json
import time
from datetime import datetime

print("🔥 Firebase Real-time Monitor")
print("="*60)
print("Press Ctrl+C to stop\n")

# Load config
with open("scripts/google-services.json", 'r') as f:
    config = json.load(f)

database_url = config["project_info"]["firebase_url"]
device_id = "MEM001"

prev_status = None
prev_update = None

while True:
    try:
        # Get device status
        response = requests.get(f"{database_url}/devices/{device_id}.json", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if data:
                status = data.get("status", "unknown")
                last_update = data.get("lastUpdate", 0)
                children = data.get("children_count", 0)
                adults = data.get("adults_count", 0)
                in_danger = data.get("children_in_danger", 0)
                
                # Only print if status changed
                if status != prev_status or last_update != prev_update:
                    timestamp = datetime.fromtimestamp(last_update/1000).strftime("%H:%M:%S")
                    
                    # Color code status
                    if status == "safe":
                        status_icon = "✅"
                    elif status == "warning":
                        status_icon = "⚠️"
                    elif status == "danger":
                        status_icon = "🚨"
                    else:
                        status_icon = "❓"
                    
                    print(f"[{timestamp}] {status_icon} Status: {status.upper()}")
                    print(f"           Children: {children}, Adults: {adults}, In Danger: {in_danger}")
                    
                    prev_status = status
                    prev_update = last_update
            else:
                print("No data in Firebase yet...")
        else:
            print(f"Error reading Firebase: {response.status_code}")
        
        time.sleep(2)  # Check every 2 seconds
        
    except KeyboardInterrupt:
        print("\n\n✋ Monitoring stopped")
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)

print("\n" + "="*60)
print("View live data in Firebase Console:")
print(f"{database_url}/devices/{device_id}")
print(f"{database_url}/alerts")
