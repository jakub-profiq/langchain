from __future__ import annotations

from typing import Optional, Type

from pydantic import BaseModel, Field

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.tools.playwright.base import BaseBrowserTool
from langchain.tools.playwright.utils import aget_current_page, get_current_page


class TakeScreenshotToolInput(BaseModel):
    """Input for TakeScreenshotTool."""

    path: str = Field(..., description="Path to save the screenshot to.")


class TakeScreenshotTool(BaseBrowserTool):
    name: str = "take_screenshot"
    description: str = "Take a screenshot of the current page"
    args_schema: Type[BaseModel] = TakeScreenshotToolInput

    def _run(
        self,
        path: str,
    ) -> str:
        """Use the tool."""
        if self.async_browser is None:
            raise ValueError(f"Synchronous browser not provided to {self.name}")
        page = aget_current_page(self.async_browser)
        try:
            page.screenshot(path=path)
        except Exception as e:
            return f"Unable to take screenshot with exception: {e}"
        return "Screenshot taken"

    async def _arun(
        self,
        path: str,
    ) -> str:
        """Use the tool."""
        if self.async_browser is None:
            raise ValueError(f"Asynchronous browser not provided to {self.name}")
        page = await aget_current_page(self.async_browser)
        try:
            await page.screenshot(path=path)
        except Exception as e:
            return f"Unable to take screenshot with exception: {e}"
        return "Screenshot taken"
