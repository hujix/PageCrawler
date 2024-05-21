import { JSDOM } from "jsdom";
// import { NodeHtmlMarkdown } from "node-html-markdown";

import { Readability } from "@mozilla/readability";
import logger from "../lib/logger";

async function cleanHtmlByMozillaReadability(
  html: string,
): Promise<{ title: string; text: string }> {
  logger.info("Mozilla Readability start extract!");
  return new Promise((resolve, _reject) => {
    const doc = new JSDOM(html);
    const reader = new Readability(doc.window.document);
    const article = reader.parse();

    if (article === undefined || article === null) {
      resolve({
        title: "",
        text: "",
      });
    }
    const content = article?.content;
    if (content === undefined) {
      resolve({
        title: article?.title ?? "",
        text: "",
      });
    }
    resolve({
      title: article?.title ?? "",
      text: content ?? "",
    });
  });
}

// const nhm = new NodeHtmlMarkdown({
//   codeBlockStyle: "fenced",
//   keepDataImages: true,
//   useLinkReferenceDefinitions: false,
// });

// async function htmlToMarkdownByNodejs(html: string): Promise<{
//   title: string;
//   text: string;
// }> {
//   return new Promise(async (resolve, _reject) => {
//     const result = (await cleanHtmlByMozillaReadability(html)) as {
//       title: string;
//       text: string;
//     };

//     if (typeof result.text !== "string" || result.text.trim().length === 0) {
//       result.text = "";
//       resolve(result);
//     }

//     const markdown = nhm.translate(result.text);

//     resolve({
//       title: result.title.trim(),
//       text: markdown.trim(),
//     });
//   });
// }

function removeImagesFromHTML(html: string): string {
  return html.replace(/<img[^>]+>/g, "");
}

export async function html2markdown(
  html: string,
  img: boolean,
): Promise<{ title: string; text: string }> {
  if (html.trim().length === 0) {
    logger.warn("html2markdown has error : html is empty");
    return {
      title: "",
      text: "",
    };
  }

  if (!img) { html = removeImagesFromHTML(html); }

  const results = (await Promise.all([
    // htmlToMarkdownByNodejs(html),
  ])) as {
    title: string;
    text: string;
  }[];
  const result = results.reduce((prev, curr) => {
    if ((prev.title + prev.text).length >= (curr.title + curr.text).length) { return prev; }

    return curr;
  });

  return {
    title: result.title.trim(),
    text: tidyMarkdown(result.text).trim(),
  };
}

function tidyMarkdown(markdown: string): string {
  // Step 1: Handle complex broken links with text and optional images spread across multiple lines
  let normalizedMarkdown = markdown.replace(
    /\[\s*([^\]\n]+?)\s*\]\s*\(\s*([^)]+)\s*\)/g,
    (match, text, url) => {
      // Remove internal new lines and excessive spaces within the text
      text = text.replace(/\s+/g, " ").trim();
      url = url.replace(/\s+/g, "").trim();
      return `[${text}](${url})`;
    },
  );

  normalizedMarkdown = normalizedMarkdown.replace(
    /\[\s*([^\]\n!]*?)\s*(?:!\[([^\]]*)\]\((.*?)\)\s*)?\]\s*\(\s*([^)]+)\s*\)/g,
    (match, text, alt, imgUrl, linkUrl) => {
      // Normalize by removing excessive spaces and new lines
      text = text.replace(/\s+/g, " ").trim();
      alt = alt ? alt.replace(/\s+/g, " ").trim() : "";
      imgUrl = imgUrl ? imgUrl.replace(/\s+/g, "").trim() : "";
      linkUrl = linkUrl.replace(/\s+/g, "").trim();
      if (imgUrl) { return `[${text} ![${alt}](${imgUrl})](${linkUrl})`; }
      else { return `[${text}](${linkUrl})`; }
    },
  );

  // Step 2: Normalize regular links that may be broken across lines
  normalizedMarkdown = normalizedMarkdown.replace(
    /\[\s*([^\]]+)\]\s*\(\s*([^)]+)\)/g,
    (match, text, url) => {
      text = text.replace(/\s+/g, " ").trim();
      url = url.replace(/\s+/g, "").trim();
      return `[${text}](${url})`;
    },
  );

  // Step 3: Replace more than two consecutive empty lines with exactly two empty lines
  normalizedMarkdown = normalizedMarkdown.replace(/\n{3,}/g, "\n\n");

  // Step 4: Remove leading spaces from each line
  normalizedMarkdown = normalizedMarkdown.replace(/^[ \t]+/gm, "");

  return normalizedMarkdown.trim();
}

const headerList: Record<string, string>[] = [
  {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "user-agent":
      "Mozilla/5.0 (Macintosh; ARM Mac OS X 14_4_1) AppleWebKit/618.1.15.11.14 (KHTML, like Gecko) Version/17.4.1 Safari/618.1.15.11.14",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US",
    "connection": "keep-alive",
  },
  {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "user-agent":
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US",
    "connection": "keep-alive",
  },
  {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "user-agent":
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US",
    "connection": "keep-alive",
  },
  {
    "connection": "Keep-Alive",
    "sec-ch-ua-platform": "\"Windows\"",
    "upgrade-insecure-requests": "1",
    "user-agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "accept":
      "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US",
  },
  {
    "connection": "keep-alive",
    "sec-ch-ua": "\"Chromium\";v=\"105\", \"Not)A;Brand\";v=\"8\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Linux\"",
    "upgrade-insecure-requests": "1",
    "user-agent":
      "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
    "accept":
      "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US",
    "dnt": "1",
  },
  {
    "connection": "keep-alive",
    "sec-ch-ua":
      "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Google Chrome\";v=\"122\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Linux\"",
    "upgrade-insecure-requests": "1",
    "user-agent":
      "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "accept":
      "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US",
  },
  {
    "connection": "keep-alive",
    "sec-ch-ua":
      "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Google Chrome\";v=\"122\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "upgrade-insecure-requests": "1",
    "user-agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "accept":
      "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US",
  },
  {
    "connection": "keep-alive",
    "sec-ch-ua":
      "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Google Chrome\";v=\"122\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "upgrade-insecure-requests": "1",
    "user-agent":
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "accept":
      "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US",
  },
  {
    "connection": "keep-alive",
    "sec-ch-ua":
      "\"Chromium\";v=\"124\", \"Google Chrome\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "upgrade-insecure-requests": "1",
    "user-agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "accept":
      "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US",
    "dnt": "1",
  },
  {
    "connection": "keep-alive",
    "sec-ch-ua":
      "\"Chromium\";v=\"124\", \"Google Chrome\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "upgrade-insecure-requests": "1",
    "user-agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "accept":
      "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US",
  },
  {
    "connection": "keep-alive",
    "sec-ch-ua":
      "\"Chromium\";v=\"124\", \"Google Chrome\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "upgrade-insecure-requests": "1",
    "user-agent":
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "accept":
      "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US",
    "dnt": "1",
  },
  {
    "connection": "keep-alive",
    "sec-ch-ua":
      "\"Chromium\";v=\"124\", \"Google Chrome\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "upgrade-insecure-requests": "1",
    "user-agent":
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "accept":
      "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US",
  },
  {
    "connection": "keep-alive",
    "sec-ch-ua":
      "\"Google Chrome\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "upgrade-insecure-requests": "1",
    "user-agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "accept":
      "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US",
  },
  {
    "connection": "keep-alive",
    "sec-ch-ua":
      "\"Google Chrome\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "upgrade-insecure-requests": "1",
    "user-agent":
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "accept":
      "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US",
  },
  {
    "connection": "keep-alive",
    "sec-ch-ua":
      "\"Not A(Brand\";v=\"99\", \"Google Chrome\";v=\"121\", \"Chromium\";v=\"121\"",
    "sec-ch-ua-mobile": "?0",
    "upgrade-insecure-requests": "1",
    "user-agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "accept":
      "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US",
  },
  {
    "connection": "keep-alive",
    "sec-ch-ua-platform": "\"Windows\"",
    "upgrade-insecure-requests": "1",
    "user-agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "accept":
      "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US",
  },
  {
    "connection": "keep-alive",
    "upgrade-insecure-requests": "1",
    "user-agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "accept":
      "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US",
  },
  {
    "sec-ch-ua":
      "\"Google Chrome\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "upgrade-insecure-requests": "1",
    "user-agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "accept":
      "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US",
  },
  {
    "sec-ch-ua":
      "\"Google Chrome\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
    "sec-ch-ua-mobile": "?0",
    "upgrade-insecure-requests": "1",
    "user-agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "accept":
      "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US",
  },
  {
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "user-agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    "accept-encoding": "gzip, deflate, br",
    "accept":
      "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "sec-ch-ua":
      "\"Microsoft Edge\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
    "connection": "keep-alive",
    "upgrade-insecure-requests": "1",
    "accept-language": "en-US",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
  },
  {
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "user-agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "accept-encoding": "gzip, deflate, br",
    "accept":
      "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "dnt": "1",
    "sec-ch-ua":
      "\"Chromium\";v=\"124\", \"Microsoft Edge\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
    "connection": "keep-alive",
    "upgrade-insecure-requests": "1",
    "accept-language": "en-US",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
  },
  {
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "user-agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "accept-encoding": "gzip, deflate, br",
    "accept":
      "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "sec-ch-ua":
      "\"Chromium\";v=\"124\", \"Microsoft Edge\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
    "connection": "keep-alive",
    "upgrade-insecure-requests": "1",
    "accept-language": "en-US",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
  },
  {
    "sec-ch-ua-platform": "\"Windows\"",
    "upgrade-insecure-requests": "1",
    "user-agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "accept":
      "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US",
  },
];

/**
 * Makes all request headers capitalized to more look like in browser
 */
export function browserifyHeaders(
  headers: Record<string, string>,
): Record<string, string> {
  const finalHeaders: Record<string, string> = {};

  for (let [key, value] of Object.entries(headers)) {
    key = key
      .toLowerCase()
      .split("-")
      .map(str => str.charAt(0).toUpperCase() + str.slice(1))
      .join("-");

    finalHeaders[key] = value;
  }

  return finalHeaders;
}

export function randomHeader(): object {
  return browserifyHeaders(
    headerList[Math.floor(Math.random() * headerList.length)],
  );
}

export function expandShadowRoots(): string {
  function getShadowContent(element: Element) {
    if (!element) {
      return null;
    };
    return element.shadowRoot?.innerHTML;
  }
  const shadowElements = Array.from(
    document.querySelectorAll("*") as NodeListOf<Element>,
  ).filter((element: Element) => element.shadowRoot !== null);

  let result = "";
  for (const shadowElement of shadowElements) {
    result += getShadowContent(shadowElement);
    if (shadowElement.querySelector("body") !== null) {
      break;
    }
  }
  if (result.trim().length === 0) {
    return "";
  };
  return `<html>${document.head}<body>${result}</body></html>`;
}
