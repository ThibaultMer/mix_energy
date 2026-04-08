import os
import pandas as pd
from sklearn.model_selection import train_test_split
from enum import IntEnum, StrEnum, auto

import google.cloud.bigquery as bigquery
import google.oauth2.service_account as service_account

from predict import get_logger

from datetime import datetime, timedelta


BIGQUERY_DATASET = os.getenv("DATASET_ID_PROD", "prod_mix_energie")


class ZoneEnum(StrEnum):
    REGION = auto()
    NATIONAL = auto()


class ZoneDictEnum(IntEnum):
    TABLE_ENTRY = (0,)
    FIELD_LIST = 1


QUERIES = {
    "region": (
        "reg_tr_predi",
        "code_insee_region,day,month,hour,minute,consommation,prev_conso_mean,prev_conso_mean_h,prev_conso_mean_m",
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
        query_data = QUERIES[ZoneEnum.NATIONAL]
    else:
        query_data = QUERIES[ZoneEnum.REGION]

    table_name = f"{BIGQUERY_DATASET}_gold.{query_data[ZoneDictEnum.TABLE_ENTRY]}"

    if is_all:
        query = (
            f"select {query_data[ZoneDictEnum.FIELD_LIST]} FROM {table_name}"
            " WHERE consommation is not NULL ORDER BY year ASC, month ASC, day ASC, hour ASC, minute ASC"
        )
    else:
        current_dt = datetime.now()

        """
        We want to retrieve the last 30 days (as we cannot minus by one month with timedelta)
        But if we proceed like that, the start_dt.day > current_dt.day
        Moreover it is possible that in the database, the current day is not available yet =>
        we must consider to take the day before
        """

        start_dt = current_dt - timedelta(days=30)
        start_dt = datetime(
            year=current_dt.year,
            month=current_dt.month,
            day=min(current_dt.day, start_dt.day),
        )

        start_dt = start_dt - timedelta(days=1)

        if current_dt.hour == 0:
            start_dt = start_dt - timedelta(days=1)

        query = (
            f"select {query_data[ZoneDictEnum.FIELD_LIST]},year FROM {table_name} "
            f"WHERE consommation is not NULL AND year >={start_dt.year} AND month >={start_dt.month} "
            f"AND day >= {start_dt.day}  "
            "ORDER BY year DESC, month DESC, day DESC, hour DESC, minute DESC"
        )

    try:
        df = client.query_and_wait(query).to_dataframe()
    except Exception as e:
        get_logger().error(f"Fail to retrieve data from {table_name}: {e}")
        get_logger().debug(f"The query tested : {query}")
        return None

    if not is_all:
        query = f"SELECT COUNT(*) as total_count FROM {table_name}"
        try:
            result = client.query_and_wait(query).to_dataframe()
        except Exception as e:
            get_logger().error(f"Fail to retrieve nb rows from {table_name}: {e}")
            get_logger().debug(f"The query tested : {query}")
            return None

        nb_entries = result["total_count"].iloc[0]

        get_logger().debug(f"Nb entries in the table {table_name} : {nb_entries}")

        df["total_count"] = nb_entries

    return df


def __compute_current_datetime():
    current_dt = datetime.now().astimezone()

    # The prediction is done for the next 15 minutes

    if current_dt.minute > 45:
        # If it is 15:47, the prediction will be done for 16:00
        # If it is 23:47, the prediction will be done the day following at 00:00
        current_dt = current_dt - timedelta(minutes=current_dt.minute)
        current_dt = current_dt + timedelta(hours=1)
    else:
        # If it is 14:13, we will perform a prediction for 14:15
        if current_dt.minute % 15 != 0:
            minute = int(current_dt.minute / 15) * 15 + 15
        else:
            minute = current_dt.minute
        current_dt = datetime(
            year=current_dt.year,
            month=current_dt.month,
            day=current_dt.day,
            hour=current_dt.hour,
            minute=minute,
        )

    get_logger().debug("Computed date time : {}".format(current_dt))

    return current_dt


def build_input_national(df: pd.DataFrame):
    # index = df["date_heure"].idxmax()

    current_dt = __compute_current_datetime()

    last_conso = df["consommation"].iloc[0]

    # For the prevision at day minus 1, we use the consumption of the day before
    day_before = current_dt - timedelta(days=1)

    date_cond = (
        (df.year == day_before.year)
        & (df.month == day_before.month)
        & (df.day == day_before.day)
        & (df.hour == day_before.hour)
        & (df.minute == day_before.minute)
    )

    df_res = df[date_cond]["consommation"]
    if df_res.count() == 0:
        date_cond = (
            (df.year == day_before.year)
            & (df.month == day_before.month)
            & (df.day == day_before.day)
        )

        df_res = df[date_cond]["consommation"]

    if df_res.count() == 0:
        get_logger().error(
            "No data to perform the prediction for {}".format(current_dt)
        )
        return None

    prevision_j1 = df_res.values[0]

    values = [
        current_dt.day,
        current_dt.month,
        current_dt.hour,
        current_dt.minute,
        0,
        prevision_j1,
        last_conso,
    ]

    keys = QUERIES[ZoneEnum.NATIONAL][ZoneDictEnum.FIELD_LIST].split(sep=",")

    dict_eval = dict(zip(keys, values))

    df_to_eval = pd.DataFrame(dict_eval, index=[0], dtype="int")

    return df_to_eval


def build_input_region(df: pd.DataFrame, code_insee: int):
    # Compute prev_conso_mean
    # mean_t = ((mean_t1*nb_entry_t1)+current_conso)/nb_entry_t

    prev_conso_mean_t1 = df["prev_conso_mean"].iloc[0]
    nb_entry_t = df["total_count"].iloc[0]
    nb_entry_t1 = nb_entry_t - 1
    prev_conso_mean = (
        (prev_conso_mean_t1 * nb_entry_t1) + df["consommation"].iloc[0]
    ) / nb_entry_t

    # Compute prev_conso_mean_h
    current_dt = __compute_current_datetime()
    prev_hour_dt = current_dt - timedelta(hours=1)

    cond_date = (
        (df.month == prev_hour_dt.month)
        & (df.day == prev_hour_dt.day)
        & (df.hour >= prev_hour_dt.hour)
    )

    last_hour_val = df[cond_date]
    prev_conso_mean_h = (
        last_hour_val["consommation"].sum() / last_hour_val["consommation"].count()
    )

    # Compute prev_conso_mean_m
    # As the dataframe was built selecting the last 30 days, it is easy to compute this value
    prev_conso_mean_m = df["consommation"].sum() / df["consommation"].count()

    # "code_insee_region,day,month,hour,minute,,consommation,prev_conso_mean,prev_conso_mean_h,prev_conso_mean_m "
    values = [
        code_insee,
        current_dt.day,
        current_dt.month,
        current_dt.hour,
        current_dt.minute,
        0,
        prev_conso_mean,
        prev_conso_mean_h,
        prev_conso_mean_m,
    ]

    keys = QUERIES[ZoneEnum.REGION][ZoneDictEnum.FIELD_LIST].split(sep=",")

    dict_eval = dict(zip(keys, values))

    df_to_eval = pd.DataFrame(dict_eval, index=[0])

    return df_to_eval


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
