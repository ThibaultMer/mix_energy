import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)
import predict.mllogs as pmllog
from predict.preproc import build_pipeline

from predict import get_logger

logger = get_logger()


class Energypredict:
    """
    Class to manage the ML model for predicting energy consumption at T+15 minutes
    """

    __slots__ = ["__model", "__mllogger"]

    def __init__(self, mllogger: pmllog.MlLog):
        """
        Constructor of the class

        Params
        ------
        mllogger: The object responsible of saving and loading the ML model
        """

        self.__model = None
        self.__mllogger = mllogger

    def create_model(self) -> None:
        """
        Create a new ML model
        """
        self.__model = LinearRegression()
        self.__mllogger.log_hyperparams(self.__model.get_params())
        logger.info("Creation of the model")

    def preprocess_data(self, X: pd.DataFrame, train: bool = True) -> pd.DataFrame:
        """
        Preprocess the data to be ready to be used by the model.

        Params
        ------
        X : dataframe to be transformed
        train: Is it for training ?

        Returns
        -------
        The transformed dataframe

        """

        # Instantier la pipeline
        if train:
            preprocessor = build_pipeline()
            preprocessor.fit(X)
            self.__mllogger.save_model(preprocessor, "preprocessor")
        else:
            preprocessor = self.__mllogger.load_model("preprocessor")
        df_preprocessed = preprocessor.transform(X)

        logger.info("Preprocessed data")

        return df_preprocessed

    def train_model(self, X_train, y_train) -> None:
        """Train the model in place and save it."""
        if self.__model is not None:
            self.__model.fit(X_train, y_train)
            self.__mllogger.save_model(self.__model, "energy_pred")
            logger.info("ML model saved")

    def evaluate_model(self, X_test, y_test) -> dict:
        if self.__model is None:
            try:
                self.__mllogger.load_model("energy_pred")
            except Exception:
                get_logger().error("Fail to load the model")
                return {}

        y_pred = self.__model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        mape = mean_absolute_percentage_error(y_test, y_pred)
        print(
            f"Evaluation metrics: MAE={mae:.2f}, MSE={mse:.2f}, R2={r2:.2f}, MAPE={mape:.2%}"
        )
        metrics = {"mae": mae, "mse": mse, "r2": r2, "mape": mape}
        self.__mllogger.log_metrics(metrics)

        logger.info(f"model performance metrics : {metrics}")

        return metrics

    def predict(self, input_vals: pd.DataFrame) -> float | None:
        pred = self.__model.predict(input_vals)
        if pred is not None:
            logger.info(f"From {input_vals} predicted an energy consumption of {pred}")
        else:
            logger.error(f"Fail to realize a prediction from {input_vals}")

        return pred
