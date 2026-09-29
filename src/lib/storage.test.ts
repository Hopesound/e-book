import 'fake-indexeddb/auto';
import { expect, it } from 'vitest';
import { deleteBook, loadBooks, saveBook } from './storage';

it('persists reading position, completion and bookmarks; removed samples stay removed', async () => {
  const books = await loadBooks();
  expect(books).toHaveLength(6);
  const book = { ...books[0], page: 2, completed: true, lastRead: Date.now(), bookmarks: [{ page: 1, label: '기억할 장면', createdAt: Date.now() }] };
  await saveBook(book);
  const restored = (await loadBooks()).find(item => item.id === book.id);
  expect(restored).toEqual(book);
  for (const item of books) await deleteBook(item.id);
  expect(await loadBooks()).toEqual([]);
});
