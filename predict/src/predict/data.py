import pandas as pd
from sklearn.model_selection import train_test_split


def create_X_y(
    df: pd.DataFrame, test_size, random_state
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
    source_data = {}
    to_predict = {}

    X_train, X_test, y_train, y_test = train_test_split(
        source_data, to_predict, test_size=test_size, random_state=random_state
    )

    return X_train, X_test, y_train, y_test
