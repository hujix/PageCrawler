import type { LimitFunction } from "p-limit";
import type { Browser, BrowserContext, Page, Request, Route } from "playwright";

import pLimit from "p-limit";
import { chromium } from "playwright";
import { BaseCrawler } from "../crawler-service";
import type { CrawlerResult, PlaywrightOptions } from "../types";
import logger from "../lib/logger";
import { expandShadowRoots } from "../lib/utils";

interface PlaywrightInstance {
  browser: Browser;
  context: BrowserContext;
  limit: LimitFunction;
}

class PlaywrightService extends BaseCrawler {
  private instances: PlaywrightInstance[] = [];
  private options: PlaywrightOptions = {
    timeout: 5000,
    concurrent: 5,
    headless: true,
    instance: 1,
  };

  private index = 0;

  constructor(options: PlaywrightOptions) {
    super();
    this.options = { ...this.options, ...options };
  }

  async initialize(): Promise<void> {
    if (this.instances.length < this.options.instance) {
      for (let i = 0; i < this.options.instance; i++) {
        const browser = await chromium.launch({
          headless: true,
          ignoreDefaultArgs: ["--mute-audio"],
        });
        const context = await browser.newContext({
          ignoreHTTPSErrors: true,
          bypassCSP: true,
        });
        const limit = pLimit(this.options.concurrent);

        this.instances.push({ browser, context, limit });
      }
    }
  }

  async close(): Promise<void> {
    if (this.instances.length === 0) {
      for (const { browser, context, limit } of this.instances) {
        await browser.close();
        await context.close();
        limit.clearQueue();
      }
    }
  }

  async _intercept(route: Route, resuest: Request): Promise<void> {
    const url = resuest.url();

    for (const suffix of ["adsbygoogle.js", ".css", ".woff", ".pdf", ".zip"]) {
      if (url.toLocaleLowerCase().includes(suffix)) {
        await route.abort();
        return;
      }
    }

    for (const suffix of [".jpg", ".jpeg", ".png", ".svg", ".gif"]) {
      if (resuest.url().toLocaleLowerCase().includes(suffix)) {
        await route.fulfill({
          body: "",
          contentType: "image/png",
          status: 200,
        });
        return;
      }
    }

    const resourceType = resuest.resourceType() as string;
    if (resourceType === "image") {
      await route.fulfill({
        body: "",
        contentType: "image/png",
        status: 200,
      });
      return;
    }

    if (
      [
        "stylesheet",
        "media",
        "texttrack",
        "object",
        "beacon",
        "csp_report",
        "imageset",
      ].includes(resourceType)
    ) {
      await route.abort();
    }
    else {
      await route.continue();
    }
  }

  async checkContent(page: Page) {
    let content: string | null;
    try {
      content = await page.evaluate(() => {
        const content = document.documentElement.textContent;
        return content;
      });
    }
    catch (error) {
      logger.error(`Error getting page content : ${error}`);
      return false;
    }
    if (content === null) {
      return false;
    }

    return content.length > 100;
  }

  async _pageWaitUntil(page: Page): Promise<void> {
    try {
      let interval: NodeJS.Timeout | undefined;
      await Promise.race([
        new Promise((resolve, _reject) => {
          interval = setInterval(async () => {
            const check = await this.checkContent(page!);
            if (check) {
              clearInterval(interval);
              resolve(true);
            }
          }, 500);
        }),
        new Promise((resolve, _reject) => {
          setTimeout(() => {
            clearInterval(interval);
            resolve(false);
          }, this.options.timeout);
        }),
      ]);
    }
    catch (error) {
      logger.error(`Error checking content : ${error}`);
    }
  }

  async crawl(url: string): Promise<CrawlerResult> {
    const idx = this.index % this.instances.length;
    this.index++;
    const { context, limit } = this.instances[idx];

    return limit(async () => {
      // 1. create a new page
      const page = await context.newPage();
      // 2. set default timeout
      page.setDefaultTimeout(this.options.timeout);
      page.setDefaultNavigationTimeout(this.options.timeout);
      // 3. set request interceptor
      await page.route("**/*", this._intercept);

      try {
        await page.goto(url, { waitUntil: "domcontentloaded", timeout: this.options.timeout });
        // 4. wait until content is loaded
        await this._pageWaitUntil(page);
        // 5. get content from shadow dom or document
        const content = await page.evaluate(() => {
          return expandShadowRoots.toString();
        });

        const html = content || (await page?.content()) || "";

        return {
          html,
          reason: "",
        };
      }
      catch (error) {
        logger.error(`Error crawling page : ${error}`);
        return {
          html: "",
          reason: `Error crawling page : ${error}`,
        };
      }
      finally {
        await page.close();
      }
    });
  }
}

export default PlaywrightService;
