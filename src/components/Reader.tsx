import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Bookmark,
  Check,
  ChevronLeft,
  ChevronRight,
  List,
  Minus,
  Plus,
  Settings2,
  X,
} from "lucide-react";
import type { Book, Preferences } from "../types";
import { paginate } from "../lib/books";

interface Props {
  book: Book;
  preferences: Preferences;
  onPreferences: (value: Preferences) => void;
  onUpdate: (id: string, patch: Partial<Book>) => void;
  onClose: () => void;
  notify: (message: string) => void;
}

export default function Reader({
  book,
  preferences,
  onPreferences,
  onUpdate,
  onClose,
  notify,
}: Props) {
  const pages = useMemo(() => paginate(book.chapters), [book.chapters]);
  const current = Math.min(book.page, pages.length - 1);
  const page = pages[current];
  const [panel, setPanel] = useState<"toc" | "settings" | "bookmarks" | null>(
    null,
  );
  const scrollRef = useRef<HTMLDivElement>(null);
  const isBookmarked = book.bookmarks.some((mark) => mark.page === current);
  const percentage = book.completed
    ? 100
    : Math.round((current / Math.max(1, pages.length - 1)) * 100);
  const goTo = (index: number) => {
    if (index >= 0 && index < pages.length)
      onUpdate(book.id, { page: index, lastRead: Date.now() });
  };
  const toggleBookmark = () => {
    onUpdate(book.id, {
      bookmarks: isBookmarked
        ? book.bookmarks.filter((mark) => mark.page !== current)
        : [
            ...book.bookmarks,
            { page: current, label: page.title, createdAt: Date.now() },
          ],
    });
    notify(
      isBookmarked ? "책갈피를 지웠어요." : "이 페이지에 책갈피를 꽂았어요.",
    );
  };
  useEffect(() => {
    scrollRef.current?.scrollTo(0, 0);
  }, [current]);
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.target as HTMLElement).closest("input, select, textarea"))
        return;
      if (event.key === "ArrowRight") {
        event.preventDefault();
        goTo(current + 1);
      }
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        goTo(current - 1);
      }
      if (event.key === "Escape") {
        if (panel) setPanel(null);
        else onClose();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  });
  useEffect(() => {
    document.title = `${book.title} — 온리프`;
    return () => {
      document.title = "온리프 — 나만의 작은 서재";
    };
  }, [book.title]);

  return (
    <div className={`reader reader-${preferences.theme}`}>
      <header className="reader-header">
        <button className="text-button back-button" onClick={onClose}>
          <ArrowLeft size={18} />
          <span>내 서재</span>
        </button>
        <div className="reader-book-title">
          <strong>{book.title}</strong>
          <span>{book.author}</span>
        </div>
        <div className="reader-tools">
          <button
            className={`icon-button ${panel === "toc" ? "selected" : ""}`}
            aria-label="목차"
            aria-expanded={panel === "toc"}
            onClick={() => setPanel(panel === "toc" ? null : "toc")}
          >
            <List size={21} />
          </button>
          <button
            className={`icon-button ${isBookmarked ? "selected" : ""}`}
            aria-label={isBookmarked ? "책갈피 제거" : "책갈피 추가"}
            aria-pressed={isBookmarked}
            onClick={toggleBookmark}
          >
            <Bookmark size={20} fill={isBookmarked ? "currentColor" : "none"} />
          </button>
          <button
            className={`icon-button ${panel === "settings" ? "selected" : ""}`}
            aria-label="읽기 설정"
            aria-expanded={panel === "settings"}
            onClick={() => setPanel(panel === "settings" ? null : "settings")}
          >
            <Settings2 size={20} />
          </button>
        </div>
      </header>
      <div className="reader-main">
        {panel && (
          <aside
            className="reader-panel"
            aria-label={panel === "settings" ? "읽기 설정" : "책 탐색"}
          >
            <div className="panel-heading">
              <h2>{panel === "settings" ? "편안한 읽기" : "책 속으로"}</h2>
              <button
                className="icon-button"
                aria-label="패널 닫기"
                onClick={() => setPanel(null)}
              >
                <X size={18} />
              </button>
            </div>
            {panel === "settings" ? (
              <>
                <div className="setting-group">
                  <span>화면 테마</span>
                  <div className="theme-options">
                    {(["light", "sepia", "dark"] as const).map((theme) => (
                      <button
                        key={theme}
                        className={`theme-option theme-${theme} ${preferences.theme === theme ? "active" : ""}`}
                        aria-pressed={preferences.theme === theme}
                        onClick={() => onPreferences({ ...preferences, theme })}
                      >
                        <span>가</span>
                        {theme === "light"
                          ? "밝게"
                          : theme === "sepia"
                            ? "따뜻하게"
                            : "어둡게"}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="setting-group">
                  <span>글자 크기</span>
                  <div className="font-size-control">
                    <button
                      className="icon-button"
                      disabled={preferences.fontSize <= 14}
                      aria-label="글자 작게"
                      onClick={() =>
                        onPreferences({
                          ...preferences,
                          fontSize: preferences.fontSize - 1,
                        })
                      }
                    >
                      <Minus size={18} />
                    </button>
                    <strong>{preferences.fontSize}px</strong>
                    <button
                      className="icon-button"
                      disabled={preferences.fontSize >= 28}
                      aria-label="글자 크게"
                      onClick={() =>
                        onPreferences({
                          ...preferences,
                          fontSize: preferences.fontSize + 1,
                        })
                      }
                    >
                      <Plus size={18} />
                    </button>
                  </div>
                </div>
                <div className="setting-group">
                  <span>글꼴</span>
                  <div className="font-options">
                    <button
                      className={preferences.font === "serif" ? "active" : ""}
                      onClick={() =>
                        onPreferences({ ...preferences, font: "serif" })
                      }
                    >
                      단정한 명조
                    </button>
                    <button
                      className={preferences.font === "sans" ? "active" : ""}
                      onClick={() =>
                        onPreferences({ ...preferences, font: "sans" })
                      }
                    >
                      깔끔한 고딕
                    </button>
                  </div>
                </div>
                <p className="panel-note">
                  설정과 읽던 페이지는 자동으로 저장돼요.
                </p>
              </>
            ) : (
              <>
                <div className="panel-tabs">
                  <button
                    className={panel === "toc" ? "active" : ""}
                    onClick={() => setPanel("toc")}
                  >
                    목차
                  </button>
                  <button
                    className={panel === "bookmarks" ? "active" : ""}
                    onClick={() => setPanel("bookmarks")}
                  >
                    책갈피 {book.bookmarks.length}
                  </button>
                </div>
                {panel === "toc" ? (
                  book.chapters.map((chapter, index) => (
                    <button
                      className={`chapter-link ${page.chapter === index ? "active" : ""}`}
                      key={index}
                      onClick={() => {
                        goTo(pages.findIndex((item) => item.chapter === index));
                        setPanel(null);
                      }}
                    >
                      <span>{String(index + 1).padStart(2, "0")}</span>
                      {chapter.title}
                    </button>
                  ))
                ) : book.bookmarks.length ? (
                  [...book.bookmarks]
                    .sort((a, b) => a.page - b.page)
                    .map((mark) => (
                      <button
                        className="chapter-link"
                        key={mark.page}
                        onClick={() => {
                          goTo(mark.page);
                          setPanel(null);
                        }}
                      >
                        <Bookmark size={16} />
                        <span>
                          {mark.label}
                          <small>{mark.page + 1} 페이지</small>
                        </span>
                      </button>
                    ))
                ) : (
                  <p className="panel-note">
                    기억하고 싶은 페이지에
                    <br />
                    책갈피를 꽂아 보세요.
                  </p>
                )}
              </>
            )}
          </aside>
        )}
        <div className="reading-scroll" ref={scrollRef}>
          <article
            className={`reading-page font-${preferences.font}`}
            style={{ fontSize: `${preferences.fontSize}px` }}
          >
            <span className="chapter-eyebrow">
              CHAPTER {String(page.chapter + 1).padStart(2, "0")}
            </span>
            <h1>{page.title}</h1>
            <span className="chapter-divider" />
            {page.paragraphs.map((paragraph, index) => (
              <p key={`${current}-${index}`}>{paragraph}</p>
            ))}
            {current === pages.length - 1 && (
              <div className="end-of-book">
                <span>이야기의 마지막 페이지입니다.</span>
                <button
                  className="primary-button"
                  onClick={() => {
                    onUpdate(book.id, {
                      completed: true,
                      lastRead: Date.now(),
                    });
                    notify("한 권을 다 읽으셨네요. 완독한 책에 담았어요.");
                    onClose();
                  }}
                >
                  <Check size={17} />
                  {book.completed ? "완독한 책으로 돌아가기" : "다 읽었어요"}
                </button>
              </div>
            )}
          </article>
        </div>
        <button
          className="page-turn page-turn-prev"
          disabled={current === 0}
          onClick={() => goTo(current - 1)}
          aria-label="이전 페이지"
        >
          <ChevronLeft size={25} />
        </button>
        <button
          className="page-turn page-turn-next"
          disabled={current === pages.length - 1}
          onClick={() => goTo(current + 1)}
          aria-label="다음 페이지"
        >
          <ChevronRight size={25} />
        </button>
      </div>
      <footer className="reader-footer">
        <span className="footer-chapter">{page.title}</span>
        <div className="page-navigation">
          <button
            className="icon-button"
            disabled={current === 0}
            aria-label="이전"
            onClick={() => goTo(current - 1)}
          >
            <ArrowLeft size={16} />
          </button>
          <label className="page-range">
            <span>
              {current + 1} <i>/ {pages.length}</i>
            </span>
            <input
              aria-label="읽기 위치"
              type="range"
              min="0"
              max={pages.length - 1}
              value={current}
              onChange={(e) => goTo(Number(e.target.value))}
            />
          </label>
          <button
            className="icon-button"
            disabled={current === pages.length - 1}
            aria-label="다음"
            onClick={() => goTo(current + 1)}
          >
            <ArrowRight size={16} />
          </button>
        </div>
        <span className="footer-progress">{percentage}% 읽음</span>
      </footer>
    </div>
  );
}
