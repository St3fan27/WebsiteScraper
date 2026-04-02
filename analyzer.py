import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

class TechAnalyzer:
    
    def __init__(self, domains):
        self.domains = domains
        
        