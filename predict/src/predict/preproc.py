from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer, make_column_selector
from sklearn.impute import KNNImputer
from sklearn.preprocessing import StandardScaler


def build_pipeline() -> Pipeline:
    num_pipe = Pipeline(
        [("knn_imp", KNNImputer(n_neighbors=5)), ("scaler", StandardScaler())]
    )

    preprocessor = ColumnTransformer(
        [("numeric", num_pipe, make_column_selector(dtype_include="number"))]
    ).set_output(transform="pandas")

    return preprocessor
