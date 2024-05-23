import express from "express";
import logger from "./app/lib/logger";
import RequestCrawler from "./app/crawlers/request-crawler";
import type { CrawlerResponse } from "./app/types";
import { createUUID } from "./app/utils";

const app = express();

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

const port = 3000;

interface RequestData {
  img: boolean;
  link: boolean;
  urls: string[];
}

interface ResponseData {
  trackId: string;
  data: CrawlerResponse[];
}

const requestCrawler = new RequestCrawler({
  timeout: 5,
  concurrent: 10,
});

app.get("/", async (req, res) => {
  res.send({
    ping: "pong",
  });
});

app.post("/extract", async (req, res) => {
  const body = req.body as RequestData;
  const trackId = createUUID();
  if (!body.urls || body.urls.length === 0) {
    res.json({
      trackId,
      data: [],
    } as ResponseData);
    return;
  }

  const response = await requestCrawler.crawls({ ...body });
  logger.info(`Crawled ${JSON.stringify(response)}`);
  res.json(response);
});

app.listen(port, () => {
  logger.info(`Server is running at http://localhost:${port}`);
});
