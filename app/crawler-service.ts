import { html2markdown } from "./lib/utils";
import type { CrawlerResult } from "./types";

/**
 * CrawlerInterface is an abstract class that defines the methods that a crawler service should implement.
 */
interface CrawlerInterface {
  /**
   * initialize is a method that initializes the crawler service.
   * @returns a promise that resolves when the crawler service is initialized
   */
  initialize: () => Promise<void>;
  /**
   * close is a method that closes the crawler service.
   * @returns a promise that resolves when the crawler service is closed
   */
  close: () => Promise<void>;
  /**
   * crawl is a method that crawls a given url and returns the crawler result.
   * @param url the url to crawl
   * @returns a promise that resolves with the crawler result @see CrawlerResult
   */
  crawl: (url: string) => Promise<CrawlerResult>;
}

export abstract class BaseCrawler implements CrawlerInterface {
  abstract initialize(): Promise<void>;

  abstract close(): Promise<void>;

  abstract crawl(url: string): Promise<CrawlerResult>;

  async startCrawl(idx: number, url: string, img: boolean): Promise<object> {
    const start = performance.now();
    const { html, reason } = await this.crawl(url);

    if (html.trim() === "" && reason !== "") {
      return {
        idx,
        time: Number(((performance.now() - start) / 1000).toFixed(2)),
        url,
        title: "",
        text: "",
        reason,
      };
    }
    const { title, text } = await html2markdown(html, img);
    return {
      idx,
      title,
      text,
      url,
      time: Number(((performance.now() - start) / 1000).toFixed(2)),
      reason: "",
    };
  }
}
