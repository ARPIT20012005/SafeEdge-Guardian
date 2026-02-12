import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

# Load dataset
df = pd.read_csv("data/features/pose_features.csv")

# 🔍 DEBUG: print columns once
print("CSV Columns:", df.columns)

# Encode labels (FIXED COLUMN NAME)
df["label"] = df["role"].map({"CHILD": 0, "ADULT": 1})

# Drop rows with missing labels (safety)
df = df.dropna(subset=["label"])

# Features & target
X = df[["body_height", "shoulder_body_ratio"]]
y = df["label"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = LogisticRegression()
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))

# Save model
joblib.dump(model, "classifiers/trained_model/child_adult_model.pkl")
print("✅ Model saved to classifiers/trained_model/")
