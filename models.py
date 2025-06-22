import pandas as pd
import numpy as np
import re
import joblib

# Loading & Cleaning Data
data = pd.read_csv("data.csv")

data = data[data['sentiment'] != 'empty']
data = data[data['sentiment'] != 'surprise']
data = data[data['sentiment'] != 'boredom']
data = data[data['sentiment'] != 'relief']

data["sentiment"] = data["sentiment"].replace("hate", "anger")
data["sentiment"] = data["sentiment"].replace("fun", "happiness")
data["sentiment"] = data["sentiment"].replace("enthusiasm", "happiness")

data = data[['sentiment', 'content']]

# loading and formatting extra data
data2 = pd.read_csv("text.csv")

data2 = data2.rename(columns={"text": "content"})
data2 = data2.rename(columns={"label": "sentiment"})

data2["sentiment"] = data2["sentiment"].replace(0, "sadness")
data2["sentiment"] = data2["sentiment"].replace(1, "joy")
data2["sentiment"] = data2["sentiment"].replace(2, "love")
data2["sentiment"] = data2["sentiment"].replace(3, "anger")
data2["sentiment"] = data2["sentiment"].replace(4, "fear")
data2 = data2[data2['sentiment'] != 5]

data2["sentiment"] = data2["sentiment"].replace("joy", "happiness")
data2["sentiment"] = data2["sentiment"].replace("fear", "worry")

data2 = data2[['sentiment', 'content']]

# concatenating extra data
data = pd.concat([data, data2], ignore_index=True)
data = data.sample(frac=1, random_state=2025).reset_index(drop=True)

data = data[data['sentiment'] != 'neutral']

def clean_tweet(text):
    text = text.lower()
    text = re.sub(r"http\S+|www\S+|https\S+", '', text)
    text = re.sub(r"@\w+", '', text)
    text = re.sub(r"#", '', text)
    text = re.sub(r"\s+", ' ', text).strip()
    return text

data["content"] = data["content"].apply(clean_tweet)

from sklearn.preprocessing import LabelEncoder

le = LabelEncoder()
data["label"] = le.fit_transform(data["sentiment"])

joblib.dump(le, "label_encoder.job")


# print(data['sentiment'].unique())
# print(data.info())

from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    data.content,
    data.label,
    test_size=0.2,
    random_state=2025,
    stratify=data.label
)


from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV

clf = Pipeline([
    ('tfidf', TfidfVectorizer(stop_words='english', ngram_range=(1,2))),
    ('log', LogisticRegression(solver='lbfgs', class_weight='balanced', max_iter=100000))
])

# # Hyperparameter grid
param_grid = {
    'tfidf__max_df': [0.7],
    'tfidf__min_df': [2],
    'log__C': [.2]
}

# Set up grid search with 5-fold cross-validation,
# scoring by F1 score to balance precision and recall,
# verbose output and parallel computation enabled
grid = GridSearchCV(
    clf,
    param_grid,
    cv=3,
    scoring='f1_weighted',
    verbose=1,
    n_jobs=2
)

# Train model and search for best hyperparameters on training data
grid.fit(X_train, y_train)
best_model = grid.best_estimator_

# Report on Model
from sklearn.metrics import classification_report
y_pred = best_model.predict(X_test)

# INFO ON MODEL
print(classification_report(y_test, y_pred, target_names=le.classes_))    
print(grid.best_params_)


# Serializing Model
joblib.dump(best_model, "model.job")
