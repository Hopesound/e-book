import type { Book } from '../types';
import { sampleSubtitles } from '../lib/samples';

export default function Cover({ book, small = false }: { book: Book; small?: boolean }) {
  return <div className={`book-cover cover-${book.color % 6} ${small ? 'cover-small' : ''}`} aria-hidden="true">
    {book.cover ? <img src={book.cover} alt="" /> : <>
      <div className="cover-grain" /><span className="cover-edition">ONLEAF ORIGINALS</span>
      <div className="cover-type"><span>{book.title}</span><small>{book.sample ? sampleSubtitles[book.color] : book.author}</small></div>
      <div className="cover-art"><i /><i /><i /><i /></div>
      <span className="cover-author">{book.author}</span>
      <span className="cover-publisher">onleaf</span>
    </>}
  </div>;
}
