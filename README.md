# SafeEdge Guardian

**Real-time Child Safety Monitoring System using Edge AI**

## 🎯 Project Overview

SafeEdge Guardian is an intelligent computer vision system that monitors children's safety in real-time using edge computing. The system detects potential dangers by tracking children's proximity to hazard zones and ensuring adult supervision.

## ✨ Key Features

- **Real-time Person Detection**: YOLO-based detection with pose estimation
- **Child/Adult Classification**: Custom ML model trained on body proportions
- **Danger Zone Monitoring**: Configurable hazard zones with real-time tracking
- **Supervision Checking**: Monitors adult attention and proximity to children
- **Firebase Integration**: Cloud-based alert system with real-time updates
- **Edge Computing**: Runs on Raspberry Pi or standard PC
- **IP Camera Support**: Robust streaming with auto-reconnection

## 🏗️ System Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Camera    │────▶│  YOLO Detector   │────▶│  Classifier │
│ (IP/Local)  │     │  (Person + Pose) │     │(Child/Adult)│
└─────────────┘     └──────────────────┘     └─────────────┘
                              │                       │
                              ▼                       ▼
                    ┌──────────────────────────────────┐
                    │      Risk Engine                 │
                    │  • Danger Zone Check             │
                    │  • Supervision Status            │
                    │  • Alert Generation              │
                    └──────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Firebase Cloud  │
                    │  (Real-time DB)  │
                    └──────────────────┘
```

## 🚀 Quick Start

See [SETUP.md](SETUP.md) for detailed installation instructions.

```bash
# Install dependencies
pip install -r requirements.txt

# Download models (automatic)
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt'); YOLO('yolov8n-pose.pt')"

# Run the system
python main.py --source 0
```

## 📋 Requirements

- Python 3.9+
- OpenCV 4.8+
- PyTorch 2.1+
- Ultralytics YOLOv8
- Firebase account (for cloud features)

## 📁 Project Structure

```
SafeEdge-Guardian/
├── main.py                 # Main application entry point
├── detectors/              # YOLO person detection
├── pose/                   # Pose estimation
├── features/               # Feature extraction
├── classifiers/            # Child/Adult classification
├── logic/                  # Risk assessment & supervision
├── utils/                  # Camera, Firebase, drawing utilities
├── config/                 # Configuration files
├── tests/                  # Unit tests
└── docs/                   # Documentation
```

## 🧪 Testing & Validation

```bash
# Test detection pipeline
python tests/test_yolo.py

# Test stream stability
python test_stream_stability.py --source <camera-url>

# Test Firebase connectivity
python test_firebase.py
```

## 📊 Performance

- **FPS**: 15-30 on Raspberry Pi 4, 30+ on PC
- **Detection Accuracy**: >90% (YOLO v8 nano)
- **Classification Accuracy**: ~85-95% (depends on training data)
- **Latency**: <100ms end-to-end on edge device

## 🔧 Configuration

Edit config files in `config/`:

- `system_config.yaml` - System-wide settings
- `danger_zone.yaml` - Hazard zone definitions
- `yolo_config.yaml` - Detection parameters

## 📖 Documentation

- [Architecture Details](docs/architecture.md)
- [Streaming Optimization](docs/streaming_optimization.md)
- [Raspberry Pi Setup](docs/raspberry_pi_lap_fix.md)
- [Presentation Points](docs/ppt_points.md)

## 🤝 Contributing

This project is for academic evaluation. For questions or improvements, please contact the development team.

## ⚠️ Important Notes

1. **Model Files**: YOLO models (~6MB each) are not included - download via setup
2. **Firebase Credentials**: Create your own Firebase project - credentials not included
3. **Training Data**: Collect and train your own classifier for best results
4. **Privacy**: Designed for controlled environments with proper consent

## 📄 License

Academic Project - SafeEdge Guardian Team

---

**For Setup Instructions**: See [SETUP.md](SETUP.md)  
**For Technical Details**: See [docs/architecture.md](docs/architecture.md)
