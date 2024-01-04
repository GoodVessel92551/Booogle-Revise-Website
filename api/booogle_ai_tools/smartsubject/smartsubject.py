import numpy as np
import pickle
import csv
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.svm import LinearSVC

try:
    with open("booogle_ai_tools/smartsubject/smartsubject_pkl.pkl", "rb") as f:
        clf = pickle.load(f)
        vectorizer = pickle.load(f)
except FileNotFoundError:
    with open("booogle_ai_tools/smartsubject/smartsubject_csv.csv", "r") as f:
        reader = csv.DictReader(f)
        data = list(reader)
    texts = []
    labels = []
    for i in data:
        labels.append(i["subject"])
        texts.append(i["name"])

    vectorizer = CountVectorizer()  # Use CountVectorizer for faster processing
    X = vectorizer.fit_transform(texts)

    clf = LinearSVC()
    clf.fit(X, labels)

    with open("api/booogle_ai_tools/smartsubject/smartsubject_pkl.pkl", "wb") as f:
        pickle.dump(clf, f)
        pickle.dump(vectorizer, f)


def text(text):
    X = vectorizer.transform([text])
    label = clf.predict(X)[0]
    return label