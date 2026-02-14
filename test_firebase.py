"""
Test Firebase connectivity and diagnose issues
"""
import requests
import json
from datetime import datetime

print("🔥 Firebase Connection Test\n")

# Load config
try:
    with open("scripts/google-services.json", 'r') as f:
        config = json.load(f)
    print("✅ Config file loaded successfully")
except Exception as e:
    print(f"❌ Failed to load config: {e}")
    exit(1)

# Extract credentials
database_url = config["project_info"]["firebase_url"]
api_key = config["client"][0]["api_key"][0]["current_key"]
device_id = "MEM001"

print(f"📡 Database URL: {database_url}")
print(f"🔑 API Key: {api_key[:10]}...{api_key[-5:]}")
print(f"🖥️  Device ID: {device_id}\n")

# Test 1: Write to Firebase (no auth)
print("Test 1: Writing without auth...")
url_no_auth = f"{database_url}/devices/{device_id}.json"
test_data = {
    "status": "test",
    "timestamp": int(datetime.now().timestamp() * 1000),
    "test": "connectivity_check"
}

try:
    response = requests.patch(url_no_auth, json=test_data, timeout=5)
    print(f"   Response: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Write successful (no auth needed)")
        print(f"   Data: {response.json()}")
    else:
        print(f"   ❌ Failed: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# Test 2: Write to Firebase (with auth)
print("Test 2: Writing with auth...")
url_with_auth = f"{database_url}/devices/{device_id}.json?auth={api_key}"

try:
    response = requests.patch(url_with_auth, json=test_data, timeout=5)
    print(f"   Response: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Write successful (with auth)")
        print(f"   Data: {response.json()}")
    else:
        print(f"   ❌ Failed: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# Test 3: Read from Firebase
print("Test 3: Reading data...")
try:
    response = requests.get(f"{database_url}/devices/{device_id}.json", timeout=5)
    print(f"   Response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Read successful")
        print(f"   Current data: {json.dumps(data, indent=2)}")
    else:
        print(f"   ❌ Failed: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*60)
print("TROUBLESHOOTING TIPS:")
print("="*60)
print("If all tests fail:")
print("1. Check Firebase Console → Realtime Database → Rules")
print("2. Rules should allow write access (for testing, use:)")
print('   {')
print('     "rules": {')
print('       ".read": true,')
print('       ".write": true')
print('     }')
print('   }')
print("3. Make sure database is in 'Test mode' or has proper rules")
print("4. Check if the database URL is correct and database is created")
print(f"5. Visit: {database_url} in browser to verify it exists")
