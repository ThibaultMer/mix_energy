from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)
import predict.mllogs as pmllog


class Energypredict:
    __slots__ = ["__model", "__mllogger"]

    def __init__(self, mllogger: pmllog.MlLog):
        self.__model = None
        self.__mllogger = mllogger

    def create_model(self) -> None:
        self.__model = LinearRegression()

    def preproc_data(self, preproc, X_train, X_test):
        preproc.fit(X_train)
        X_train_scaled = preproc.transform(X_train)
        X_test_scaled = preproc.transform(X_test)
        return X_train_scaled, X_test_scaled

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


if __name__ == "__main__":
    mlflow_logger = pmllog.MlFlowLogger("energy")

    epredict = Energypredict(mlflow_logger)

    epredict.create_model()
