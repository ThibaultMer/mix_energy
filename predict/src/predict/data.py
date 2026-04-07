import os
import pandas as pd
from sklearn.model_selection import train_test_split

import google.cloud.bigquery as bigquery
import google.oauth2.service_account as service_account

from predict import get_logger

from datetime import datetime, timedelta


BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "TEST_DBT_GOLD")

QUERIES = {
    "region": (
        "reg_tr_predi",
        "code_insee_region,day,month,hour,minute,,consommation,prev_conso_mean,prev_conso_mean_h,prev_conso_mean_m ",
    ),
    "national": (
        "nat_tr_predi",
        "day,month,hour,minute,consommation,prevision_j1,prevision_j",
    ),
}


def connect_to_bigquery() -> bigquery.Client | None:
    # Create the credential used to authenticate

    json_credential_file = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS",
        os.path.join(
            os.path.dirname(__file__), "data/meteo/mix-energie-gcp-23501901f9c9.json"
        ),
    )
    project_id = os.getenv("PROJECT_ID")

    if not os.path.exists(json_credential_file):
        get_logger().error(
            f"Fichier de credentials introuvable : {json_credential_file}"
        )
        return None

    credentials = service_account.Credentials.from_service_account_file(
        json_credential_file
    )

    get_logger().info("Connection to the project ")

    try:
        client = bigquery.Client(project=project_id, credentials=credentials)
    except Exception as e:
        get_logger().error("Fail to connect to project {} : {}".format(project_id, e))
        return None

    return client


def load_data(
    client: bigquery.Client, is_national: bool = True, is_all: bool = True
) -> pd.DataFrame:
    """
    Loads data from the Gold table stored in BIGQUERY_DATASET

    Params
    ------
    is_national : Retrieve data from the National ? (default True). Otherwise, it will use the by Region dataset

    Return
    ------
    A DataFrame loaded with the data from the specified dataset
    None if an error occured
    """

    if is_national:
        query_data = QUERIES["national"]
    else:
        query_data = QUERIES["region"]

    if is_all:
        query = (
            f"select {query_data[1]} FROM {BIGQUERY_DATASET}.{query_data[0]}"
            " WHERE consommation is not NULL ORDER BY date_heure ASC"
        )
    else:
        current_dt = datetime.now() - timedelta(days=30)

        compare_dt = current_dt.strftime("%Y-%m-%d 00:00:00")

        query = (
            f"select {query_data[1]},date_heure, COUNT(1) as total_count FROM {BIGQUERY_DATASET}.{query_data[0]} "
            f"WHERE consommation is not NULL AND date_heure>='{compare_dt}' "
            "ORDER BY date_heure DESC"
        )

    try:
        df = client.query_and_wait(query).to_dataframe()
    except Exception as e:
        get_logger().error(
            f"Fail to retrieve data from {BIGQUERY_DATASET}.{query[0]}: {e}"
        )
        get_logger().debug("The query tested : {query}")
        return None

    return df


# def build_input_national(df: pd.DataFrame):
#     index = df["date_heure"].idxmax()

#     df.iloc(index)

#     current_dt = datetime.now()

#     # The prediction is done for the next 15 minutes

#     if current_dt.minute > 45:
#         # If it is 15:47, the prediction will be done for 16:00
#         # If it is 23:47, the prediction will be done the day following at 00:00
#         current_dt = current_dt + timedelta(hours=1)
#         minute = current_dt.minute
#     else:
#         # If it is 14:13, we will perform a prediction for 14:15
#         minute = int(current_dt.minute / 15) * 15 + 15

#     values = [current_dt.day, current_dt.month, current_dt.hour, minute, 0, 0, 0]

#     input_values = dict(zip(QUERIES["national"][1], values))


# def build_input_region(df: pd.DataFrame, code_insee: int):
#     index = df["date_heure"].idxmax()


def create_X_y(
    df: pd.DataFrame,
    test_size: float,
    random_state: int,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Create the feature matrix X and target vector y from the diamonds dataset.

    Parameters
    ----------
    df : pd.DataFrame
        The preprocessed diamonds dataset

    Returns
    -------
    (pd.DataFrame, pd.Series)
        The feature matrix X and target vector y
    """
    df.dropna()
    source_data = df.drop(columns=["consommation"])
    source_data.dropna()
    to_predict = df["consommation"]
    to_predict.dropna()

    X_train, X_test, y_train, y_test = train_test_split(
        source_data, to_predict, test_size=test_size, random_state=random_state
    )

    return X_train, X_test, y_train, y_test
