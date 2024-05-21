interface CrawlerOptions {
  timeout: number;
  concurrent: number;
}

export interface RequestOptions extends CrawlerOptions {
  headers?: Record<string, string>;
  followRedirect?: boolean;
}

export interface PlaywrightOptions extends CrawlerOptions {
  headless: boolean;
  instance: number;
}

export interface CrawlerResult {
  html: string;
  reason: string;
}

export interface CrawlerResponse {
  idx: number;
  time: number;
  url: string;
  title: string;
  description: string;
  extract_text: string;
  available: boolean;
  reason: string;
  adapter: string;
}
