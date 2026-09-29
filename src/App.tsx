import { useCallback, useEffect, useRef, useState, type ChangeEvent } from 'react';
import { ArrowDownWideNarrow, ArrowRight, BookCheck, BookMarked, BookOpen, Bookmark, Check, CheckCheck, ChevronRight, CloudOff, FolderOpen, Grid2X2, HelpCircle, LayoutList, Leaf, LibraryBig, LoaderCircle, Plus, Search, Settings2, Sparkles, Trash2, Upload, X } from 'lucide-react';
import type { Book, Preferences, Shelf } from './types';
import { progress, readPreferences } from './lib/books';
import { deleteBook, loadBooks, saveBook } from './lib/storage';
import Cover from './components/Cover';
import Modal from './components/Modal';
import Reader from './components/Reader';

const shelfNames: Record<Shelf, string> = { all: '나의 서재', reading: '읽고 있는 책', bookmarks: '책갈피', finished: '다 읽은 책' };

export default function App() {
  const [books, setBooks] = useState<Book[]>([]);
  const booksRef = useRef<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [shelf, setShelf] = useState<Shelf>('all');
  const [query, setQuery] = useState('');
  const [format, setFormat] = useState('all');
  const [sort, setSort] = useState('recent');
  const [layout, setLayout] = useState('grid');
  const [modal, setModal] = useState<'import' | 'help' | 'settings' | null>(null);
  const [deleting, setDeleting] = useState<Book | null>(null);
  const [busy, setBusy] = useState(false);
  const [importStatus, setImportStatus] = useState('');
  const [importErrors, setImportErrors] = useState<string[]>([]);
  const [dragging, setDragging] = useState(false);
  const [toast, setToast] = useState('');
  const [preferences, setPreferences] = useState(readPreferences);
  const fileInput = useRef<HTMLInputElement>(null);
  const importing = useRef(false);
  const dragDepth = useRef(0);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const notify = useCallback((message: string) => {
    clearTimeout(toastTimer.current);
    setToast(message);
    toastTimer.current = setTimeout(() => setToast(''), 4200);
  }, []);
  const replaceBooks = (next: Book[]) => { booksRef.current = next; setBooks(next); };
  useEffect(() => {
    let cancelled = false;
    loadBooks().then(result => { if (!cancelled) { booksRef.current = result; setBooks(result); } })
      .catch(() => { if (!cancelled) setLoadError(true); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);
  useEffect(() => () => clearTimeout(toastTimer.current), []);

  const updateBook = (id: string, patch: Partial<Book>) => {
    const existing = booksRef.current.find(book => book.id === id);
    if (!existing) return;
    const next = { ...existing, ...patch };
    replaceBooks(booksRef.current.map(book => book.id === id ? next : book));
    void saveBook(next).catch(() => notify('변경사항을 저장하지 못했어요. 브라우저 저장 공간을 확인해 주세요.'));
  };
  const openBook = (book: Book, page?: number) => {
    updateBook(book.id, { lastRead: Date.now(), ...(page !== undefined ? { page } : {}) });
    setActiveId(book.id);
  };
  const changePreferences = (value: Preferences) => {
    setPreferences(value);
    try { localStorage.setItem('onleaf-preferences-v1', JSON.stringify(value)); }
    catch { notify('읽기 설정을 저장하지 못했어요.'); }
  };
  const importFiles = async (files: FileList | File[]) => {
    if (importing.current || !files.length || loadError || loading) return;
    importing.current = true;
    setBusy(true); setModal('import'); setImportErrors([]);
    let added = 0, duplicates = 0;
    const errors: string[] = [];
    try {
      const { importBook } = await import('./lib/import-book');
      for (const [index, file] of Array.from(files).entries()) {
        setImportStatus(`${index + 1} / ${files.length} · ${file.name}`);
        try {
          const book = await importBook(file);
          if (booksRef.current.some(item => item.id === book.id)) { duplicates++; continue; }
          await saveBook(book);
          replaceBooks([...booksRef.current, book]);
          added++;
        } catch (error) { errors.push(`${file.name}: ${error instanceof Error ? error.message : '저장 공간이 부족하거나 파일을 읽을 수 없습니다.'}`); }
      }
    } catch { errors.push('파일 읽기 기능을 불러오지 못했습니다. 페이지를 새로고침해 주세요.'); }
    finally {
      importing.current = false;
      setBusy(false); setImportStatus(''); setImportErrors(errors);
      if (fileInput.current) fileInput.current.value = '';
    }
    if (added) { setShelf('all'); setFormat('all'); setQuery(''); setSort('recent'); }
    if (!errors.length) setModal(null);
    notify([added ? `${added}권을 서재에 담았어요.` : '', duplicates ? `이미 있는 ${duplicates}권은 건너뛰었어요.` : '', errors.length ? `${errors.length}개 파일을 불러오지 못했어요.` : ''].filter(Boolean).join(' '));
  };
  const activeBook = books.find(book => book.id === activeId);
  const reading = books.filter(book => book.lastRead > 0 && !book.completed);
  const finished = books.filter(book => book.completed);
  const bookmarkCount = books.reduce((sum, book) => sum + book.bookmarks.length, 0);
  const recent = [...reading].sort((a, b) => b.lastRead - a.lastRead)[0] ?? books.find(book => !book.completed) ?? books[0];
  const search = query.trim().toLocaleLowerCase();
  const shelfBooks = books.filter(book => (shelf === 'all' || (shelf === 'reading' && book.lastRead && !book.completed) || (shelf === 'finished' && book.completed) || (shelf === 'bookmarks' && book.bookmarks.length)) && `${book.title} ${book.author}`.toLocaleLowerCase().includes(search));
  const filtered = shelfBooks.filter(book => format === 'all' || book.format === format).sort((a, b) => sort === 'title' ? a.title.localeCompare(b.title, 'ko') : sort === 'added' ? b.addedAt - a.addedAt : (b.lastRead || b.addedAt) - (a.lastRead || a.addedAt));
  const navigate = (next: Shelf) => { setShelf(next); setQuery(''); setFormat('all'); };
  const showImport = () => { setImportErrors([]); setModal('import'); };

  return <>
    <input type="file" ref={fileInput} accept=".epub,.txt" multiple className="file-input" aria-label="전자책 파일 선택" onChange={(event: ChangeEvent<HTMLInputElement>) => { if (event.target.files) void importFiles(event.target.files); }} />
    {activeBook ? <Reader book={activeBook} preferences={preferences} onPreferences={changePreferences} onUpdate={updateBook} onClose={() => setActiveId(null)} notify={notify} /> :
    <div className="app-shell" onDragEnter={event => { event.preventDefault(); if (event.dataTransfer.types.includes('Files')) { dragDepth.current++; setDragging(true); } }} onDragOver={event => event.preventDefault()} onDragLeave={event => { event.preventDefault(); dragDepth.current--; if (dragDepth.current <= 0) setDragging(false); }} onDrop={event => { event.preventDefault(); dragDepth.current = 0; setDragging(false); void importFiles(event.dataTransfer.files); }}>
      <aside className="sidebar">
        <button className="brand" onClick={() => navigate('all')} aria-label="온리프 홈"><span className="brand-icon"><BookOpen size={23} strokeWidth={1.7} /></span><span><strong>온리프<span className="brand-dot">.</span></strong><small>ONLEAF</small></span></button>
        <div className="sidebar-section-label">MY LIBRARY</div>
        <nav className="main-nav" aria-label="서재 탐색">
          <button aria-label='전체 도서' className={shelf === 'all' ? 'active' : ''} onClick={() => navigate('all')}><LibraryBig size={19} /><span>전체 도서</span><small>{books.length}</small></button>
          <button aria-label='읽고 있는 책' className={shelf === 'reading' ? 'active' : ''} onClick={() => navigate('reading')}><BookOpen size={19} /><span>읽고 있는 책</span>{reading.length > 0 && <small>{reading.length}</small>}</button>
          <button aria-label='책갈피' className={shelf === 'bookmarks' ? 'active' : ''} onClick={() => navigate('bookmarks')}><Bookmark size={18} /><span>책갈피</span>{bookmarkCount > 0 && <small>{bookmarkCount}</small>}</button>
          <button aria-label='다 읽은 책' className={shelf === 'finished' ? 'active' : ''} onClick={() => navigate('finished')}><BookCheck size={19} /><span>다 읽은 책</span>{finished.length > 0 && <small>{finished.length}</small>}</button>
        </nav>
        <div className="sidebar-note"><span className="note-spark">✳</span><p>한 페이지씩,<br />나만의 속도로.</p><span>책을 펼치는 순간,<br />나를 위한 시간이 시작돼요.</span><div className="note-line" /></div>
        <div className="sidebar-bottom"><button onClick={() => setModal('settings')}><Settings2 size={18} />서재 설정</button><button onClick={() => setModal('help')}><HelpCircle size={18} />이용 가이드</button><div className="local-indicator"><span />이 기기에 안전하게 보관 중</div></div>
      </aside>
      <div className="workspace">
        <header className="topbar"><div className="breadcrumb">내 공간<ChevronRight size={13} /><strong>서재</strong></div><div className="topbar-right"><label className="search-field"><Search size={17} /><input placeholder="어떤 책을 찾고 있나요?" value={query} onChange={event => setQuery(event.target.value)} aria-label="책 제목 또는 저자 검색" />{query && <button aria-label="검색 지우기" onClick={() => setQuery('')}><X size={15} /></button>}</label><span className="topbar-separator" /><span className="profile-icon" aria-label="개인 서재"><Leaf size={20} /></span></div></header>
        <main className="library-content">
          <div className="page-heading"><div><div className="eyebrow">YOUR OWN LITTLE WORLD</div><h1>{shelfNames[shelf]}<span className="heading-dot">.</span></h1><p>{shelf === 'all' ? '책과 함께하는 시간, 오늘도 한 페이지 더.' : shelf === 'reading' ? '잠시 덮어두었던 이야기를 이어가 보세요.' : shelf === 'bookmarks' ? '다시 돌아오고 싶은 페이지를 모았어요.' : '마지막 페이지까지 함께한 이야기들.'}</p></div><button className="primary-button add-book" onClick={showImport} disabled={loading || loadError}><Plus size={18} />책 추가하기</button></div>
          {loading ? <div className="state-message"><LoaderCircle className="spinning" /><h2>서재를 준비하고 있어요</h2></div> : loadError ? <div className="state-message"><CloudOff size={32} /><h2>서재 저장 공간을 열지 못했어요</h2><p>브라우저의 사이트 저장 공간 허용 여부를 확인한 뒤 다시 시도해 주세요.</p><button className="primary-button" onClick={() => window.location.reload()}>다시 시도</button></div> : <>
          {shelf === 'all' && !query && <div className="overview-row"><section className="reading-banner"><div className="banner-copy"><div className="banner-kicker"><span className="mini-dot" />{recent?.lastRead ? 'CONTINUE READING' : 'A MOMENT FOR YOURSELF'}</div><h2>{recent?.lastRead ? '이야기를 이어가 볼까요?' : <>잠시 쉬어가도 좋아요.<br />책 한 권과 함께라면.</>}</h2><p>{recent?.lastRead ? `${recent.title} · ${progress(recent)}% 읽었어요` : '바쁜 하루에 작은 쉼표가 되어줄 이야기.'}</p>{recent ? <button className="banner-button" onClick={() => openBook(recent)}>{recent.lastRead ? '이어서 읽기' : '첫 페이지 펼치기'}<ArrowRight size={16} /></button> : <button className="banner-button" onClick={showImport}>첫 번째 책 담기<Plus size={16} /></button>}</div><div className="banner-art" aria-hidden="true"><div className="art-orbit" /><span className="art-spark spark-one">✦</span><span className="art-spark spark-two">✧</span><div className="book-shadow" /><div className="illustrated-book"><div className="illustration-left"><i /><i /><i /><i /><i /></div><div className="illustration-right"><span /><i /><i /><i /><i /></div><b /></div><div className="little-leaf leaf-one" /><div className="little-leaf leaf-two" /></div></section><section className="reading-stats"><div className="stats-title"><span>차곡차곡, 독서 기록</span><Sparkles size={17} /></div><div className="stats-main"><span className="stats-icon"><BookMarked size={26} strokeWidth={1.5} /></span><div><strong>{books.length}<small>권</small></strong><span>내 서재에 담긴 책</span></div></div><div className="stats-bottom"><div><span className="stat-dot purple" />읽는 중<strong>{reading.length}</strong></div><div><span className="stat-dot green" />완독<strong>{finished.length}</strong></div></div></section></div>}
          <div className="collection-heading"><div><h2>{shelf === 'bookmarks' ? '간직한 페이지' : shelf === 'all' ? '내 책장' : shelfNames[shelf]}</h2><span>{shelf === 'bookmarks' ? `${bookmarkCount}개의 책갈피` : `${shelfBooks.length}권의 책`}</span></div>{shelf === 'all' && <span className="collection-hint"><CloudOff size={14} />나만의 기기에 저장되는 서재</span>}</div>
          <div className="collection-toolbar"><div className="format-tabs" aria-label="파일 형식 필터">{['all', 'EPUB', 'TXT'].map(item => <button key={item} className={format === item ? 'active' : ''} onClick={() => setFormat(item)}>{item === 'all' ? '전체' : item}<span>{item === 'all' ? shelfBooks.length : shelfBooks.filter(book => book.format === item).length}</span></button>)}</div><div className="view-tools"><label className="sort-control"><ArrowDownWideNarrow size={15} /><select value={sort} onChange={event => setSort(event.target.value)} aria-label="책 정렬"><option value="recent">최근 읽은 순</option><option value="added">최근 추가한 순</option><option value="title">제목 순</option></select></label>{shelf !== 'bookmarks' && <div className="layout-toggle"><button className={layout === 'grid' ? 'active' : ''} aria-label="격자로 보기" aria-pressed={layout === 'grid'} onClick={() => setLayout('grid')}><Grid2X2 size={17} /></button><button className={layout === 'list' ? 'active' : ''} aria-label="목록으로 보기" aria-pressed={layout === 'list'} onClick={() => setLayout('list')}><LayoutList size={18} /></button></div>}</div></div>
          {!filtered.length ? <div className="empty-state"><span><FolderOpen size={33} strokeWidth={1.4} /></span><h2>{query ? '찾으시는 책이 없어요' : shelf === 'bookmarks' ? '아직 꽂아둔 책갈피가 없어요' : shelf === 'reading' ? '어떤 이야기로 시작할까요?' : shelf === 'finished' ? '완독의 기쁨을 기다리고 있어요' : '새로운 이야기를 담아보세요'}</h2><p>{query ? '다른 제목이나 저자로 검색해 보세요.' : shelf === 'bookmarks' ? '읽기 화면의 책갈피 아이콘을 눌러 보세요.' : shelf === 'finished' ? '마지막 페이지에서 ‘다 읽었어요’를 눌러 주세요.' : '내 서재의 책을 펼치거나 EPUB·TXT 파일을 추가해 보세요.'}</p><button className="secondary-button" onClick={() => { if (query) setQuery(''); else if (shelf !== 'all') navigate('all'); else showImport(); }}>{query ? '검색 지우기' : shelf !== 'all' ? '전체 도서 보기' : '책 추가하기'}<ArrowRight size={15} /></button></div> : shelf === 'bookmarks' ? <div className="bookmark-list">{filtered.flatMap(book => [...book.bookmarks].sort((a, b) => a.page - b.page).map(mark => <div className="bookmark-card" key={`${book.id}-${mark.page}`}><span className="bookmark-badge"><Bookmark size={20} /></span><button onClick={() => openBook(book, mark.page)}><strong>{mark.label}</strong><span>{book.title} · {mark.page + 1} 페이지</span></button><button className="icon-button" aria-label={`${book.title} ${mark.page + 1} 페이지 책갈피 삭제`} onClick={() => updateBook(book.id, { bookmarks: book.bookmarks.filter(item => item.page !== mark.page) })}><Trash2 size={17} /></button><ChevronRight size={17} /></div>))}</div> : <div className={`books-${layout}`}>{filtered.map(book => <article className="book-card" key={book.id}><button className="book-cover-button" onClick={() => openBook(book)} aria-label={`${book.title} 읽기`}><Cover book={book} /><span className="cover-hover"><BookOpen size={20} />{book.lastRead ? '이어서 읽기' : '책 펼치기'}</span>{book.completed && <span className="completed-badge"><CheckCheck size={12} />완독</span>}</button><div className="book-info"><div className="book-metadata"><span className={`format-badge ${book.format.toLowerCase()}`}>{book.format}</span>{book.sample && <span className="sample-label">샘플 도서</span>}<button className="delete-book" onClick={() => setDeleting(book)} aria-label={`${book.title} 삭제`}><Trash2 size={14} /></button></div><button className="book-title" onClick={() => openBook(book)}>{book.title}</button><p className="book-author">{book.author}</p><div className="book-progress">{book.lastRead ? <><div className="progress-track"><span style={{ width: `${progress(book)}%` }} /></div><span>{progress(book)}%</span></> : <span className="unread-label"><span />아직 펼치지 않은 이야기</span>}</div></div></article>)}</div>}
          {shelf === 'all' && !query && <button className="import-strip" onClick={showImport}><span className="import-strip-icon"><Plus size={19} /></span><span><strong>다음 이야기를 서재에 담아보세요</strong><small>EPUB, TXT 파일을 이곳에 끌어다 놓거나 클릭해 주세요.</small></span><span className="import-strip-action">파일 불러오기<ArrowRight size={15} /></span></button>}
          <footer className="library-footer"><span>좋은 책과 나 사이, <b>온리프</b></span><span>MADE FOR YOUR READING MOMENTS</span></footer>
          </>}
        </main>
      </div>
      {dragging && <div className="drop-overlay"><div><Upload size={44} /><h2>이곳에 책을 놓아주세요</h2><p>EPUB · TXT / 파일당 최대 30MB</p></div></div>}
    </div>}
    {modal === 'import' && <Modal title="새로운 이야기를 담아볼까요?" onClose={() => { if (!busy) setModal(null); }}><p className="modal-description">소장하고 있는 전자책을 나의 서재에 추가하세요.</p><button className="upload-zone" disabled={busy} onClick={() => fileInput.current?.click()}>{busy ? <LoaderCircle size={34} className="spinning" /> : <Upload size={32} strokeWidth={1.5} />}<strong>{busy ? '책을 서재에 담고 있어요' : '파일을 선택해 주세요'}</strong><span>{busy ? importStatus : 'EPUB 또는 TXT · 여러 권 선택 가능 · 최대 30MB'}</span>{!busy && <span className="upload-button">내 컴퓨터에서 가져오기</span>}</button>{importErrors.length > 0 && <ul className="import-errors" role="alert">{importErrors.map((error, index) => <li key={index}>{error}</li>)}</ul>}<p className="privacy-note"><CloudOff size={15} />책은 서버로 전송되지 않고 이 브라우저에만 저장됩니다.</p><p className="import-limit-note">텍스트 중심 EPUB을 지원해요. DRM, PDF, 이미지·복잡한 편집은 지원하지 않습니다.</p></Modal>}
    {modal === 'help' && <Modal title="온리프, 이렇게 사용해 보세요" onClose={() => setModal(null)}><div className="guide-steps"><section><span>01</span><div><h3>나만의 서재 채우기</h3><p>책 추가하기를 누르거나 파일을 화면으로 끌어다 놓으세요. EPUB과 TXT를 지원합니다. 기본 책 6권은 온리프가 직접 작성한 체험용 콘텐츠입니다.</p></div></section><section><span>02</span><div><h3>나에게 편안한 읽기</h3><p>책을 누르면 읽기 화면이 열려요. 오른쪽 위 설정에서 글자 크기, 글꼴, 배경색을 바꿀 수 있어요.</p></div></section><section><span>03</span><div><h3>다음에 다시, 그 페이지부터</h3><p>읽던 페이지와 책갈피가 자동으로 저장됩니다. 방향키 ← →로 페이지를 넘기고, Esc로 서재에 돌아갈 수 있어요.</p></div></section></div><p className="info-box">브라우저 데이터를 삭제하면 서재도 삭제됩니다. 원본 파일은 따로 보관해 주세요. 다른 기기와 자동 동기화되지는 않습니다.</p></Modal>}
    {modal === 'settings' && <Modal title="내 서재 정보" onClose={() => setModal(null)}><div className="storage-info"><span className="storage-symbol"><LibraryBig size={30} /></span><strong>{books.length}권의 책과 함께하고 있어요.</strong><p>온리프 0.1 · 나만의 작은 서재</p></div><div className="settings-row"><span>저장 위치</span><strong>현재 브라우저 · 이 기기</strong></div><div className="settings-row"><span>책갈피</span><strong>{bookmarkCount}개</strong></div><div className="settings-row"><span>지원 파일</span><strong>EPUB, TXT</strong></div><p className="info-box">책과 독서 기록은 IndexedDB에 저장됩니다. 브라우저 데이터를 지우거나 다른 주소·브라우저로 접속하면 기존 서재를 볼 수 없으므로 원본 책은 보관해 주세요.</p><button className="secondary-button full-width" onClick={() => { changePreferences({ theme: 'light', fontSize: 19, font: 'serif' }); notify('읽기 설정을 기본값으로 되돌렸어요.'); }}>읽기 설정 초기화</button></Modal>}
    {deleting && <Modal title="이 책을 서재에서 삭제할까요?" onClose={() => setDeleting(null)}><p className="modal-description"><strong>{deleting.title}</strong>의 읽기 기록과 책갈피도 함께 삭제됩니다. 컴퓨터의 원본 파일은 유지됩니다.</p><div className="modal-actions"><button className="secondary-button" onClick={() => setDeleting(null)}>취소</button><button className="danger-button" onClick={async () => { try { await deleteBook(deleting.id); replaceBooks(booksRef.current.filter(book => book.id !== deleting.id)); setDeleting(null); notify('책을 서재에서 삭제했어요.'); } catch { notify('삭제하지 못했어요. 다시 시도해 주세요.'); } }}>삭제하기</button></div></Modal>}
    {toast && <div className="toast" role="status"><Check size={17} /><span>{toast}</span><button aria-label="알림 닫기" onClick={() => setToast('')}><X size={15} /></button></div>}
  </>;
}

