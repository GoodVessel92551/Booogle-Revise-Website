import pickle
import csv
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.svm import LinearSVC

with open("api/booogle_ai_tools/moderation/moderation_pkl.pkl", "rb") as f:
    clf = pickle.load(f)
    vectorizer = pickle.load(f)

def prompt(prompt):
    X = vectorizer.transform([prompt])
    label = clf.predict(X)[0]
    return label