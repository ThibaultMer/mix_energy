import os
import google.cloud.storage as storage
import google.oauth2.service_account as service_account
from . import get_logger


# -----------------------------------------------------------------------------------------
def connect_to_bucket() -> storage.Bucket:
    """
    Connect to GCP bucket using the JSON KEY file of a specified service account

    Returns
    -------
    the shared bucket if success
    None otherwise
    """

    # Create the credential used to authenticate
    json_credential_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    project_id = os.getenv("PROJECT_ID")

    credentials = service_account.Credentials.from_service_account_file(
        json_credential_file
    )

    get_logger().info("Connection to the project ")

    try:
        client = storage.Client(project=project_id, credentials=credentials)
    except Exception as e:
        get_logger().error("Fail to connect to project {} : {}".format(project_id, e))
        return None

    try:
        bucket = client.get_bucket("mix-energie-bucket")
    except Exception as e:
        get_logger().error(
            "Fail to retrieve bucket 'mix-energie-bucket' in project {} : {}".format(
                project_id, e
            )
        )
        return None

    return bucket


# -----------------------------------------------------------------------------------------
def upload_data_in_bucket(bucket, data, dataset):
    """
    Upload data from a dataset onto a bucket

    Parameters
    ----------
    bucket: bucket instance used to load data in
    data: the data to load
    dataset: the name of the dataset the data is coming from

    """

    get_logger().info("Load data on the bucket : {}".format(dataset))
    blob = bucket.blob(dataset + ".csv")
    blob.upload_from_string(data)
