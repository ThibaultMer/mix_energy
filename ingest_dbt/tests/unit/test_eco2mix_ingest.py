from mix_energy import eco2mix_ingest as eco2mix


class FakeResponse:
    def __init__(self, status_code, headers=None, content=b"", json_data=None):
        self.status_code = status_code
        self.headers = headers or {}
        self.content = content
        self._json_data = json_data or {}

    def json(self):
        return self._json_data


def test_perform_request_429_errorcode_returns_empty_dict(monkeypatch):
    def fake_get(url, params=None):
        return FakeResponse(
            status_code=429,
            headers={"content-type": "application/json"},
            json_data={
                "errorcode": "429",
                "error": "rate limit",
                "call_limit": 100,
                "limit_time_unit": "hour",
            },
        )

    monkeypatch.setattr(eco2mix.requests, "get", fake_get)

    result = eco2mix.__perform_request("https://example.com", params={"foo": "bar"})
    assert result == {}


def test_retrieve_csv_success_returns_content(monkeypatch):
    expected_content = b"col1;col2\n1;2\n"

    def fake_get(url, params=None):
        return FakeResponse(
            status_code=200,
            headers={"content-type": "text/csv; charset=utf-8"},
            content=expected_content,
        )

    monkeypatch.setattr(eco2mix.requests, "get", fake_get)

    actual_content = eco2mix.retrieve_csv("my-dataset")
    assert actual_content == expected_content


def test_retrieve_csv_non_csv_content_type_returns_none(monkeypatch):
    def fake_get(url, params=None):
        return FakeResponse(
            status_code=200,
            headers={"content-type": "application/json"},
            content=b"{}",
        )

    monkeypatch.setattr(eco2mix.requests, "get", fake_get)

    assert eco2mix.retrieve_csv("my-dataset") is None


def test_select_data_from_dataset_success_with_json_response(monkeypatch):
    results = [{"a": 1}, {"a": 2}]

    def fake_get(url, params=None):
        assert params["order_by"] == "date desc"
        assert params["limit"] == "100"
        return FakeResponse(
            status_code=200,
            headers={"content-type": "application/json; charset=utf-8"},
            json_data={"total_count": 2, "results": results},
        )

    monkeypatch.setattr(eco2mix.requests, "get", fake_get)

    actual = eco2mix.select_data_from_dataset(
        "my-dataset", field_list=["a"], where="a>0"
    )
    assert actual == results


def test_select_data_from_dataset_non_json_content_type_returns_none(monkeypatch):
    def fake_get(url, params=None):
        return FakeResponse(
            status_code=200,
            headers={"content-type": "text/plain"},
            json_data={"total_count": 0, "results": []},
        )

    monkeypatch.setattr(eco2mix.requests, "get", fake_get)

    assert eco2mix.select_data_from_dataset("my-dataset") is None
