import os
import requests
import loguru
import pandas as pd

logger = loguru.logger

base_url = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/"


def __perform_request(req_url: str, params: dict):
    result = requests.get(req_url, params=params)
    match result.status_code:
        case 200:
            logger.info(
                "Successful connection to {} to retrieve CSV file   ".format(base_url)
            )

        case 400:
            logger.error("Bad request {} with params {}".format(req_url, params))
            json_res = result.json()
            logger.error(json_res["message"])

        case 401:
            logger.error(
                "Unauthorized  access to {} with params {}".format(req_url, params)
            )

        case 429:
            json_res = result.json()
            if "errorcode" in json_res:
                logger.error(
                    "Errorcode : {} - {}, limit :{} / {} ".format(
                        json_res["errorcode"],
                        json_res["error"],
                        json_res["call_limit"],
                        json_res["limit_time_unit"],
                    )
                )
            return {}
        case 500:
            logger.error("Internal Server error")

        case _:
            logger.error("HTTP error : {}".format(result.status_code))

    return result


def retrieve_csv(
    dataset_id: str,
    delimiter: str = ";",
    list_sep: str = ",",
    quote_all: bool = False,
    with_bom: bool = True,
):
    """
        Retrieves the CSV file of a specific dataset

    Parameters
    ----------

    dataset_id: Dataset identifier (name of the dataset to retrieve),
    delimiter:  Specify the field delimiter character (default = ';')
    list_sep:   Specify list separator (default = ",")
    quote_all:  All field quoted (default False)
    with_bom:   default True

    Return
    ------
    The content of the CSV file if success
    None otherwises

    """

    req_url = base_url + dataset_id + "/exports/csv"

    params = {
        "delimiter": delimiter,
        "list_separator": list_sep,
        "quote_all": quote_all,
        "with_bom": with_bom,
    }

    result = __perform_request(req_url=req_url, params=params)

    if result.status_code == 200:
        if (
            "content-type" in result.headers
            and result.headers["content-type"].split(";")[0] == "text/csv"
        ):
            logger.info("CSV file of the dataset {} retrieved", dataset_id)
            return result.content
        else:
            logger.error(
                "Unexpected data received : {}".format(result.headers["content-type"])
            )
    else:
        return None


def select_data_from_dataset(dataset_id: str, field_list: list = (), where: str = ""):
    req_url = base_url + dataset_id + "/records"
    params = {"order_by": "date desc", "limit": "100"}

    if len(where):
        params["where"] = where

    if len(field_list):
        params["select"] = field_list

    response = __perform_request(req_url=req_url, params=params)

    if response.status_code == 200:
        if response.headers.get("content-type").count("json") != 0:
            result = response.json()
            logger.info("Retrieve total count : {}".format(result["total_count"]))
            return result["results"]
        else:
            logger.error(
                "Unexpected data received : {}".format(result.headers["content-type"])
            )
    else:
        return None


if __name__ == "__main__":
    dataset_list = (
        "eco2mix-national-tr",
        "eco2mix-national-cons-def",
        "eco2mix-regional-tr",
        "eco2mix-regional-cons-def",
    )

    result = retrieve_csv(dataset_id="eco2mix-national-tr")
    if result is not None:
        with open("temp_csv.txt", "wb") as csvfile:
            csvfile.write(result)

        df = pd.read_csv("temp_csv.txt", delimiter=";")

        os.remove("temp_csv.txt")
        print(df.head(5))
    else:
        print("Ouiiiin! CA MARCHE PAS !!!!!!!!")

    for dataset in dataset_list:
        result = select_data_from_dataset(dataset)
        if result is not None:
            df = pd.DataFrame(result)
            print("The 5 first element of the dataset {}".format(dataset))
            print(df.head(5))
