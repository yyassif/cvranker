import os
import requests
from logger import get_logger
from pydantic import BaseModel
from typing import Dict, Optional, Type

from langchain_core.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.pydantic_v1 import BaseModel as BaseModelV1
from langchain_core.pydantic_v1 import Field as FieldV1
from langchain_core.tools import BaseTool

logger = get_logger(__name__)


class WebSearchInput(BaseModelV1):
    """Input schema for the web search tool."""
    query: str = FieldV1(..., title="query", description="Search query to look up")


class WebSearchTool(BaseTool):
    name = "brave-web-search"
    description = "Useful for when you need to search the web for something."
    args_schema: Type[BaseModel] = WebSearchInput # type: ignore
    api_key: str = os.getenv("BRAVE_SEARCH_API_KEY", "")

    def _check_environment_variable(self) -> bool:
        """Check if the environment variable is set."""

        return os.getenv("BRAVE_SEARCH_API_KEY") is not None

    def __init__(self):
        if not self._check_environment_variable():
            raise ValueError("BRAVE_SEARCH_API_KEY environment variable is not set")
        super().__init__() # type: ignore

    def _run( # type: ignore
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict:
        """Run the tool."""
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key,
        }
        response = requests.get(
            f"https://api.search.brave.com/res/v1/web/search?q={query}&count=3",
            headers=headers,
        )
        return self._parse_response(response.json()) # type: ignore

    async def _arun( # type: ignore
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> Dict:
        """Run the tool asynchronously."""
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key,
        }
        response = requests.get(
            f"https://api.search.brave.com/res/v1/web/search?q={query}&count=3",
            headers=headers,
        )
        return self._parse_response(response.json()) # type: ignore

    def _parse_response(self, response: Dict) -> str:
        """Parse the response."""
        short_results = []
        results = response["web"]["results"]
        for result in results:
            title = result["title"]
            url = result["url"]
            description = result["description"]
            short_results.append(self._format_result(title, description, url))
        return "\n".join(short_results)

    def _format_result(self, title: str, description: str, url: str) -> str:
        return f"**{title}**\n{description}\n{url}"
    

if __name__ == "__main__":
    tool = WebSearchTool()
    print(tool.run("python"))