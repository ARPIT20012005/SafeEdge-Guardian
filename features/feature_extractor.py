import math

class FeatureExtractor:
    def extract(self, keypoints):
        """
        keypoints: list of (x, y) from YOLOv8 pose
        """

        def dist(p1, p2):
            return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

        head = keypoints[0]
        left_shoulder = keypoints[5]
        right_shoulder = keypoints[6]
        left_hip = keypoints[11]
        right_hip = keypoints[12]

        body_height = dist(head, ((left_hip[0]+right_hip[0])/2,
                                  (left_hip[1]+right_hip[1])/2))
        shoulder_width = dist(left_shoulder, right_shoulder)

        return {
            "body_height": round(body_height, 2),
            "shoulder_body_ratio": round(
                shoulder_width / body_height if body_height != 0 else 0, 3)
        }
