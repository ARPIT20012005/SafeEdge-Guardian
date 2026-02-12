import cv2

url = "http://172.18.132.254:8080"

print(f"Testing stream connection to: {url}")
cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print("Failed to open stream")
    exit()

print("Stream opened successfully")

frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        print("Frame read failed")
        break

    frame_count += 1
    if frame_count % 30 == 0:
        print(f"Frames received: {frame_count}")

    cv2.imshow("MEMENTO Stream Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print(f"Total frames received: {frame_count}")
