from ultralytics import YOLO

class YOLOPersonDetector:
    def __init__(self,
                 model_path="yolov8n-pose.pt",
                 conf_thresh=0.4):
        """
        YOLOv8 Pose detector (person + keypoints)
        """
        self.model = YOLO(model_path)
        self.conf_thresh = conf_thresh
        self.use_tracking = True
        self.tracking_error_shown = False
        self.next_id = 0  # Fallback ID generator

    def detect(self, frame):
        """
        Returns list of persons:
        [
            {
                "id": int,
                "bbox": (x1, y1, x2, y2),
                "keypoints": [(x, y), ...],
                "confidence": float
            }
        ]
        """
        # Try tracking first, fall back to detection if tracking fails
        try:
            if self.use_tracking:
                results = self.model.track(
                    frame,
                    conf=self.conf_thresh,
                    persist=True,
                    tracker="bytetrack.yaml",  # ByteTrack doesn't require lap
                    verbose=False
                )
            else:
                results = self.model.predict(
                    frame,
                    conf=self.conf_thresh,
                    verbose=False
                )
        except Exception as e:
            # Tracking failed (likely lap issue on Raspberry Pi)
            if not self.tracking_error_shown:
                print(f"⚠️  Tracking disabled due to error: {e}")
                print("   Using detection-only mode. See docs/raspberry_pi_lap_fix.md")
                self.tracking_error_shown = True
            self.use_tracking = False
            
            # Fallback to prediction
            results = self.model.predict(
                frame,
                conf=self.conf_thresh,
                verbose=False
            )

        persons = []

        for r in results:
            if r.boxes is None or r.keypoints is None:
                continue

            for i, box in enumerate(r.boxes):
                # Try to get tracking ID, or generate one
                if box.id is not None:
                    person_id = int(box.id[0])
                else:
                    # Fallback ID generation
                    person_id = self.next_id
                    self.next_id += 1

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])

                kps = r.keypoints.xy[i].tolist()

                persons.append({
                    "id": person_id,
                    "bbox": (x1, y1, x2, y2),
                    "keypoints": kps,
                    "confidence": round(conf, 2)
                })

        return persons
