import joblib
import numpy as np
import pandas as pd

class RoleClassifier:
    def __init__(self):
        self.model = joblib.load(
            "classifiers/trained_model/child_adult_model.pkl"
        )

    def classify(self, features):
        # Use pandas DataFrame with feature names to avoid sklearn warning
        X = pd.DataFrame([[features["body_height"], features["shoulder_body_ratio"]]], 
                        columns=["body_height", "shoulder_body_ratio"])

        prob = self.model.predict_proba(X)[0]
        label = self.model.predict(X)[0]

        if label == 1:
            return "ADULT", round(prob[1], 2)
        else:
            return "CHILD", round(prob[0], 2)
