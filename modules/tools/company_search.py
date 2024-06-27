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


class CompanySearchInput(BaseModelV1):
    """Input schema for the company search tool."""
    query: str = FieldV1(..., title="query", description="Search query to look up")


class CompanySearchTool(BaseTool):
    name = "company-search"
    description = "Useful for when you need to search the companies for something."
    args_schema: Type[BaseModel] = CompanySearchInput # type: ignore

    def __init__(self):
        super().__init__() # type: ignore

    def _run( # type: ignore
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict:
        """Run the tool."""
        response = requests.get(
            f"https://api.recherche-entreprises.fabrique.social.gouv.fr/api/v1/search?query={query}&limit=10&ranked=true&matchingLimit=10"
        )
        
        return self._parse_response(response.json()) # type: ignore

    async def _arun( # type: ignore
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> Dict:
        """Run the tool asynchronously."""
        response = requests.get(
            f"https://api.recherche-entreprises.fabrique.social.gouv.fr/api/v1/search?query={query}&limit=10&ranked=true&matchingLimit=10"
        )
        return self._parse_response(response.json()) # type: ignore

    def _parse_response(self, response: Dict) -> str:
        """Parse the response."""
        short_results = []
        results = response["entreprises"]
        for result in results:
            label = result["label"]
            simpleLabel = result["simpleLabel"]
            activitePrincipale = result["activitePrincipale"]
            short_results.append(self._format_result(label, simpleLabel, activitePrincipale))
        return "\n".join(short_results)

    def _format_result(self, title: str, description: str, url: str) -> str:
        return f"**{title}**\n{description}\n{url}"
    

if __name__ == "__main__":
    tool = CompanySearchTool()
    print(tool.run("python"))