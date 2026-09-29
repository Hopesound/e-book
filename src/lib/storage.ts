import type { Book } from "../types";
import { sampleBooks } from "./samples";

let database: Promise<IDBDatabase> | undefined;
function openDatabase(): Promise<IDBDatabase> {
  if (!database) {
    database = new Promise((resolve, reject) => {
      const request = indexedDB.open("onleaf-library", 1);
      request.onupgradeneeded = () => {
        request.result.createObjectStore("books", { keyPath: "id" });
        request.result.createObjectStore("meta");
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => {
        database = undefined;
        reject(request.error);
      };
      request.onblocked = () => {
        database = undefined;
        reject(new Error("다른 탭을 닫고 다시 시도해 주세요."));
      };
    });
  }
  return database;
}

export async function loadBooks(): Promise<Book[]> {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    // The seed flag shares a transaction with the books: deleting all books is permanent.
    const tx = db.transaction(["books", "meta"], "readwrite");
    const books = tx.objectStore("books");
    const meta = tx.objectStore("meta");
    let result: Book[] = [];
    const seeded = meta.get("seeded");
    seeded.onsuccess = () => {
      if (!seeded.result) {
        sampleBooks().forEach((book) => books.put(book));
        meta.put(true, "seeded");
      }
      const request = books.getAll();
      request.onsuccess = () => {
        result = request.result as Book[];
      };
    };
    tx.oncomplete = () => resolve(result);
    tx.onerror = () => reject(tx.error);
    tx.onabort = () =>
      reject(tx.error ?? new Error("서재를 불러오지 못했습니다."));
  });
}

export async function saveBook(book: Book): Promise<void> {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("books", "readwrite");
    tx.objectStore("books").put(book);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error ?? new Error("저장하지 못했습니다."));
  });
}

export async function deleteBook(id: string): Promise<void> {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("books", "readwrite");
    tx.objectStore("books").delete(id);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error ?? new Error("삭제하지 못했습니다."));
  });
}
