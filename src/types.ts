export interface Chapter {
  title: string;
  paragraphs: string[];
}
export interface Bookmark {
  page: number;
  label: string;
  createdAt: number;
}
export interface Book {
  id: string;
  title: string;
  author: string;
  format: "EPUB" | "TXT";
  chapters: Chapter[];
  cover?: string;
  color: number;
  sample: boolean;
  addedAt: number;
  lastRead: number;
  page: number;
  completed: boolean;
  bookmarks: Bookmark[];
}
export interface Page {
  chapter: number;
  title: string;
  paragraphs: string[];
}
export interface Preferences {
  theme: "light" | "sepia" | "dark";
  fontSize: number;
  font: "serif" | "sans";
}
export type Shelf = "all" | "reading" | "bookmarks" | "finished";
