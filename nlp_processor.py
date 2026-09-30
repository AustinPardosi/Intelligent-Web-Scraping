import os
import json
import requests
from typing import Dict, Optional, Any

class NLPProcessor:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the NLP Processor that turns natural language into scraping parameters

        Args:
            api_key: OpenAI API key. If None, falls back to the OPENAI_API_KEY env variable
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Pass it as a parameter or set the OPENAI_API_KEY env variable")

        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4.1-mini"

    def parse_command(self, query: str) -> Dict[str, Any]:
        """
        Convert a natural language query into scraping parameters

        Args:
            query: Command in natural language

        Returns:
            Dictionary with scraping parameters (state, member, breed)
        """
        system_prompt = """
        You are an assistant that converts natural language commands into parameters for web scraping the AMGR Directory website.

        Your task is to extract the following parameters from the user's command:
        - state: a US state (e.g. Kansas, Texas)
        - member: member/breeder name (e.g. Dwight Elmore, Smith)
        - breed: breed type (e.g. American Red, Ameri-Kiko)

        The result must be JSON with the parameters: state, member, breed.
        If a parameter is not mentioned in the command, use null.

        Examples:
        Command: "Find breeders in Texas"
        Output: {"state": "Texas", "member": null, "breed": null}

        Command: "Show all breeders named Smith in Kansas"
        Output: {"state": "Kansas", "member": "Smith", "breed": null}

        Command: "Find American Red breeders in Alabama"
        Output: {"state": "Alabama", "member": null, "breed": "American Red"}
        """

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            "temperature": 0.2,  # Low value for consistency
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

            # Take the response text and parse it as JSON
            response_text = result["choices"][0]["message"]["content"]

            # Parse directly if it's already JSON
            try:
                parsed_params = json.loads(response_text)
            except json.JSONDecodeError:
                # Otherwise, try to extract the JSON part from the text
                import re
                json_match = re.search(r'{.*}', response_text, re.DOTALL)
                if json_match:
                    parsed_params = json.loads(json_match.group(0))
                else:
                    raise ValueError(f"Could not extract JSON from response: {response_text}")

            return parsed_params

        except requests.exceptions.RequestException as e:
            print(f"Error contacting the OpenAI API: {e}")
            return {"state": None, "member": None, "breed": None}
        except Exception as e:
            print(f"Error processing the response: {e}")
            return {"state": None, "member": None, "breed": None}

    def get_api_usage(self) -> Dict[str, Any]:
        """Get API usage info"""
        # Simple implementation that shows usage info
        return {
            "model": self.model,
            "status": "active"
        }


if __name__ == "__main__":
    # Simple demo for testing
    import sys

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter a search command: ")

    try:
        processor = NLPProcessor()
        result = processor.parse_command(query)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except ValueError as e:
        print(f"Error: {e}")
        print("Make sure the API key is set correctly")
