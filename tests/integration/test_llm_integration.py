"""
Integration tests for Gemini LLM client — retry logic and model fallback.
All actual API calls are mocked.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from google.genai.errors import APIError




class TestGeminiGenerate:
    def _mock_stream_response(self, response_dict):
        """Create a mock that simulates generate_content_stream yielding chunks."""
        chunk = MagicMock()
        chunk.text = json.dumps(response_dict)
        return [chunk]

    def _valid_response(self):
        return {
            "domains_to_block": [{"domain": "tracker.com", "reason": "Tracking", "confidence": "HIGH"}],
            "domains_to_unblock": [],
            "domains_to_test": [],
            "analysis_summary": "Test summary",
        }

    @patch("src.gemini.init.genai.Client")
    def test_successful_generation(self, MockClient):
        from src.gemini.init import generate

        mock_client = MockClient.return_value
        mock_client.models.generate_content_stream.return_value = self._mock_stream_response(
            self._valid_response()
        )

        result = generate('{"Allowed": [], "Blocked": []}')
        assert "domains_to_block" in result
        assert "analysis_summary" in result

    @patch("src.gemini.init.genai.Client")
    def test_returns_error_when_all_models_fail(self, MockClient):
        from src.gemini.init import generate

        mock_client = MockClient.return_value
        mock_client.models.generate_content_stream.side_effect = APIError(
            code=429, response_json={"error": {"message": "Rate limited"}}
        )

        result = generate('{"Allowed": [], "Blocked": []}')
        assert "error" in result




class TestGeminiRetryLogic:
    @patch("src.gemini.init.time.sleep")  # Skip actual waiting
    @patch("src.gemini.init.genai.Client")
    def test_retries_on_429_then_succeeds(self, MockClient, mock_sleep):
        from src.gemini.init import generate

        valid_response = {
            "domains_to_block": [],
            "domains_to_unblock": [],
            "domains_to_test": [],
            "analysis_summary": "OK",
        }
        chunk = MagicMock()
        chunk.text = json.dumps(valid_response)

        mock_client = MockClient.return_value
        # First call: 429, second call: success
        mock_client.models.generate_content_stream.side_effect = [
            APIError(code=429, response_json={"error": {"message": "Rate limited"}}),
            [chunk],
        ]

        result = generate('{"Allowed": [], "Blocked": []}')
        assert "analysis_summary" in result
        assert result["analysis_summary"] == "OK"

    @patch("src.gemini.init.time.sleep")
    @patch("src.gemini.init.genai.Client")
    def test_switches_model_after_exhausting_retries(self, MockClient, mock_sleep):
        from src.gemini.init import generate

        valid_response = {
            "domains_to_block": [],
            "domains_to_unblock": [],
            "domains_to_test": [],
            "analysis_summary": "Fallback OK",
        }
        chunk = MagicMock()
        chunk.text = json.dumps(valid_response)

        mock_client = MockClient.return_value

        with patch("src.gemini.init.settings") as mock_settings:
            mock_settings.GEMINI_MODELS_NAME = ["model-a", "model-b"]
            mock_settings.GEMINI_API_KEY = "test-key"

            # model-a: both attempts fail with 429
            # model-b: first attempt succeeds
            mock_client.models.generate_content_stream.side_effect = [
                APIError(code=429, response_json={"error": {"message": "Rate limited"}}),
                APIError(code=429, response_json={"error": {"message": "Rate limited"}}),
                [chunk],
            ]

            result = generate('{"Allowed": [], "Blocked": []}')
            assert result["analysis_summary"] == "Fallback OK"




class TestGeminiPromptInjection:
    @patch("src.gemini.init.genai.Client")
    def test_user_prompt_included_in_system_instruction(self, MockClient):
        from src.gemini.init import generate

        valid_response = {
            "domains_to_block": [],
            "domains_to_unblock": [],
            "domains_to_test": [],
            "analysis_summary": "With user prompt",
        }
        chunk = MagicMock()
        chunk.text = json.dumps(valid_response)

        mock_client = MockClient.return_value
        mock_client.models.generate_content_stream.return_value = [chunk]

        result = generate('{"Allowed": []}', user_prompt="Block all Microsoft telemetry")
        assert "analysis_summary" in result

        # Verify the system instruction contained user prompt
        call_kwargs = mock_client.models.generate_content_stream.call_args
        config = call_kwargs.kwargs.get("config") or call_kwargs[1].get("config")
        system_text = config.system_instruction[0].text
        assert "Block all Microsoft telemetry" in system_text

    @patch("src.gemini.init.genai.Client")
    def test_empty_user_prompt_excluded(self, MockClient):
        from src.gemini.init import generate

        valid_response = {
            "domains_to_block": [],
            "domains_to_unblock": [],
            "domains_to_test": [],
            "analysis_summary": "No user prompt",
        }
        chunk = MagicMock()
        chunk.text = json.dumps(valid_response)

        mock_client = MockClient.return_value
        mock_client.models.generate_content_stream.return_value = [chunk]

        result = generate('{"Allowed": []}', user_prompt="")
        
        call_kwargs = mock_client.models.generate_content_stream.call_args
        config = call_kwargs.kwargs.get("config") or call_kwargs[1].get("config")
        system_text = config.system_instruction[0].text
        assert "USER PREFERENCES" not in system_text
