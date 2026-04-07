from predict.model import Energypredict
from predict.mllogs import MlFlowLogger
from predict.data import create_X_y


def train(
    model_name: str = "baseline",
    test_size: float = 0.2,
    random_state: int = 42,
) -> None:
    """ """

    with MlFlowLogger("energy") as mlogger:
        predicteng = Energypredict(mlogger)

        # Add here the import of the data used to train
        df = []

        X_train, X_test, y_train, y_test = create_X_y(
            df, test_size=test_size, random_state=random_state
        )

        X_train_preproc = predicteng.preprocess_data(X_train, train=True)
        X_test_preproc = predicteng.preprocess_data(X_test, train=False)

        predicteng.train_model(X_train=X_train_preproc, y_train=y_train)
        predicteng.evaluate_model(X_test=X_test_preproc, y_test=y_test)
