import React from 'react';
import { useAppStore } from '../../context/appStore';
import styles from './Sidebar.module.css';
import { FileUp, MessageSquare, BarChart3, FileText } from 'lucide-react';
import { clsx } from 'clsx';

export const Sidebar: React.FC = () => {
  const { currentPage, setPage, pdfName, pdfPages, pdfSizeKb } = useAppStore();
  const hasPdf = !!pdfName;

  const navItems = [
    { icon: <FileUp size={20} />, label: 'Upload PDF', key: 'upload' as const },
    { icon: <MessageSquare size={20} />, label: 'RAG Agent', key: 'rag' as const },
    { icon: <BarChart3 size={20} />, label: 'Trend Analysis', key: 'trend' as const },
  ];

  const handleNavClick = (key: 'upload' | 'rag' | 'trend') => {
    if (key !== 'upload' && !hasPdf) {
      alert('Please upload a PDF first.');
      return;
    }
    setPage(key);
  };

  return (
    <aside className={styles.sidebar}>
      <div className={styles.header}>
        <div className={styles.logoContainer}>
          <div className={styles.logoIcon}>
            <span>🧠</span>
          </div>
        </div>
        <h2 className={styles.title}>PDF Intelligence</h2>
        <p className={styles.subtitle}>v2.0 • Multi-Agent AI</p>
      </div>

      <nav className={styles.navSection}>
        <p className={styles.navHeading}>Main Navigation</p>
        {navItems.map((item) => (
          <button
            key={item.key}
            className={clsx(
              styles.navButton,
              currentPage === item.key && styles.navButtonActive
            )}
            onClick={() => handleNavClick(item.key)}
          >
            {item.icon}
            <span>
              {item.label}
              {item.key === 'upload' && hasPdf && ' (Ready)'}
            </span>
          </button>
        ))}
      </nav>

      {hasPdf && (
        <div className={styles.activeDoc}>
          <p className={styles.docHeading}>Active Document</p>
          <div className={styles.docInfo}>
            <div className={styles.docIcon}>
              <FileText color="#E2E8F0" />
            </div>
            <div className={styles.docDetails}>
              <div className={styles.docName} title={pdfName || ''}>
                {pdfName}
              </div>
              <div className={styles.docMeta}>
                {pdfPages} pages • {pdfSizeKb?.toFixed(1)} KB
              </div>
            </div>
          </div>
          <div className={styles.progressBar}>
            <div className={styles.progressFill}></div>
          </div>
          <p className={styles.statusText}>Status: Indexed & Ready</p>
        </div>
      )}

      <footer className={styles.footer}>
        <div className={styles.footerText}>
          Powered by <span className={styles.footerAccent}>OpenRouter & Pinecone</span>
        </div>
      </footer>
    </aside>
  );
};
