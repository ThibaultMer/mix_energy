import os
import mlflow
import abc
from sklearn.base import BaseEstimator

MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "local")


class MlLog(abc.ABC):
    def __init__(self, savename: str):
        self.savename = savename

    @classmethod
    @abc.abstractmethod
    def save_model(self, model: BaseEstimator, name=str):
        pass

    @classmethod
    @abc.abstractmethod
    def log_hyperparams(self, params: dict):
        pass

    @classmethod
    @abc.abstractmethod
    def log_metrics(self, metrics: dict):
        pass

    @classmethod
    @abc.abstractmethod
    def load_model(self, name: str) -> BaseEstimator:
        pass


class MlFlowLogger(MlLog):
    def __init__(self, savename: str):
        super.__init__(savename)
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow.set_experiment(self.savename)

    def save_model(self, model: BaseEstimator, name: str):
        mlflow.sklearn.log_model(sk_model=model, name=name)

    def log_hyperparams(self, params: dict):
        mlflow.log_params(params)

    def log_metrics(self, metrics):
        mlflow.log_metrics(metrics)

    def load_model(self, name: str) -> BaseEstimator:
        return mlflow.sklearn.load_model(MLFLOW_TRACKING_URI)

    def __enter__(self):
        mlflow.start_run()
        return self

    def __exit__(self, exec_type, exec_val, exc_tb):
        mlflow.end_run()
