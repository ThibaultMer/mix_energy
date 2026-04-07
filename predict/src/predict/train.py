from predict.model import Energypredict
from predict.mllogs import MlFlowLogger
from predict.data import connect_to_bigquery, load_data, create_X_y


def train(
    is_national: bool = True,
    test_size: float = 0.2,
    random_state: int = 42,
) -> None:
    """
    Train a model

    Params
    ------
    is_national : Do we train for National values ? or Region values ?
    test_size: used to split the dataset between the values to use for training and the ones for testing
    random_state: used for the dataset split function
    """

    if is_national:
        savename = "national_model"
    else:
        savename = "region_model"

    with MlFlowLogger(savename) as mlogger:
        predicteng = Energypredict(mlogger)

        # Import the dataset
        bqclient = connect_to_bigquery()
        if bqclient is not None:
            df = load_data(bqclient, is_national)

        if df is not None:
            # Split the dataset and apply necessary transformation to prepare data for the training
            X_train, X_test, y_train, y_test = create_X_y(
                df, test_size=test_size, random_state=random_state
            )

            # Prepare data for the training
            X_train_preproc = predicteng.preprocess_data(X_train, train=True)
            X_test_preproc = predicteng.preprocess_data(X_test, train=False)

            predicteng.create_model()

            # Train the model
            predicteng.train_model(X_train=X_train_preproc, y_train=y_train)

            # Evaluate the model
            predicteng.evaluate_model(X_test=X_test_preproc, y_test=y_test)


# def predict_conso(bqclient, is_national: bool = True) -> float | None:
#     if is_national:
#         savename = "national_model"
#     else:
#         savename = "region_model"

#     with MlFlowLogger(savename) as mlogger:
#         predicteng = Energypredict(mlogger)

#         df = load_data(bqclient, is_national, False)

#         if df is None:
#             return None


if __name__ == "__main__":
    train(True)
    train(False)

    # with MlFlowLogger("national_model") as mlogger:
