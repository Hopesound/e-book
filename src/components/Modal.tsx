import { useEffect, useRef, type ReactNode } from 'react';
import { X } from 'lucide-react';

export default function Modal({ title, children, onClose }: { title: string; children: ReactNode; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current!;
    dialog.showModal();
    return () => dialog.close();
  }, []);
  return <dialog className="modal" ref={ref} onCancel={event => { event.preventDefault(); onClose(); }} onClick={e => { if (e.target === e.currentTarget) onClose(); }} aria-label={title}>
    <div className="modal-inner"><div className="modal-heading"><h2>{title}</h2><button className="icon-button" onClick={onClose} aria-label="닫기"><X size={20} /></button></div>{children}</div>
  </dialog>;
}

