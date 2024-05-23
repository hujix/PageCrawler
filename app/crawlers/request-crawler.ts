import https from "node:https";
import type { AxiosInstance } from "axios";
import axios from "axios";
import iconv from "iconv-lite";
// import pLimit,type { LimitFunction } from "p-limit";
import { BaseCrawler } from "../crawler-service";
import logger from "../lib/logger";

import { randomHeader } from "../lib/utils";
import type { CrawlerResult, RequestOptions } from "../types";

/**
 * RequestCrawler 基于 axios，使用 GET 方法请求 URL，并返回响应的 HTML 内容。
 */
class RequestCrawler extends BaseCrawler {
  private instance: AxiosInstance | undefined;
  private options: RequestOptions = { timeout: 5, concurrent: 5 };
  // private limit: LimitFunction = pLimit(5);

  constructor(options: RequestOptions) {
    super();
    this.options = options;
  }

  async initialize(): Promise<void> {
    if (this.instance === undefined) {
      // this.limit = pLimit(this.options.concurrent);
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
    await this.initialize();
    // return this.limit(async () => {
    try {
      // 1. 发起 GET 请求
      const response = await this.instance?.get(url, {
        responseType: "arraybuffer",
        headers: {
          ...randomHeader(),
        },
        httpsAgent: new https.Agent({
          rejectUnauthorized: false,
        }),
      });
      // 2. 获取响应的HTML内容编码

      const sourceHtml = response?.data.toString();
      let charset = "utf-8"; // 默认字符集为 utf-8
      const match = sourceHtml.match(/<meta.*?charset="?([\w-]+)"/i);
      if (match) {
        charset = match[1].trim().toLocaleLowerCase();
      }

      logger.info(`Charset [${charset}] : ${url}`);

      // 3. 解码 HTML 内容
      const html = iconv.decode(response?.data, charset).trim();

      // 4. 返回结果
      return {
        html,
        reason: "",
      };
    }
    catch (error) {
      logger.error(`Request Crawler error : ${error}`);
      return {
        html: "",
        reason: `Request Crawler error : ${error}`,
      };
    }
    // });
  }
}

export default RequestCrawler;
