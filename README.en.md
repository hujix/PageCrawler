# PageCrawler

<div align="center">
    <a href="README.md">¼òÌåÖÐÎÄ</a> | <a href="README.en.md">English</a>
</div>

## Overview

`PageCrawler` aims to provide an efficient page extraction service. By inputting a URL, you can obtain the key content
of the webpage.

It uses three methods: `aiohttp`, `playwright`, and `pyppeteer` to obtain page content.

## Installation and Running

Install dependencies

```shell
pip install -r requirements.txt
```

Run the project

```shell
uvicorn main:app --host 0.0.0.0 --port 8899
```

> **About --reload**
>
> Due to some irresistible factors, when running the project with the command
>
> `uvicorn main:app --host 0.0.0.0 --port 8899 --reload`
>
> An exception will occur in playwright: raise NotImplementedError

## Usage

```shell
curl --location 'http://localhost:8899/extract' \
--header 'Content-Type: application/json' \
--data '{
    "url": "https://wap.peopleapp.com/article/7318277/7155177",
    "adapters": [
        "playwright"
    ]
}'
```

The parameter adapters defaults to `['request']`, which means direct requests are made using `aiohttp`. When multiple
adapters are passed, or one with the longest content is chosen for the return.

The available adapter parameters are: `request`, `playwright`, `pyppeteer`.

## Project Structure

```text
PageCrawler
©¦  .gitignore
©¦  LICENSE
©¦  logger.py
©¦  main.py
©¦  models.py
©¦  README.md
©¦  README.en.md
©¦  requirements.txt
©¦          
©À©¤crawler                           # Crawler module
©¦  ©¦  abstract_crawler_adapter.py   # Crawler adapter abstract module 
©¦  ©¦  models.py
©¦  ©¦  page_crawler.py               # Crawler adapter initialization and orchestration call
©¦  ©¦  utils.py
©¦  ©¦  __init__.py
©¦  ©¦  
©¦  ©À©¤adapter                        # Specific crawler adapter module
©¦  ©¦  ©¦  playwright_adapter.py
©¦  ©¦  ©¦  pyppeteer_adapter.py
©¦  ©¦  ©¦  request_adapter.py
©¸©¤©¤©¸©¤©¤©¸©¤ __init__.py
```

## About Second Creation

If there are no special or explicit requirements, only the `crawl_page` method in `crawler/page_crawler.py` needs to be
modified or expanded.

Here, you can implement the orchestration and invocation of different types of crawlers.

For the direct request using `aiohttp`, or the rendering method using the two browsers, the author has tested a large
number of URLs, and currently, the speed is considered optimal in most cases.

## Q&A

### Q: Why Choose Two Browser Rendering Frameworks?

When it comes to rendering some commonly used web pages, `playwright` has a significantly better average speed
than `pyppeteer`. However, there is a downside; on the network level, `playwright` does not offer the same fine-grained
control over page rendering return as `pyppeteer` does:

| Granularity      | Description                                                                      | playwright | pyppeteer |
|------------------|----------------------------------------------------------------------------------|:----------:|:---------:|
| commit           | When a network response is received and the document begins to load.             |     ?      |     ?     |
| domcontentloaded | When the "DOMContentLoaded" event is fired.                                      |     ?      |     ?     |
| load             | When the "load" event is fired.                                                  |     ?      |     ?     |
| networkidle      | When there has been no network activity for at least 500 milliseconds.           |     ?      |     ?     |
| networkidle0     | When there are fewer than 0 network connections for at least 500 milliseconds.   |     ?      |     ?     |
| networkidle2     | When there are no more than 2 network connections for at least 500 milliseconds. |     ?      |     ?     |

While rendering pages, `playwright` can capture the majority of the page content. However, it may fail to retrieve
content from pages that require sending `http` requests, resulting in an empty `html` structure.

In such cases, `pyppeteer` can be employed for rendering. With the `networkidle2` control granularity, it can
effectively capture these types of websites.

## ? Good Luck~

<div align="center">
 <img src="https://www.emojiall.com/en/header-svg/%F0%9F%8E%89.svg" width="300" alt="?">
</div>

