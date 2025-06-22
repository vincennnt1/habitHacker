import joblib
import re
import numpy as np

def clean(text):
    text = text.lower()
    text = re.sub(r"http\S+|www\S+|https\S+", '', text)
    text = re.sub(r"@\w+", '', text)
    text = re.sub(r"#", '', text)
    text = re.sub(r"\s+", ' ', text).strip()
    return text

# loading model & Encoder (MUST DO ON STARTUP)
mod = joblib.load("model.job")
le = joblib.load("label_encoder.job")

# ---------- INPUT TESTING ----------
# t = input("Enter you prompt: ")
# t = [clean(t)]

# ---------- TUTORIAL ON HOW TO USE ---------

# # predicts probabilities
# pred_proba = mod.predict_proba(t)

# # gets top probaility
# pred_index = np.argmax(pred_proba, axis=1)

# # corresponding sentiment of top prob
# label = le.inverse_transform(pred_index)
# print(label[0])

# GET ALL PROBABILITIES AND CORRESPONDING SENTIMENT
# import pandas as pd

# # Predict class probabilities
# probs = model.predict_proba(cleaned)[0]  # shape: (n_classes,)
# classes = le.classes_

# # Wrap in DataFrame
# df_probs = pd.DataFrame([probs], columns=classes).T
# df_probs.columns = ["probability"]
# df_probs = df_probs.sort_values("probability", ascending=False)

# print(df_probs)