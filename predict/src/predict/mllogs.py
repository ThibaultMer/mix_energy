import os
import mlflow
import abc
import pickle
from sklearn.base import BaseEstimator
from predict import get_logger
from datetime import date

MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")


# -------------------------------------------------------------------------
# Base class for Machine Learning Model logger
# -------------------------------------------------------------------------
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


# -------------------------------------------------------------------------
# Machine Learning Model File logger
# -------------------------------------------------------------------------
class MlFileLogger(MlLog):
    def __init__(self, savename: str):
        super.__init__(savename)
        self.__file = None

    def save_model(self, model: BaseEstimator, name: str):
        if self.__file is not None:
            pickle.dump(model, self.__file)

    def log_hyperparams(self, params: dict):
        pass

    def log_metrics(self, metrics):
        pass

    def load_model(self, name: str) -> BaseEstimator:
        if self.__file is not None:
            pickle.load(self.__file)
        else:
            return None

    def __enter__(self):
        self.__file = open(self.savename, "rw")
        return self

    def __exit__(self, exec_type, exec_val, exc_tb):
        self.__file.close()
        self.__file = None


# -------------------------------------------------------------------------
# Machine Learning Model MLFLOW logger
# -------------------------------------------------------------------------
class MlFlowLogger(MlLog):
    def __init__(self, savename: str):
        super().__init__(savename)
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

        current_date = date.today()
        experiment = f"Energy Model Tracking {current_date.month}_{current_date.year}"
        get_logger().info(f"Experimentation : {experiment}")
        mlflow.set_experiment(experiment)

    def save_model(self, model: BaseEstimator, name: str):
        model_name = f"{self.savename}_{name}"
        mlflow.sklearn.log_model(
            sk_model=model, name=model_name, registered_model_name=model_name
        )

    def log_hyperparams(self, params: dict):
        mlflow.log_params(params)

    def log_metrics(self, metrics):
        mlflow.log_metrics(metrics)

    def load_model(self, name: str) -> BaseEstimator:
        model_uri = f"models:/{self.savename}_{name}/latest"
        estimator = mlflow.sklearn.load_model(model_uri)
        get_logger().info(
            f"Load last registered {self.savename}_{name} model from mlflow server"
        )
        return estimator

    def __enter__(self):
        mlflow.start_run()
        return self

    def __exit__(self, exec_type, exec_val, exc_tb):
        mlflow.end_run()
