from __future__ import annotations


from typing import Type

from pydantic import BaseModel, Field

from langchain.tools.playwright.base import BaseBrowserTool
from langchain.tools.playwright.utils import aget_current_page, get_current_page, awrite_to_file, awrite_fail_to_file

from playwright.async_api import TimeoutError as PlaywrightTimeoutError


class ClickByTextToolInput(BaseModel):
    """Input for ClickByTextTool."""

    selector: str = Field(..., description="Selector for the element by text content.")
    text: str = Field(..., description="Text content of the element to click on.")
    index: int = Field(0, description="Index of the element to click on.")
    timeout: float = Field(3_000, description="Timeout (in ms) for Playwright to wait for element to be ready.")


class ClickByTextTool(BaseBrowserTool):
    """Tool for clicking on an element with the given text and selector."""

    name: str = "click_by_text"
    description: str = "Click on element in the current web page matching the text content"
    args_schema: Type[BaseModel] = ClickByTextToolInput

    visible_only: bool = True
    """Whether to consider only visible elements."""
    playwright_strict: bool = False
    """Whether to employ Playwright's strict mode when clicking on elements."""

    def _selector_effective(self, selector: str, index: int, text: str) -> str:
        if not self.visible_only:
            return f"page.getByRole('{selector}').getByText('{text}')"
        return f"page.getByRole('{selector}').getByText('{text}').nth({index})"

    def _text_effective(self, index: int, text: str) -> str:
        if not self.visible_only:
            return f"page.getByText({text})"
        return f"page.getByText('{text}').nth({index})"

    def _run(
        self,
        selector: str,
        text: str,
        timeout: float = 3_000
    ) -> str:
        """Use the tool."""
        if self.sync_browser is None:
            raise ValueError(f"Synchronous browser not provided to {self.name}")
        # Navigate to the desired webpage before using this tool
        page = get_current_page(self.sync_browser)
        playwright_cmd = None

        try:
            el = page.get_by_role(selector).get_by_text(text)
            # check if element is visible via selector and text
            if el.is_visible():
                el.click(timeout=self.timeout)
                # write playwright command to temp file
                playwright_cmd = f"    page.getByRole('{selector}').getByText('{text}').click({{timeout: {timeout}}});\n"
                with open('tempfile', 'a') as f:
                    f.write(playwright_cmd)
            else:
                # if not visible, try to click on element only by text
                page.get_by_text(text).click(timeout=self.timeout)
                # write playwright command to temp file
                playwright_cmd = f"    page.getByText('{text}').click({{timeout: {timeout}}});\n"
                with open('tempfile', 'a') as f:
                    f.write(playwright_cmd)
        except Exception as e:
            try:
                # if there are more than one element with the same text, click on the first one
                page.click(f"{selector}:has-text('{text}')", strict=False, timeout=self.timeout)
                # write playwright command to temp file
                playwright_cmd = f"    page.click(\"{selector}:has-text('{text}'), {{timeout:{timeout}}}\");\n"
                with open('tempfile', 'a') as f:
                    f.write(playwright_cmd)
            except PlaywrightTimeoutError as e2:
                with open('tempfile', 'a') as f:
                    f.write(f"    // FAIL - click_by_text: selector - '{selector} ; text: '{text}'\n")
                return f"Unable to click on element with selector: '{selector}' text:'{text}'with exception: {e2}"
        return (f"Click on the element with selector: '{selector}' text: '{text}', was successfully performed")

    async def _arun(
        self,
        selector: str,
        text: str,
        index: int = 0,
        timeout: float = 3_000

    ) -> str:
        """Use the tool."""
        if self.async_browser is None:
            raise ValueError(f"Asynchronous browser not provided to {self.name}")

        try:
            # Navigate to the desired webpage before using this tool
            page = await aget_current_page(self.async_browser)
            playwright_cmd = None
            el = page.get_by_role(selector).get_by_text(text)
            # check if element is visible via selector and text
            if await el.nth(index).is_visible():
                selector_effective = self._selector_effective(selector=selector, index=index, text=text)
                await el.nth(index).click(timeout=timeout)
                # write playwright command to temp file
                playwright_cmd = f"await {selector_effective}.click({{strict:{str(self.playwright_strict).lower()}, timeout:{timeout}}});\n"
                await awrite_to_file(msg=f'    {playwright_cmd}')
            else:
                # if not visible, try to click on element only by text
                text_effective = self._text_effective(text=text, index=index)
                await page.get_by_text(text).click(timeout=timeout)
                # write playwright command to temp file
                playwright_cmd = f"await {text_effective}.click({{strict:{str(self.playwright_strict).lower()}, timeout:{timeout}}});\n"
                await awrite_to_file(msg=f'    {playwright_cmd}')
        except Exception:
                return f"Unable to click on element with selector: '{selector}', index: '{index}' text:'{text}'"
        return f"Click on the element with selector: '{selector}', index: '{index}' text: '{text}', was successfully performed"
