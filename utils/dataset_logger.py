import csv
import os
import time

class DatasetLogger:
    def __init__(self, filepath="data/features/pose_features.csv"):
        self.filepath = filepath
        self.header = [
            "timestamp",
            "person_id",
            "body_height",
            "shoulder_body_ratio",
            "role"
        ]

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Write header ONLY once
        if not os.path.exists(filepath):
            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(self.header)

    def log(self, person_id, features, role):
        with open(self.filepath, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                time.time(),
                person_id,
                features["body_height"],
                features["shoulder_body_ratio"],
                role
            ])
