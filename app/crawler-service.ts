import { html2markdown } from "./lib/utils";
import type { CrawlerParams, CrawlerResponse, CrawlerResult } from "./types";

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
   * @param url the url(s) to crawl
   * @returns a promise that resolves with the crawler result(s) @see CrawlerResult
   */
  crawl: (url: string) => Promise<CrawlerResult>;
}

export abstract class BaseCrawler implements CrawlerInterface {
  abstract initialize(): Promise<void>;

  abstract close(): Promise<void>;

  abstract crawl(url: string): Promise<CrawlerResult>;

  async crawls(params: CrawlerParams): Promise<CrawlerResult[]> {
    const results = await Promise.all(params.urls.map(url => this.crawl(url)));
    // const markdown = results.map(result => html2markdown(result.html, true));
    return results;
  }
}
