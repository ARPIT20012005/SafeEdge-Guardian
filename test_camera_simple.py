import cv2
import time

print("Testing camera access...")
print("Press 'q' to quit\n")

# Try opening camera with different backends
backends = [
    (cv2.CAP_DSHOW, "DirectShow (Windows default)"),
    (cv2.CAP_MSMF, "Media Foundation"),
    (cv2.CAP_ANY, "Auto-detect")
]

for backend, name in backends:
    print(f"Trying {name}...")
    cap = cv2.VideoCapture(0, backend)
    
    if cap.isOpened():
        print(f"✓ Camera opened with {name}")
        
        # Try to read a few frames
        success_count = 0
        for i in range(10):
            ret, frame = cap.read()
            if ret:
                success_count += 1
                if i == 0:
                    h, w = frame.shape[:2]
                    print(f"  Frame size: {w}x{h}")
            time.sleep(0.1)
        
        print(f"  Successfully read {success_count}/10 frames\n")
        
        if success_count >= 8:
            print("✅ Camera is working! Starting live preview...")
            print("Press 'q' to quit\n")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("⚠ Lost frame")
                    continue
                
                cv2.imshow('Camera Test', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cap.release()
            cv2.destroyAllWindows()
            break
        else:
            cap.release()
    else:
        print(f"✗ Failed to open with {name}\n")

print("\nTest complete!")
