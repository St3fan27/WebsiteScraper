import asyncio
from playwright.async_api import async_playwright, Playwright, Browser
from bs4 import BeautifulSoup
import os
import json
import re

class TechAnalyzer:
    
    def __init__(self, domains, folder="technologies"):
        self.domains = domains
        self.results = {}
        self.browser: Browser | None = None
        self.tech_data = {}

        for file in os.listdir(folder):
            if file.endswith(".json"):
                with open(f"{folder}/{file}", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tech_data.update(data)

    async def start_browser(self, p: Playwright):
        self.webkit = p.webkit
        self.browser = await self.webkit.launch()

    async def run_page(self, semaphore, page_url, index):
        async with semaphore:
            # I have defined the protocols that need to be tried
            protocols = ["https://", "http://"]
            context = None
            # I use try to not stop scanning other sites if browser/system errors occur
            try:
                # I used a user_agent to hide the fact that the script is a bot
                context = await self.browser.new_context(ignore_https_errors=True, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                page = await context.new_page()
                # I didn't load images, css and media to increase speed
                await page.route("**/*", lambda route: route.abort() 
                                 if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
                                 else route.continue_())

                ok = False
                for protocol in protocols:
                    url = f"{protocol}{page_url}"
                    print(f"{index} Scanning: {url}")
                    # I use try to avoid stopping the entire script when a site goes down
                    try:
                        # I wait 30 seconds to see if the site works if not we throw an error
                        response = await page.goto(url, timeout=30000)
                        # I wait for JavaScript to load
                        await page.wait_for_timeout(2000)

                        html_content = await page.content()
                        if response.headers:
                            headers = response.headers
                        else:
                            headers = {}

                        tech = self.extract_tech(html_content, headers, index)
                        self.results[url] = tech

                        print(f"{index} Ok")
                        ok = True
                        break

                    except Exception as e:
                        print(f"{index} Error: {e}")
                
                # I write down the sites that couldn't run
                if not ok:
                    print(f"{index}, {url} Error ")
                    with open("links_error.txt", "a", encoding="utf-8") as f:
                        f.write(f"{page_url} No protocol succeeded\n")

            # Error in case there is not enough ram or there is a problem with Playwright
            except Exception as e:
                print(f"{index}, {page_url} System Error : {e}")
                with open("links_error.txt", "a", encoding="utf-8") as f:
                    f.write(f"{page_url} Playwright Error\n")

            finally:
                if context:
                    await context.close()

    def extract_tech(self, html, headers, index):
        detected = []
        soup = BeautifulSoup(html, 'html.parser')

        for tech_name, rules in self.tech_data.items():

            if "html" in rules:
                html_rules = rules["html"]
                
                if isinstance(html_rules, str):
                    html_rules = [html_rules]

                for rule in html_rules:
                    rule_copy = rule.split('\\;')[0]

                    try:
                        if re.search(rule_copy, html, re.IGNORECASE):
                            detected.append(tech_name)
                            break
                    except re.error:
                        pass
        
        print(f"{index} {len(detected)} number of tech")

    async def close_browser(self):
        if self.browser:
           await self.browser.close()