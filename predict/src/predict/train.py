from predict import get_logger
from predict.model import Energypredict
from predict.mllogs import MlFlowLogger
from predict.data import (
    connect_to_bigquery,
    load_data,
    create_X_y,
    build_input_national,
    build_input_region,
)
import sys


def train(
    bqclient,
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


def predict_conso(
    bqclient, is_national: bool = True, code_insee_region: int = 0
) -> float | None:
    if is_national:
        savename = "national_model"
    else:
        savename = "region_model"

    with MlFlowLogger(savename) as mlogger:
        predicteng = Energypredict(mlogger)

        df = load_data(bqclient, is_national, False)

        if df is None:
            return None

        if is_national:
            df_to_evaluate = build_input_national(df)
        else:
            df_to_evaluate = build_input_region(df, code_insee=code_insee_region)

        pred_conso = None
        if df_to_evaluate is not None:
            X_test_preproc = predicteng.preprocess_data(df_to_evaluate, train=False)
            pred_conso = predicteng.predict(X_test_preproc)

        return pred_conso

    return None


if __name__ == "__main__":
    bqclient = connect_to_bigquery()
    if bqclient is None:
        get_logger().error(
            "Impossible to reach the Datawarehouse for computing prediction"
        )
        sys.exit(1)

    # train(bqclient, True)
    # train(bqclient, False)

    pred_nat = predict_conso(bqclient)
    pred_reg_idf = predict_conso(bqclient, False, 11)

    get_logger().info(
        f"Consommation nationale estimée: {pred_nat} - Consommation région IdF estimée {pred_reg_idf}"
    )
