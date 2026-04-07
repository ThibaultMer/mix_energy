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


class Energypredict:
    __slots__ = ["__model", "__mllogger"]

    def __init__(self, mllogger: pmllog.MlLog):
        self.__model = None
        self.__mllogger = mllogger

    def create_model(self) -> None:
        self.__model = LinearRegression()
        self.__mllogger.log_hyperparams(self.__model.get_params())

    def preprocess_data(self, X: pd.DataFrame, train: bool = True) -> pd.DataFrame:
        # Instantier la pipeline
        if train:
            preprocessor = build_pipeline()
            preprocessor.fit(X)
            self.__mllogger.save_model(preprocessor, "preprocessor")
        else:
            preprocessor = self.__mllogger.load_model("preprocessor")
        df_preprocessed = preprocessor.transform(X)
        # logger.info(f"Preprocessed the diamonds dataset: {X.shape} -> {df_preprocessed.shape}")
        return df_preprocessed

    def train_model(self, X_train, y_train) -> None:
        """Train the model in place and save it."""
        self.__model.fit(X_train, y_train)
        self.__mllogger.save_model(self.__model, "energy_model")

    def evaluate_model(self, X_test, y_test) -> dict:
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

        return metrics

    def predict(self, input_vals):
        return self.__model.predict(input_vals)


if __name__ == "__main__":
    mlflow_logger = pmllog.MlFlowLogger("energy")

    epredict = Energypredict(mlflow_logger)

    epredict.create_model()
