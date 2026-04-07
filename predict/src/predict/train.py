from predict.model import Energypredict
from predict.mllogs import MlFlowLogger
from predict.data import load_data, create_X_y


def train(
    is_national: bool = True,
    test_size: float = 0.2,
    random_state: int = 42,
) -> None:
    """ """

    if is_national:
        savename = "national_model"
    else:
        savename = "region_model"

    with MlFlowLogger(savename) as mlogger:
        predicteng = Energypredict(mlogger)

        # Import the dataset
        df = load_data(is_national)

        if df is not None:
            # Split the dataset and apply necessary transformation to prepare data for the training
            X_train, X_test, y_train, y_test = create_X_y(
                df, test_size=test_size, random_state=random_state
            )

            X_train_preproc = predicteng.preprocess_data(X_train, train=True)
            X_test_preproc = predicteng.preprocess_data(X_test, train=False)

            predicteng.create_model()

            predicteng.train_model(X_train=X_train_preproc, y_train=y_train)
            predicteng.evaluate_model(X_test=X_test_preproc, y_test=y_test)


if __name__ == "__main__":
    # train(True)
    train(False)

    # with MlFlowLogger("national_model") as mlogger:
