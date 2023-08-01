from __future__ import annotations


from typing import Type

from pydantic import BaseModel, Field

from langchain.tools.playwright.base import BaseBrowserTool
from langchain.tools.playwright.utils import aget_current_page, get_current_page

class ClickByTextToolInput(BaseModel):
    """Input for ClickByTextTool."""
    selector: str = Field(..., description="Selector for the element by text content.")
    text: str = Field(..., description="Text content of the element to click on.")


class ClickByTextTool(BaseBrowserTool):
    name: str = "click_by_text"
    description: str = "Click on element in the current web page matching the text content"
    args_schema: Type[BaseModel] = ClickByTextToolInput

    visible_only: bool = True
    """Whether to consider only visible elements."""
    playwright_strict: bool = False
    """Whether to employ Playwright's strict mode when clicking on elements."""
    playwright_timeout: float = 1_000
    """Timeout (in ms) for Playwright to wait for element to be ready."""

    def _run(
        self,
        selector: str,
        text: str,
    ) -> str:
        """Use the tool."""
        if self.sync_browser is None:
            raise ValueError(f"Synchronous browser not provided to {self.name}")
        # Navigate to the desired webpage before using this tool
        page = get_current_page(self.sync_browser)

        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

        try:
            el = page.get_by_role(selector).get_by_text(text)
            # check if element is visible via selector and text
            if el.is_visible():
                el.click(timeout=self.playwright_timeout)
            else:
                # if not visible, try to click on element only by text
                page.get_by_text(text).click(timeout=self.playwright_timeout)
        except Exception as e:
            try:
                # if there are more than one element with the same text, click on the first one
                page.click(f"{selector}:has-text('{text}')",strict=False)
            except PlaywrightTimeoutError:
                return f"Unable to click on element '{text}' with exception: {e}"
        return "Click on the element by text", text ,"was successfully performed"

    async def _arun(
        self,
        selector: str,
        text: str,
    ) -> str:
        """Use the tool."""
        if self.async_browser is None:
            raise ValueError(f"Asynchronous browser not provided to {self.name}")
        # Navigate to the desired webpage before using this tool
        page = await aget_current_page(self.async_browser)
        playwright_cmd = None

        from playwright.async_api import TimeoutError as PlaywrightTimeoutError
        try:
            el = page.get_by_role(selector).get_by_text(text)
            # check if element is visible via selector and text
            if await el.is_visible():
                await el.click(timeout=self.playwright_timeout)
                # write playwright command to temp file
                playwright_cmd = f"    await page.getByRole('{selector}').getByText('{text}').click();\n"
                with open('tempfile', 'a') as f:
                    f.write(playwright_cmd)
            else:
                # if not visible, try to click on element only by text
                await page.get_by_text(text).click(timeout=self.playwright_timeout)
                # write playwright command to temp file
                playwright_cmd = f"    await page.getByText('{text}').click();\n"
                with open('tempfile', 'a') as f:
                    f.write(playwright_cmd)
        except Exception as e:
            try:
                # if there are more than one element with the same text, click on the first one
                await page.click(f"{selector}:has-text('{text}')", strict=False)
                # write playwright command to temp file
                playwright_cmd = f"    await page.click(\"{selector}:has-text('{text}')\");\n"
                with open('tempfile', 'a') as f:
                    f.write(playwright_cmd)
            except PlaywrightTimeoutError as e2:
                return f"Unable to click on element with selector: '{selector}' text:'{text}'with exception: {e2}"
        return (f"Click on the element with selector: '{selector}' text: '{text}', was successfully performed")