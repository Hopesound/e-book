import { beforeAll, describe, expect, it, vi } from 'vitest';
import { webcrypto } from 'node:crypto';
import { TextDecoder, TextEncoder } from 'node:util';
import { strToU8, zipSync } from 'fflate';
import { extractChapter, importBook } from './import-book';
import { paginate, progress, readPreferences } from './books';
import { sampleBooks } from './samples';

beforeAll(() => {
  vi.stubGlobal('crypto', webcrypto);
  vi.stubGlobal('TextDecoder', TextDecoder);
  vi.stubGlobal('TextEncoder', TextEncoder);
});
const makeFile = (name: string, bytes: Uint8Array | string) => {
  const data = typeof bytes === 'string' ? strToU8(bytes) : bytes;
  return { name, size: data.length, arrayBuffer: async () => new Uint8Array(data).buffer } as File;
};
function epub(overrides: Record<string, Uint8Array> = {}) {
  return zipSync({
    mimetype: strToU8('application/epub+zip'),
    'META-INF/container.xml': strToU8('<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" /></rootfiles></container>'),
    'OEBPS/content.opf': strToU8('<package xmlns="http://www.idpf.org/2007/opf"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>테스트 책</dc:title><dc:creator>테스트 저자</dc:creator></metadata><manifest><item id="two" href="text/two.xhtml" /><item id="one" href="text/one.xhtml" /></manifest><spine><itemref idref="one" /><itemref idref="two" /></spine></package>'),
    'OEBPS/text/one.xhtml': strToU8('<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>첫 번째 장</h1><p>처음 <em>만나는</em> 문장입니다.</p><script>alert(1)</script><img src="https://example.com/tracker.png" /></body></html>'),
    'OEBPS/text/two.xhtml': strToU8('<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>두 번째 장</h1><p>마지막 문장입니다.</p></body></html>'),
    ...overrides,
  });
}

describe('book import', () => {
  it('reads Korean UTF-8 TXT, normalizes lines and gives identical files identical IDs', async () => {
    const file = makeFile('내 책.txt', '안녕하세요.\r\n\r\n두 번째 문장입니다.');
    const first = await importBook(file);
    const duplicate = await importBook(makeFile('다른 이름.txt', '안녕하세요.\r\n\r\n두 번째 문장입니다.'));
    expect(first.title).toBe('내 책');
    expect(first.chapters[0].paragraphs).toEqual(['안녕하세요.', '두 번째 문장입니다.']);
    expect(first.id).toBe(duplicate.id);
  });
  it('reads UTF-16 and legacy Korean text', async () => {
    const utf16 = new Uint8Array([255, 254, 72, 0, 105, 0]);
    expect((await importBook(makeFile('utf16.txt', utf16))).chapters[0].paragraphs).toEqual(['Hi']);
    expect((await importBook(makeFile('legacy.txt', new Uint8Array([0xbe, 0xc8, 0xb3, 0xe7])))).chapters[0].paragraphs).toEqual(['안녕']);
  });
  it('uses EPUB metadata and spine order, strips executable markup', async () => {
    const book = await importBook(makeFile('test.epub', epub()));
    expect(book.title).toBe('테스트 책');
    expect(book.author).toBe('테스트 저자');
    expect(book.chapters.map(chapter => chapter.title)).toEqual(['첫 번째 장', '두 번째 장']);
    expect(book.chapters[0].paragraphs).toEqual(['처음 만나는 문장입니다.']);
    expect(JSON.stringify(book)).not.toContain('alert(');
    expect(JSON.stringify(book)).not.toContain('tracker');
  });
  it('preserves paragraph breaks in nested containers without duplicating content', () => {
    const chapter = extractChapter('<html><body><div><h1>장 제목</h1><p>첫 문단</p><p>둘째<br/>줄</p></div><p>마지막</p></body></html>', '제목');
    expect(chapter.paragraphs).toEqual(['첫 문단', '둘째\n줄', '마지막']);
  });
  it('rejects unsupported, empty, oversized and malformed files', async () => {
    await expect(importBook(makeFile('book.pdf', 'pdf'))).rejects.toThrow('EPUB 또는 TXT');
    await expect(importBook(makeFile('blank.txt', ''))).rejects.toThrow('내용이 없는');
    await expect(importBook(makeFile('spaces.txt', '   '))).rejects.toThrow('텍스트가 없습니다');
    await expect(importBook({ name: 'huge.txt', size: 31 * 1024 * 1024 } as File)).rejects.toThrow('30MB');
    await expect(importBook(makeFile('broken.epub', 'not a zip'))).rejects.toThrow('EPUB 파일을 열 수');
  });
  it('rejects DRM and an incomplete spine instead of silently omitting chapters', async () => {
    const encrypted = epub({ 'META-INF/encryption.xml': strToU8('<encryption><EncryptionMethod Algorithm="https://example.com/drm" /></encryption>') });
    await expect(importBook(makeFile('drm.epub', encrypted))).rejects.toThrow('DRM');
    const incomplete = epub({ 'OEBPS/text/two.xhtml': strToU8('broken XML') });
    await expect(importBook(makeFile('incomplete.epub', incomplete))).rejects.toThrow('문서 구조');
  });
  it('rejects zip bombs based on expanded sizes', async () => {
    const oversized = epub({ 'big.bin': new Uint8Array(81 * 1024 * 1024) });
    await expect(importBook(makeFile('large.epub', oversized))).rejects.toThrow('80MB');
  });
});

describe('reading positions', () => {
  it('keeps all text including Unicode intact when splitting long paragraphs', () => {
    const source = '가나다📚'.repeat(700);
    const pages = paginate([{ title: '장', paragraphs: [source] }], 100);
    expect(pages.map(page => page.paragraphs.join('')).join('')).toBe(source);
    expect(pages.every(page => !page.paragraphs.join('').includes('\uFFFD'))).toBe(true);
  });
  it('keeps chapter boundaries and progress between 0 and 100', () => {
    const book = sampleBooks()[0];
    expect(progress(book)).toBe(0);
    expect(paginate(book.chapters).map(page => page.chapter)).toContain(2);
    expect(progress({ ...book, completed: true })).toBe(100);
    expect(progress({ ...book, lastRead: 1, page: 999 })).toBe(99);
  });
  it('handles corrupt preferences and clamps out-of-range text sizes', () => {
    localStorage.setItem('onleaf-preferences-v1', '{broken');
    expect(readPreferences().fontSize).toBe(19);
    localStorage.setItem('onleaf-preferences-v1', JSON.stringify({ fontSize: 99, theme: 'unknown' }));
    expect(readPreferences()).toEqual({ fontSize: 28, theme: 'light', font: 'serif' });
  });
});
