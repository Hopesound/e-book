import { strFromU8, unzip } from "fflate";
import type { Book, Chapter } from "../types";

const MAX_FILE = 30 * 1024 * 1024;
const MAX_EXPANDED = 80 * 1024 * 1024;

function xml(text: string): Document {
  const doc = new DOMParser().parseFromString(text, "application/xml");
  if (doc.getElementsByTagName("parsererror").length)
    throw new Error("EPUB 문서 구조가 올바르지 않습니다.");
  return doc;
}
function elements(doc: Document | Element, name: string): Element[] {
  return Array.from(doc.getElementsByTagNameNS("*", name));
}
function resolvePath(base: string, href: string): string {
  // Resolve archive paths only. Nothing in a book may cause a network request.
  if (/^[a-z][a-z\d+.-]*:|^\/\//i.test(href)) return "";
  const parts =
    `${base.substring(0, base.lastIndexOf("/") + 1)}${href.split("#")[0]}`.split(
      "/",
    );
  const resolved: string[] = [];
  for (const part of parts) {
    if (part === "..") resolved.pop();
    else if (part && part !== ".") resolved.push(part);
  }
  try {
    return decodeURIComponent(resolved.join("/"));
  } catch {
    return resolved.join("/");
  }
}

export function extractChapter(source: string, fallback: string): Chapter {
  const doc = xml(source);
  const body = elements(doc, "body")[0] ?? doc.documentElement;
  for (const tag of [
    "script",
    "style",
    "noscript",
    "iframe",
    "object",
    "nav",
  ]) {
    elements(body, tag).forEach((node) => node.remove());
  }
  const title =
    (elements(body, "h1")[0] ?? elements(body, "h2")[0])?.textContent?.trim() ||
    fallback;
  const clone = body.cloneNode(true) as Element;
  elements(clone, "br").forEach((node) =>
    node.replaceWith(doc.createTextNode("\n")),
  );
  for (const tag of [
    "p",
    "div",
    "h1",
    "h2",
    "h3",
    "h4",
    "li",
    "blockquote",
    "section",
    "tr",
  ]) {
    elements(clone, tag).forEach((node) =>
      node.appendChild(doc.createTextNode("\n\n")),
    );
  }
  const paragraphs = (clone.textContent ?? "")
    .replace(/\r\n?/g, "\n")
    .split(/\n\s*\n/)
    .map((text) => text.replace(/[\t ]+/g, " ").trim())
    .filter(Boolean);
  if (paragraphs[0] === title) paragraphs.shift();
  return { title, paragraphs };
}

function decodeText(bytes: Uint8Array): string {
  if (bytes[0] === 0xff && bytes[1] === 0xfe)
    return new TextDecoder("utf-16le").decode(bytes);
  if (bytes[0] === 0xfe && bytes[1] === 0xff)
    return new TextDecoder("utf-16be").decode(bytes);
  try {
    return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch {
    return new TextDecoder("euc-kr").decode(bytes);
  }
}

export async function importBook(file: File): Promise<Book> {
  if (!/\.(txt|epub)$/i.test(file.name))
    throw new Error("EPUB 또는 TXT 파일을 선택해 주세요.");
  if (file.size > MAX_FILE)
    throw new Error("한 파일당 30MB까지 불러올 수 있습니다.");
  if (!file.size) throw new Error("내용이 없는 파일입니다.");
  const data = new Uint8Array(await file.arrayBuffer());
  const hash = await crypto.subtle.digest("SHA-256", data);
  const id = Array.from(new Uint8Array(hash))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
  const base: Book = {
    id,
    title: file.name.replace(/\.[^.]+$/, ""),
    author: "작자 미상",
    format: "TXT",
    chapters: [],
    color: data.length % 6,
    sample: false,
    addedAt: Date.now(),
    lastRead: 0,
    page: 0,
    completed: false,
    bookmarks: [],
  };
  if (/\.txt$/i.test(file.name)) {
    const text = decodeText(data).replace(/\r\n?/g, "\n").trim();
    if (!text) throw new Error("읽을 수 있는 텍스트가 없습니다.");
    base.chapters = [
      {
        title: base.title,
        paragraphs: text
          .split(/\n+/)
          .map((line) => line.trim())
          .filter(Boolean),
      },
    ];
    return base;
  }

  let expanded = 0;
  const archive = await new Promise<Record<string, Uint8Array>>(
    (resolve, reject) => {
      try {
        unzip(
          data,
          {
            filter: (entry) => {
              expanded += entry.originalSize;
              return (
                expanded <= MAX_EXPANDED &&
                entry.originalSize <= 12 * 1024 * 1024
              );
            },
          },
          (error, files) =>
            error
              ? reject(
                  new Error(
                    "EPUB 파일을 열 수 없습니다. 파일이 손상되었는지 확인해 주세요.",
                  ),
                )
              : resolve(files),
        );
      } catch {
        reject(new Error("EPUB 파일을 열 수 없습니다."));
      }
    },
  );
  if (expanded > MAX_EXPANDED)
    throw new Error(
      "압축 해제한 EPUB이 너무 큽니다. 80MB 이하의 책을 사용해 주세요.",
    );
  const read = (path: string) => {
    if (!archive[path])
      throw new Error(
        "EPUB에 필요한 문서가 없거나 문서 크기 제한(12MB)을 초과했습니다.",
      );
    return strFromU8(archive[path]);
  };
  if (archive["META-INF/encryption.xml"]) {
    const encryption = xml(read("META-INF/encryption.xml"));
    const methods = elements(encryption, "EncryptionMethod");
    if (
      methods.some(
        (item) =>
          ![
            "http://www.idpf.org/2008/embedding",
            "http://ns.adobe.com/pdf/enc#RC",
          ].includes(item.getAttribute("Algorithm") ?? ""),
      )
    ) {
      throw new Error("DRM으로 보호된 EPUB은 지원하지 않습니다.");
    }
  }
  const container = xml(read("META-INF/container.xml"));
  const packagePath = elements(container, "rootfile")[0]?.getAttribute(
    "full-path",
  );
  if (!packagePath) throw new Error("올바른 EPUB 패키지를 찾지 못했습니다.");
  const pkg = xml(read(packagePath));
  base.title = elements(pkg, "title")[0]?.textContent?.trim() || base.title;
  base.author = elements(pkg, "creator")[0]?.textContent?.trim() || base.author;
  base.format = "EPUB";
  const manifest = new Map(
    elements(pkg, "item").map((item) => [item.getAttribute("id"), item]),
  );
  const coverId = elements(pkg, "meta")
    .find((item) => item.getAttribute("name") === "cover")
    ?.getAttribute("content");
  const coverItem =
    [...manifest.values()].find((item) =>
      item.getAttribute("properties")?.split(/\s+/).includes("cover-image"),
    ) ?? manifest.get(coverId ?? "");
  if (coverItem) {
    const coverPath = resolvePath(
      packagePath,
      coverItem.getAttribute("href") ?? "",
    );
    const mime = coverItem.getAttribute("media-type") ?? "";
    const bytes = archive[coverPath];
    if (
      bytes &&
      /^image\/(jpeg|png|webp|gif)$/.test(mime) &&
      bytes.length < 4 * 1024 * 1024
    ) {
      let binary = "";
      for (let offset = 0; offset < bytes.length; offset += 8192)
        binary += String.fromCharCode(...bytes.subarray(offset, offset + 8192));
      base.cover = `data:${mime};base64,${btoa(binary)}`;
    }
  }
  const spine = elements(pkg, "itemref").filter(
    (item) => item.getAttribute("linear") !== "no",
  );
  spine.forEach((ref, index) => {
    const item = manifest.get(ref.getAttribute("idref"));
    if (!item) throw new Error("EPUB의 목차와 본문이 일치하지 않습니다.");
    const path = resolvePath(packagePath, item.getAttribute("href") ?? "");
    const chapter = extractChapter(read(path), `${index + 1}장`);
    if (chapter.paragraphs.length) base.chapters.push(chapter);
  });
  if (!base.chapters.length)
    throw new Error(
      "읽을 수 있는 본문이 없습니다. 이미지 전용·고정 레이아웃 EPUB은 지원하지 않습니다.",
    );
  return base;
}
