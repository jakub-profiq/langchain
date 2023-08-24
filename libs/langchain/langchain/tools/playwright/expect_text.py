from __future__ import annotations

from typing import Type

from pydantic import BaseModel, Field

from langchain.tools.playwright.base import BaseBrowserTool
from langchain.tools.playwright.utils import aget_current_page, get_current_page
from langchain.tools.playwright.utils import aget_current_page, get_current_page
from playwright.sync_api import expect as syncExpect
from playwright.async_api import expect as asyncExpect


class ExpectTextToolInput(BaseModel):
    """Input for ExpectTextTool."""

    text: str = Field(
        ...,
        description="Text what you expect to see.",
    )


class ExpectTextTool(BaseBrowserTool):
    """Tool for checking expected text."""

    name: str = "expect_text"
    description: str = "Check if expected text is the same as the text of the current web page."
    args_schema: Type[BaseModel] = ExpectTextToolInput

    def _run(
        self,
        text: str,
    ) -> str:
        """Use the tool."""
        if self.sync_browser is None:
            raise ValueError(f"Synchronous browser not provided to {self.name}")
        page = get_current_page(self.sync_browser)
        # check if the text is the same as expected
        try:
            element = page.get_by_text(text).first;
            syncExpect(element).to_have_text(text)
            playwrite_command = f"    expect(page.getByText(/{text}/)).toHaveText(/{text}/);\n"
            with open('tempfile', 'a') as f:
                f.write(playwrite_command)
        except Exception as e:
            with open('tempfile', 'a') as f:
                f.write(f"    // FAIL - expect().toHaveText('{text}')\n")
            return f"Cannot to find '{text}' with exception: {e}"

        return "Text: ", text, "is visible on the current page."

    async def _arun(
        self,
        text: str,
    ) -> str:
        """Use the tool."""
        if self.async_browser is None:
            raise ValueError(f"Asynchronous browser not provided to {self.name}")
        page = await aget_current_page(self.async_browser)
        # check if the text is the same as expected
        try:
            element = page.get_by_text(text).first;
            await asyncExpect(element).to_have_text(text)
            playwrite_command = f"    await expect(page.getByText(/{text}/)).toHaveText(/{text}/);\n"
            with open('tempfile', 'a') as f:
                f.write(playwrite_command)
        except Exception as e:
            with open('tempfile', 'a') as f:
                f.write(f"    // FAIL - expect().toHaveText('{text}')\n")
            return f"Cannot to find '{text}' with exception: {e}"

        return "Text: ", text, "is visible on the current page."