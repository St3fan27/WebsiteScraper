from playwright.async_api import Playwright, Browser
from bs4 import BeautifulSoup
import os
import json
import re
import pandas as pd

class TechAnalyzer:
    
    def __init__(self, folder="technologies"):
        self.results = {}
        self.browser: Browser | None = None
        self.tech_data = {}
        self.invalid_regex = []

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
        detected = set()
        soup = BeautifulSoup(html, 'html.parser')

        headers_low = {k.lower(): str(v) for k, v in headers.items()}
        scripts = [script.get('src') for script in soup.find_all('script') if script.get('src')]
        meta_tags = {}
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                meta_tags[name.lower()] = content

        for tech_name, rules in self.tech_data.items():

            if "html" in rules:
                html_rules = rules["html"]
                
                if isinstance(html_rules, str):
                    html_rules = [html_rules]

                for rule in html_rules:
                    rule_copy = rule.split('\\;')[0]

                    try:
                        if re.search(rule_copy, html, re.IGNORECASE):
                            detected.add(tech_name)
                            break
                    except re.error:
                        self.invalid_regex.append(f"{index} {rule_copy}")
            
            if "scriptSrc" in rules:
                script_rules = rules["scriptSrc"]
                if isinstance(script_rules, str):
                    script_rules = [script_rules]
                
                for rule in script_rules:
                    rule_copy = rule.split('\\;')[0]
                    for src in scripts:
                        try:
                            if re.search(rule_copy, src, re.IGNORECASE):
                                detected.add(tech_name)
                                break
                        except re.error:
                            self.invalid_regex.append(f"{index} {rule_copy}")

            if "meta" in rules:
                for meta, meta_r in rules["meta"].items():
                    meta_copy = meta.lower()
                    
                    if meta_copy in meta_tags:
                        if isinstance(meta_r, list):
                            meta_r = meta_r[0] 
                            
                        rule_copy = meta_r.split('\\;')[0]
                        try:
                            if re.search(rule_copy, meta_tags[meta_copy], re.IGNORECASE):
                                detected.add(tech_name)
                        except re.error:
                            self.invalid_regex.append(f"{index} {rule_copy}")
            
            if "headers" in rules:
                for header, header_r in rules["headers"].items():
                    header_copy = header.lower()
                    
                    if header_copy in headers_low:
                        rule_copy = header_r.split('\\;')[0]
                        try:
                            if re.search(rule_copy, headers_low[header_copy], re.IGNORECASE):
                                detected.add(tech_name)
                        except re.error:
                            self.invalid_regex.append(f"{index} {rule_copy}")

        detected_list = list(detected)
        print(f"{index} {len(detected_list)} tech")

        return detected_list
    
    def export_data(self, file = "tech_results.parquet", error_f = "regex_errors.txt"): 
        
        if not self.results:
            print("No technologies")
            return

        techs = set()

        data = []
        for url, technologies in self.results.items():
            techs.update(technologies)
            data.append({
                "url": url,
                "technologies": technologies,
                "tech_count": len(technologies)
            })

        df = pd.DataFrame(data)
        print(f"Unique tech: {len(techs)}")
        df.to_parquet(file, engine="pyarrow", index=False)
                        
        if self.invalid_regex:
            
            with open(error_f, "w", encoding="utf-8") as f:
                f.write(f"Total regex errors: {len(self.invalid_regex)}\n")
                f.write("-" * 50 + "\n")
                for error in self.invalid_regex:
                    f.write(f"{error}\n")
                    
    async def close_browser(self):
        if self.browser:
           await self.browser.close()