import https from "node:https";
import type { AxiosInstance } from "axios";
import axios from "axios";
import iconv from "iconv-lite";
import { BaseCrawler } from "../crawler-service";
import logger from "../lib/logger";

import { randomHeader } from "../lib/utils";
import type { CrawlerResult, RequestOptions } from "../types";

class RequestCrawler extends BaseCrawler {
  private instance: AxiosInstance | undefined = undefined;
  private options: RequestOptions = { timeout: 5, concurrent: 5, followRedirect: true };

  constructor(options: RequestOptions) {
    super();
    this.options = options;
  }

  async initialize(): Promise<void> {
    if (this.instance === undefined) {
      this.instance = axios.create({
        timeout: (this.options.timeout ?? 5) * 1000,
        withCredentials: false,
        maxRedirects: 50,
      });
    }
  }

  async close(): Promise<void> {
    logger.warning("RequestCrawler closed!");
  }

  async crawl(url: string): Promise<CrawlerResult> {
    try {
      const response = await this.instance?.get(url, {
        responseType: "arraybuffer",
        headers: {
          ...randomHeader(),
        },
        httpsAgent: new https.Agent({
          rejectUnauthorized: false,
        }),
      });

      const sourceHtml = response?.data.toString();
      let charset = "utf-8"; // 默认字符集为 utf-8
      const match = sourceHtml.match(/<meta.*?charset="?([\w-]+)"/i);

      if (match) {
        charset = match[1].trim();
      }

      logger.info(`Charset [${charset}] : ${url}`);

      const html = iconv.decode(response?.data, charset);

      if (html.trim().length === 0) {
        return {
          html: "",
          reason: `Empty html : ${url} : ${response?.status} -> ${response?.statusText}`,
        };
      }

      return {
        html,
        reason: "",
      };
    }
    catch (error) {
      logger.error(`Error fetching data : ${url} : ${error}`);
      return { html: "", reason: `Error fetch : ${error}` };
    }
  }
}

export default RequestCrawler;
