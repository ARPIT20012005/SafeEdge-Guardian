# Fixing 'lap' Error on Raspberry Pi

## Error

```
Detection error: module 'lap' has no attribute 'lapjv'
```

## Cause

The `lap` package (Linear Assignment Problem solver) is required by YOLO for object tracking, but it often fails on ARM architecture (Raspberry Pi).

## Solutions

### Solution 1: Install lap from source (Recommended)

```bash
# Activate your virtual environment
source venv/bin/activate

# Install build dependencies
sudo apt install -y build-essential cmake python3-dev

# Reinstall lap from source
pip uninstall lap -y
pip install lap --no-binary lap

# If that fails, try:
pip install "lap>=0.4.0" --no-binary :all:
```

### Solution 2: Use Alternative Tracker

If lap installation fails, modify the YOLO detector to use ByteTrack (doesn't require lap):

In [detectors/yolo_person_detector.py](e:\SafeEdge-Guardian\detectors\yolo_person_detector.py), change:

```python
results = self.model.track(
    frame,
    conf=self.conf_thresh,
    persist=True,
    tracker="bytetrack.yaml",  # Add this line
    verbose=False
)
```

### Solution 3: Disable Tracking (Simple Detection Only)

If tracking isn't critical, replace `.track()` with `.predict()`:

```python
results = self.model.predict(
    frame,
    conf=self.conf_thresh,
    verbose=False
)
```

Then modify the detection parsing to handle missing IDs:

```python
person_id = int(box.id[0]) if box.id is not None else i
```

### Solution 4: Install Compatible Wheel

```bash
# For ARM64/aarch64
pip install https://github.com/gatagat/lap/releases/download/0.4.0/lap-0.4.0-cp39-cp39-linux_aarch64.whl
```

_Note: Adjust the Python version (cp39) to match your Python version._

## Quick Test

After applying any solution, test with:

```bash
python main.py --source 0 --skip-frames 10
```

## Verification

Run Python and test:

```python
import lap
print(lap.lapjv)  # Should not error
```

## Additional Help

If all solutions fail, you can run without tracking by using the modified detector in Solution 3.
