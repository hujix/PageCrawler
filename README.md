# PageExtractor: 页面提取服务

## 概述

`PageExtractor`旨在提供高效的页面提取服务。通过输入URL，可以获得网页的关键内容。

通过使用`aiohttp`、`playwright`、`pyppeteer`三种方式进行页面内容的获取。

## 安装运行

安装依赖

```shell
pip install -r requirements.txt
```

运行项目

```shell
uvicorn main:app --host 0.0.0.0 --port 8899
```

> **关于 --reload**
>
> 由于某种不可抗力的影响，当使用命令
>
> `uvicorn main:app --host 0.0.0.0 --port 8899 --reload`
>
> 运行项目时，`playwright`的运行会出现异常：`raise NotImplementedError`

## 请求调用

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

参数`adapters`默认为`['request']`，即使用`aiohttp`进行直接的请求。 当传入多个`adapter`时，或选择一个内容最长的结果进行返回。

`adapter`的可选参数为：`request`、`playwright`、`pyppeteer`。

## 项目结构

```text
PageExtractor
│  .gitignore
│  LICENSE
│  logger.py
│  main.py
│  models.py
│  README.md
│  requirements.txt
│          
├─crawler                           # 爬虫模块
│  │  abstract_crawler_adapter.py   # 爬虫适配器抽象模块 
│  │  models.py
│  │  page_crawler.py               # 爬虫适配器初始化以及编排调用
│  │  utils.py
│  │  __init__.py
│  │  
│  ├─adapter                        # 具体的爬虫适配器模块
│  │  │  playwright_adapter.py
│  │  │  pyppeteer_adapter.py
│  │  │  request_adapter.py
└──└──└─ __init__.py
```

## 关于二创

如若没有特殊的、明确的需求，只需要对`crawler/page_crawler.py`中的`crawl_page`方法进行修改或拓展。

在这里可以实现对不同类型的爬虫进行编排与调用。

对于使用`aiohttp`的直接请求，或者是使用两种浏览器的渲染方式，作者已经经过了大量的`URL`进行测试，目前算是确定了在大多数的情况下，速度达到了最优。

## Q&A

### Q: 为什么选择两种浏览器渲染框架？

在一些常用网页的渲染下，`playwright`的平均速度明显比`pyppeteer`的速度要好的多，但是有一个问题就是，在网络层面，`playwright`
没有`pyppeteer`对页面渲染返回控制的粒度细：

| 粒度               | 描述                       | playwright | pyppeteer |
|------------------|--------------------------|:----------:|:---------:|
| commit           | 在收到网络响应并开始加载文档时。         |     ✅      |     ❌     |
| domcontentloaded | 触发“DOMContentLoaded”事件时。 |     ✅      |     ✅     |
| load             | 触发“load”事件时              |     ✅      |     ✅     |
| networkidle      | 当至少“500”毫秒没有网络连接时。       |     ✅      |     ❌     |
| networkidle0     | 当至少 500 毫秒的网络连接不超过 0 时。  |     ❌      |     ✅     |
| networkidle2     | 当至少 500 毫秒的网络连接不超过 2 个时。 |     ❌      |     ✅     |

在页面渲染时`playwright`能够获取绝大部分的页面内容，但是获取不到页面需要发送如`http`
请求的网站，所以会导致，获取到的只是一个空内容的`html`的结构。

这个时候就可以使用`pyppeteer`来进行渲染，使用`networkidle2`的控制粒度，可以很好地获取到这类的网站。

## 🎉 祝好运~

<div align="center">
 <img src="https://www.emojiall.com/en/header-svg/%F0%9F%8E%89.svg" width="300" alt="🎉">
</div>

