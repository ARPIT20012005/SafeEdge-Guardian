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
        results = self.model.track(
            frame,
            conf=self.conf_thresh,
            persist=True,
            verbose=False
        )

        persons = []

        for r in results:
            if r.boxes is None or r.keypoints is None:
                continue

            for i, box in enumerate(r.boxes):
                if box.id is None:
                    continue

                person_id = int(box.id[0])
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
