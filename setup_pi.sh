#!/bin/bash
# SafeEdge Guardian - Raspberry Pi Setup Script
# Run this script on your Raspberry Pi to set up the project

set -e  # Exit on error

echo "🍓 SafeEdge Guardian - Raspberry Pi Setup"
echo "=========================================="
echo

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null && ! grep -q "BCM" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  WARNING: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Python version
echo "📋 Checking Python version..."
PYTHON_VERSION=$(python3 --version | grep -oP '\d+\.\d+')
MIN_VERSION="3.9"
if (( $(echo "$PYTHON_VERSION < $MIN_VERSION" | bc -l) )); then
    echo "❌ Python 3.9+ required. Found: $PYTHON_VERSION"
    exit 1
fi
echo "✅ Python $PYTHON_VERSION found"
echo

# Update system
read -p "Update system packages? (recommended) (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "📦 Updating system..."
    sudo apt update
    sudo apt upgrade -y
fi

# Install system dependencies
echo
echo "📦 Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-opencv \
    libopencv-dev \
    libatlas-base-dev \
    libopenblas-dev \
    libjpeg-dev \
    libcamera-dev \
    git

# Check if camera support is needed
echo
read -p "Are you using Pi Camera Module? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📷 Installing Pi Camera support..."
    sudo apt install -y python3-picamera2 || echo "⚠️  picamera2 installation from apt failed, will try pip"
    
    echo
    echo "📝 Enabling camera in raspi-config..."
    echo "   Please enable Camera in: Interface Options -> Camera"
    read -p "Press Enter to open raspi-config..." 
    sudo raspi-config
fi

# Create virtual environment
echo
echo "🐍 Creating virtual environment..."
if [ -d "venv" ]; then
    read -p "Virtual environment already exists. Recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
    fi
else
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo
echo "📦 Installing Python dependencies..."
echo "⏳ This may take 30-60 minutes for PyTorch..."

if [ -f "requirements_pi.txt" ]; then
    pip install -r requirements_pi.txt
else
    echo "⚠️  requirements_pi.txt not found, using requirements.txt"
    pip install -r requirements.txt
fi

# Check if YOLO models exist
echo
echo "🔍 Checking for YOLO models..."
if [ ! -f "yolov8n-pose.pt" ]; then
    echo "⚠️  yolov8n-pose.pt not found. It will download on first run."
fi

# Check if classifier model exists
echo
echo "🤖 Checking for classifier model..."
if [ ! -f "classifiers/trained_model/child_adult_model.pkl" ]; then
    echo "⚠️  Classifier model not found."
    read -p "Train classifier now? (requires dataset) (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f "data/features/pose_features.csv" ]; then
            python scripts/train_classifier.py
        else
            echo "❌ No dataset found at data/features/pose_features.csv"
            echo "   You'll need to transfer a pre-trained model or collect data first."
        fi
    else
        echo "   You'll need to transfer a pre-trained model from your PC:"
        echo "   scp classifiers/trained_model/child_adult_model.pkl pi@$(hostname -I | awk '{print $1}'):~/SafeEdge-Guardian/classifiers/trained_model/"
    fi
fi

# Test camera
echo
read -p "Test camera now? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "📷 Testing camera (press 'q' to quit)..."
    python test_camera_simple.py || echo "⚠️  Camera test failed"
fi

# Performance recommendations
echo
echo "⚡ Performance Recommendations:"
echo "   1. Enable GPU memory: sudo raspi-config -> Performance -> GPU Memory -> 256MB"
echo "   2. Ensure adequate cooling (heatsink/fan)"
echo "   3. Use lower resolution: --skip-frames 10 --target-fps 5"
echo "   4. For headless mode: --no-display"
echo

# Create systemd service
read -p "Create systemd service for autostart? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    SERVICE_FILE="/etc/systemd/system/safeedge.service"
    WORK_DIR="$(pwd)"
    
    sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=SafeEdge Guardian Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORK_DIR
Environment="PATH=$WORK_DIR/venv/bin"
ExecStart=$WORK_DIR/venv/bin/python $WORK_DIR/main.py --source 0 --no-display
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    echo "✅ Service created at $SERVICE_FILE"
    echo
    read -p "Enable service to start on boot? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl enable safeedge.service
        echo "✅ Service enabled"
        echo
        read -p "Start service now? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo systemctl start safeedge.service
            sleep 2
            sudo systemctl status safeedge.service
        fi
    fi
fi

echo
echo "✅ Setup Complete!"
echo
echo "📝 Quick Start:"
echo "   source venv/bin/activate"
echo "   python main.py --source 0"
echo
echo "📚 For more info, see docs/raspberry_pi_deployment.md"
echo

deactivate
