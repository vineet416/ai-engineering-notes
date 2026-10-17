# A tiny prediction API. The app itself is not the point of this folder.
# It exists so the Docker image has real, heavy dependencies
# (scikit-learn, scipy, numpy, pandas) that take a while to pip install.

import logging

import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression

logger = logging.getLogger("uvicorn.error")

# measure_builds.py edits this one line to simulate a small code change.
STARTUP_MESSAGE = "Iris model is ready"

app = FastAPI(title="Iris predictor")

# Train a small model once at startup. The iris dataset ships inside
# scikit-learn, so nothing is downloaded here.
iris = load_iris(as_frame=True)
model = LogisticRegression(max_iter=500).fit(iris.data, iris.target)
logger.info(STARTUP_MESSAGE)


class Flower(BaseModel):
    sepal_length: float = Field(gt=0, examples=[5.1])
    sepal_width: float = Field(gt=0, examples=[3.5])
    petal_length: float = Field(gt=0, examples=[1.4])
    petal_width: float = Field(gt=0, examples=[0.2])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(flower: Flower):
    row = pd.DataFrame([[
        flower.sepal_length, flower.sepal_width,
        flower.petal_length, flower.petal_width,
    ]], columns=iris.data.columns)
    label = int(model.predict(row)[0])
    return {"species": str(iris.target_names[label])}
