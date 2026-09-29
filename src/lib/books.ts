import type { Book, Chapter, Page } from "../types";

export function paginate(chapters: Chapter[], limit = 1100): Page[] {
  const pages: Page[] = [];
  chapters.forEach((chapter, index) => {
    let paragraphs: string[] = [];
    let length = 0;
    const flush = () => {
      if (paragraphs.length)
        pages.push({ chapter: index, title: chapter.title, paragraphs });
      paragraphs = [];
      length = 0;
    };
    for (const paragraph of chapter.paragraphs) {
      // Stable text positions survive font-size changes and browser restarts.
      const characters = Array.from(paragraph);
      for (let offset = 0; offset < characters.length; offset += limit) {
        const part = characters.slice(offset, offset + limit).join("");
        if (length + part.length > limit) flush();
        paragraphs.push(part);
        length += part.length;
      }
    }
    flush();
  });
  return pages;
}

export function progress(
  book: Book,
  total = paginate(book.chapters).length,
): number {
  if (book.completed) return 100;
  if (!book.lastRead || total <= 1) return 0;
  return Math.min(99, Math.round((book.page / (total - 1)) * 100));
}

export function readPreferences(): import("../types").Preferences {
  try {
    const value = JSON.parse(
      localStorage.getItem("onleaf-preferences-v1") || "{}",
    );
    return {
      theme: ["light", "sepia", "dark"].includes(value.theme)
        ? value.theme
        : "light",
      fontSize:
        typeof value.fontSize === "number"
          ? Math.min(28, Math.max(14, value.fontSize))
          : 19,
      font: value.font === "sans" ? "sans" : "serif",
    };
  } catch {
    return { theme: "light", fontSize: 19, font: "serif" };
  }
}
