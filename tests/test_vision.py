import pytest

from models import FoodAnalysis
from vision import VisionError, analyze_image


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeModels:
    def __init__(self, responses=None, error=None):
        self.responses = responses or []
        self.error = error
        self.calls = 0

    def generate_content(self, **kwargs):
        self.calls += 1

        if self.error is not None:
            raise self.error

        return FakeResponse(
            self.responses[self.calls - 1]
        )


class FakeClient:
    def __init__(self, responses=None, error=None):
        self.models = FakeModels(
            responses=responses,
            error=error,
        )


def valid_json():
    return """
    {
        "items": [
            {
                "name": "Pirinç pilavı",
                "grams": 200,
                "confidence": 0.95
            }
        ],
        "notes": "Test analizi"
    }
    """


def test_valid_response_returns_food_analysis():
    client = FakeClient(
        responses=[valid_json()]
    )

    result = analyze_image(
        image="fake-image",
        client=client,
    )

    assert isinstance(result, FoodAnalysis)
    assert len(result.items) == 1
    assert result.items[0].name == "Pirinç pilavı"
    assert result.items[0].grams == 200
    assert result.items[0].confidence == 0.95
    assert client.models.calls == 1


def test_invalid_first_response_retries_and_succeeds():
    client = FakeClient(
        responses=[
            "bu geçerli bir JSON değil",
            valid_json(),
        ]
    )

    result = analyze_image(
        image="fake-image",
        client=client,
    )

    assert isinstance(result, FoodAnalysis)
    assert result.items[0].name == "Pirinç pilavı"
    assert client.models.calls == 2


def test_two_invalid_responses_raise_vision_error():
    client = FakeClient(
        responses=[
            "geçersiz cevap 1",
            "geçersiz cevap 2",
        ]
    )

    with pytest.raises(VisionError):
        analyze_image(
            image="fake-image",
            client=client,
        )

    assert client.models.calls == 2


def test_api_error_is_converted_to_vision_error():
    client = FakeClient(
        error=RuntimeError("API bağlantı hatası")
    )

    with pytest.raises(VisionError):
        analyze_image(
            image="fake-image",
            client=client,
        )

    assert client.models.calls == 1