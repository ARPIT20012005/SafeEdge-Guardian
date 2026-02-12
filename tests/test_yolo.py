import cv2
from detectors.yolo_person_detector import YOLOPersonDetector
from features.feature_extractor import FeatureExtractor
from classifiers.role_classifier import RoleClassifier
from logic.danger_zone import DangerZone
from logic.supervision import SupervisionChecker
from utils.dataset_logger import DatasetLogger

def main():
    cap = cv2.VideoCapture(0)
    detector = YOLOPersonDetector()
    extractor = FeatureExtractor()
    classifier = RoleClassifier()
    supervisor = SupervisionChecker()
    logger = DatasetLogger()

    danger_zone = None

    print("PHASE 7: ADULT SUPERVISION ACTIVE")
    print("Press 'q' to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        h, w, _ = frame.shape
        if danger_zone is None:
            danger_zone = DangerZone(w, h)

        # Draw danger zone
        zx1, zy1, zx2, zy2 = danger_zone.get_zone()
        cv2.rectangle(frame, (zx1, zy1), (zx2, zy2), (0, 0, 255), 3)
        cv2.putText(frame, "DANGER ZONE", (zx1 + 5, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        persons = detector.detect(frame)

        children = []
        adults = []

        for p in persons:
            pid = p["id"]
            x1, y1, x2, y2 = p["bbox"]
            keypoints = p["keypoints"]

            features = extractor.extract(keypoints)
            role, _ = classifier.classify(features)
           
            logger.log(pid, features, role)

            # Use head keypoint
            cx, cy = keypoints[0]

            if role == "CHILD":
                children.append((pid, (cx, cy)))
                color = (0, 255, 255)
            else:
                adults.append((pid, (cx, cy)))
                color = (0, 255, 0)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"ID {pid} | {role}",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        status = "SAFE"

        for cid, cpos in children:
            in_danger = danger_zone.is_inside(int(cpos[0]), int(cpos[1]))

            if not in_danger:
                continue

            attentive = False
            has_adult = False
            for aid, apos in adults:
                has_adult = True
                if supervisor.is_attentive(aid, apos, cpos):
                    attentive = True
                    break

            if not attentive:
                if not has_adult:
                    status = "DANGER"
                else:
                    status = "WARNING"
            else:
                if status == "SAFE":
                    status = "WARNING"

            if status == "DANGER":
                break

        # Display global status
        if status == "SAFE":
            color = (0, 255, 0)
        elif status == "WARNING":
            color = (0, 255, 255)
        else:
            color = (0, 0, 255)

        cv2.putText(frame,
                    f"STATUS: {status}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,
                    color,
                    3)

        cv2.imshow("SafeEdge Guardian — Phase 7", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
