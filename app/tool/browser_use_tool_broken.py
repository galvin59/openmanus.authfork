import asyncio
import base64
import json
import logging
import os
import re
from pathlib import Path
from typing import Generic, Optional, TypeVar, Dict, Any, List

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from app.secure_credentials import credential_manager
from app.tool.base import BaseTool, ToolResult
from app.config import config

logger = logging.getLogger(__name__)


class BrowserUseTool(BaseTool):
    """A tool for browser automation with persistent cookies."""
    
    name: str = "browser_use"
    description: str = """A web browser tool that can navigate to URLs, interact with elements, 
    and persist cookies between sessions for maintaining logins."""
    
    def __init__(self):
        super().__init__()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.cookies_file: Path = Path.home() / ".openmanus" / "browser_data" / "cookies.json"
        self.user_data_dir: Path = Path.home() / ".openmanus" / "browser_data"
        self.lock = asyncio.Lock()
    
    def _ensure_data_dir(self) -> None:
        """Ensure the user data directory exists."""
        self.user_data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    
    async def _save_cookies(self) -> None:
        """Save cookies to a file."""
        if not self.context:
            return
            
        try:
            cookies = await self.context.cookies()
            if cookies:
                self._ensure_data_dir()
                with open(self.cookies_file, 'w') as f:
                    json.dump(cookies, f, indent=2)
                logger.info(f"Saved {len(cookies)} cookies to {self.cookies_file}")
        except Exception as e:
            logger.error(f"Error saving cookies: {e}")
    
    async def _load_cookies(self) -> None:
        """Load cookies from file if it exists."""
        if not self.context or not self.cookies_file.exists():
            return
            
        try:
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
                if cookies:
                    await self.context.add_cookies(cookies)
                    logger.info(f"Loaded {len(cookies)} cookies from {self.cookies_file}")
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
    
    async def _ensure_browser(self) -> None:
        """Ensure the browser is initialized."""
        if self.browser:
            return
            
        self._ensure_data_dir()
        
        # Get browser configuration from config
        browser_config = {
            'headless': getattr(config.browser, 'headless', False),
            'args': getattr(config.browser, 'extra_chromium_args', [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ])
        }
        
        logger.info(f"Launching browser with config: {browser_config}")
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.user_data_dir),
            headless=browser_config['headless'],
            args=browser_config['args'],
            viewport={'width': 1280, 'height': 1024}
        )
        
        # Get the first page or create a new one
        pages = self.browser.pages
        self.page = pages[0] if pages else await self.browser.new_page()
        
        # Load saved cookies
        await self._load_cookies()
    
    async def execute(
        self,
        action: str,
        url: Optional[str] = None,
        index: Optional[int] = None,
        text: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """Execute a browser action."""
        async with self.lock:
            try:
                await self._ensure_browser()
                if not self.page:
                    return ToolResult(error="Page not initialized")
                
                if action == "go_to_url" and url:
                    # Replace secure credentials in URL if any
                    processed_url = self._replace_secure_credentials(url)
                    if processed_url != url:
                        logger.info("Identifiants sécurisés détectés et remplacés dans l'URL")
                    
                    await self.page.goto(processed_url, wait_until="networkidle")
                    domain = processed_url.split('//')[-1].split('/')[0]
                    return ToolResult(output=f"Navigated to {domain}")
                
                elif action == "click_element" and index is not None:
                    elements = await self.page.query_selector_all('*')
                    if 0 <= index < len(elements):
                        await elements[index].click()
                        return ToolResult(output=f"Clicked element at index {index}")
                    return ToolResult(error=f"Element index {index} out of range")
                
                elif action == "input_text" and index is not None and text is not None:
                    # Replace secure credentials in text if any
                    processed_text = self._replace_secure_credentials(text)
                    if processed_text != text:
                        logger.info("Identifiants sécurisés détectés et remplacés")
                    
                    elements = await self.page.query_selector_all('input, textarea')
                    if 0 <= index < len(elements):
                        await elements[index].fill(processed_text)
                        masked_text = "*" * 8 if processed_text != text and "#" in text else processed_text
                        return ToolResult(
                            output=f"Entered text into element at index {index}: {masked_text}",
                            masked_output=f"Entered text into element at index {index} (contenu masqué pour des raisons de sécurité)"
                        )
                    return ToolResult(error=f"Input element index {index} out of range")
                
                return ToolResult(error=f"Unknown action: {action}")
                
            except Exception as e:
                logger.error(f"Browser action '{action}' failed: {e}", exc_info=True)
                return ToolResult(error=str(e))
    
    def _replace_secure_credentials(self, text: str) -> str:
        """Replace secure credential placeholders with actual values."""
        if not text or not isinstance(text, str):
            return text
            
        def replace_match(match):
            service, key = match.groups()
            value = credential_manager.get_credential(service, key)
            if value is None:
                logger.warning(f"Identifiant non trouvé: {service}.{key}")
                return match.group(0)
            return value
            
        return re.sub(r'#(\w+)_(\w+)#', replace_match, text)
    
    async def cleanup(self) -> None:
        """Clean up browser resources and save cookies."""
        try:
            if self.page:
                await self._save_cookies()
            
            if self.browser:
                await self.browser.close()
                logger.info("Browser closed successfully")
                
        except Exception as e:
            logger.error(f"Error during browser cleanup: {e}")
        finally:
            self.page = None
            self.context = None
            self.browser = None
    
    def __del__(self):
        """Ensure cleanup when the object is destroyed."""
        if self.browser:
            try:
                asyncio.get_event_loop().run_until_complete(self.cleanup())
            except RuntimeError:
                # If there's no event loop, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.cleanup())
                loop.close()
