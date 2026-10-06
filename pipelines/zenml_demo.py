# pipelines/zenml_demo.py
from zenml import pipeline
from steps.zenml_demo import greet


@pipeline
def zenml_demo(name: str = "World"):
    greet(name=name)
