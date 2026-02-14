import cv2

print("Checking available cameras...")
print("-" * 40)

available_cameras = []

for i in range(10):  # Check first 10 indices
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            available_cameras.append(i)
            print(f"✓ Camera {i}: Available")
            # Get camera properties
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            fps = cap.get(cv2.CAP_PROP_FPS)
            print(f"  Resolution: {int(width)}x{int(height)}, FPS: {int(fps)}")
        else:
            print(f"✗ Camera {i}: Opened but cannot read frames")
        cap.release()
    else:
        if i < 3:  # Only show first 3 failed attempts
            print(f"✗ Camera {i}: Not available")

print("-" * 40)
print(f"\nFound {len(available_cameras)} available camera(s): {available_cameras}")

if len(available_cameras) == 0:
    print("\n⚠ No cameras detected!")
elif len(available_cameras) == 1:
    print(f"\n💡 Only one camera found. Use --source {available_cameras[0]}")
else:
    print(f"\n💡 Multiple cameras found:")
    for idx in available_cameras:
        print(f"   - Camera {idx}: Use --source {idx}")
