# SafeEdge Guardian - Setup Guide

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd SafeEdge-Guardian
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 3. Download YOLO Models

The YOLO model files are not included in the repository due to size constraints.

Download them automatically:

```bash
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt'); YOLO('yolov8n-pose.pt')"
```

Or manually download:

- `yolov8n.pt` - [YOLOv8 Nano](https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt)
- `yolov8n-pose.pt` - [YOLOv8 Nano Pose](https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n-pose.pt)

Place them in the project root directory.

### 4. Configure Firebase

1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Download `google-services.json`
3. Place it in `scripts/google-services.json`
4. Update [utils/firebase_uploader.py](utils/firebase_uploader.py) with your database URL

### 5. Train the Classifier

Generate training data and train the child/adult classifier:

```bash
# Collect dataset (press 'c' for CHILD, 'a' for ADULT, 'q' to quit)
python scripts/collect_dataset.py

# Train the model
python scripts/train_classifier.py
```

This will create `classifiers/trained_model/child_adult_model.pkl`

### 6. Run the Application

```bash
# Using webcam
python main.py --source 0

# Using IP camera
python main.py --source http://192.168.1.100:8080/video

# Headless mode (no display)
python main.py --source 0 --no-display
```

## 📱 Raspberry Pi Setup

For Raspberry Pi deployment, run:

```bash
chmod +x setup_pi.sh
./setup_pi.sh
```

See [docs/raspberry_pi_lap_fix.md](docs/raspberry_pi_lap_fix.md) for troubleshooting.

## 🧪 Testing

```bash
# Test YOLO detection
python tests/test_yolo.py

# Test camera connection
python test_camera_simple.py

# Test Firebase
python test_firebase.py

# Test stream stability (IP camera)
python test_stream_stability.py --source <stream-url>
```

## 📖 Documentation

- [Architecture](docs/architecture.md)
- [Streaming Optimization](docs/streaming_optimization.md)
- [PPT Points](docs/ppt_points.md)

## ⚠️ Important Files NOT in Repository

These files are excluded for security/size reasons:

- ✗ `yolov8n.pt` (6 MB) - Download via setup
- ✗ `yolov8n-pose.pt` (6 MB) - Download via setup
- ✗ `scripts/google-services.json` - Create your own Firebase project
- ✗ `classifiers/trained_model/*.pkl` - Train after collecting data
- ✗ `data/features/*.csv` - Generated during data collection

## 🛠️ Features

✅ Real-time person detection (YOLO)  
✅ Child/Adult classification (custom ML model)  
✅ Danger zone monitoring  
✅ Supervision checking  
✅ Firebase real-time alerts  
✅ IP camera support with auto-reconnection  
✅ Raspberry Pi compatible

## 🔐 Security

Firebase credentials are kept secure:

- Never commit `google-services.json` to git
- It's in `.gitignore` for your protection
- Each user must create their own Firebase project

---

**Need Help?** Check the [docs/](docs/) folder or open an issue!
