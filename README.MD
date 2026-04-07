Project Overview:
This project is a high-performance, asynchronous web analyzer built with Python, Playwright, and BeautifulSoup. It identifies the technology stack of websites using Wappalyzer rules, with a specialized engine designed for high data accuracy and low false-positive rates.
Total Unique Technologies Detected: 369 
Certain (Verified): 353
Proof is derived from multi-vector verification: if a technology is found in the window object or a specific secure_cookie, it constitutes technical proof of active residency, not just a textual reference.
Possible (Unverified): 16

Development Journey & Technical Challenges:
The current implementation is the result of an iterative process where I solved real-world scraping obstacles. Below is the chronological order of the challenges I faced and how I tackled them:
1. Custom Engine vs. Pre-built Tools: While using a library like the official Wappalyzer package would have been easier, I chose to build the logic from scratch. This allowed me to deeply understand the underlying regex engine, manage custom rule merging and I created two separate categories for the results.
2. Optimization for Speed & Script Execution: The primary challenge was balancing the need for JavaScript execution with the requirement for high-speed scanning. I implemented Network Resource Interception to block images, CSS, and media files. This optimization reduced average page load times from ~10 seconds to under 1 second per site while still allowing essential technology-detecting scripts to run.
3. Handling Domain-Specific Blocks: Certain domains, such as bas-ingenieria.cl, initially returned errors or blocked access. I resolved this by implementing a modern User-Agent string (Chrome/120.0.0.0), which allowed the scraper to bypass basic anti-bot filters that were flagging default Playwright headers.
4. Browser Engine Trade-offs (WebKit vs. Chromium): I experimented with Chromium to utilize the system-level --mute-audio flag. However, Chromium was consistently detected and blocked by more sites compared to WebKit. I made the strategic decision to revert to WebKit for its superior "stealth" capabilities.
5. Expanding Detection Scope: My initial prototype only detected 204 technologies by looking at the static HTML. By iterating and expanding the search vectors to include HTTP Headers, Cookies, and Global JS variables (window object), I successfully increased the detection count to 369 unique technologies.
6. Data Integrity & Confidence Scoring: To ensure the final dataset was clean, I implemented Confidence Scoring. I created separate categories for Certain (verified technical usage) and Possible (textual mentions in HTML). This distinction is crucial for filtering out "mentions" versus "actual implementation."

Scaling for Millions of Domains:
1. Framework Optimization (Scrapy & Splash): I would transition the crawling logic to Scrapy, the industry-standard framework for high-throughput scraping. For JavaScript-heavy sites, I would integrate Splash or a headless browser cluster (Playwright/Puppeteer) as a middleware, using it only when necessary to optimize CPU and RAM consumption across millions of requests.
2. Data Storage (Data Lake vs. Databases): Instead of saving to local Parquet files, I would implement a Data Lake (e.g., AWS S3 or Google Cloud Storage) for long-term storage of raw HTML. For real-time querying and indexing of the detected technologies, I would use a distributed database like Elasticsearch or PostgreSQL with partitioning.
3. Cloud Scalability: Utilizing Cloud Services is essential for horizontal scaling. By deploying the analyzer on AWS Lambda (serverless) or Kubernetes (EKS/GKE), we can spin up thousands of concurrent workers across different geographical regions. This not only speeds up the process but also helps in distributing traffic to avoid IP-based blocking.

Discovering New Technologies in the Future:
1. LLM Assisted Signature Generation: I would use Large Language Models (LLMs) to analyze unidentified or "unknown" source code fragments. The LLM can automatically suggest and generate new Regex signatures and rules by recognizing code patterns associated with emerging frameworks.
2. Community Data Integration: I would set up automated pipelines to sync with open-source communities and databases (such as the Wappalyzer GitHub repository or BuiltWith). By contributing to and pulling from these datasets, the analyzer remains aligned with global technology trends.

Key Features:
- Asynchronous Engine: Leverages asyncio and Playwright's WebKit for high-concurrency parallel processing.
- Confidence Scoring: Implements a dual-category detection logic:
- Certain: Technologies confirmed via technical evidence (HTTP Headers, Cookies, Script Sources, or Global JS variables).
- Possible: Technologies identified only through raw HTML pattern matching (filtering out mere mentions).
- Dynamic JS Analysis: Executes JavaScript to inspect the window object, capturing libraries that don't leave traces in the static DOM.
- Performance Optimized: Blocks non-essential resources (images, CSS, fonts) to reduce bandwidth and CPU usage.

Getting Started:
1. Installation
First, clone the repository and navigate to the project folder. Then, install the required dependencies using the requirements.txt file:
```bash
pip install -r requirements.txt
```
2. Browser Setup
This project uses Playwright with the WebKit engine for better stealth and performance. You need to install the browser binaries after installing the Python package:
```bash
playwright install webkit
```

Usage:
1. Input Data
Ensure your input Parquet file is in the root directory. By default, the script looks for:
part-00000-66e0628d-2c7f-425a-8f5b-738bcd6bf198-c000.snappy.parquet

If your file has a different name, update the input_file variable in main.py.

2. Running the Analysis
To start the asynchronous scanning process, execute the main script:
```bash
python main.py
```

3. Viewing Results
After the scan completes, a new file named tech_results.parquet will be generated.
The results are split into two categories to ensure data integrity:
Certain: High-confidence detections verified via HTTP headers, scripts, cookies, or JS variables.
Possible: Low-confidence detections found only as text patterns in the raw HTML.

4. Error Handling
- links_error.txt: Logs domains that were unreachable via both HTTPS and HTTP.
- regex_errors.txt: Logs any invalid regex patterns found in the technology rule sets for future maintenance.