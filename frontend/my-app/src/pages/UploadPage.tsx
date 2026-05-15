import React from 'react';
import { PdfUploader } from '../components/domain/PdfUploader';
import styles from './UploadPage.module.css';

export const UploadPage: React.FC = () => {
  return (
    <div className={styles.page}>
      <div className={styles.hero}>
        <h1 className={styles.title}>PDF Intelligence Hub</h1>
        <p className={styles.subtitle}>
          Upload your documents to unlock deep insights, agentic Q&A, and trend analysis.
        </p>
      </div>

      <div className={styles.content}>
        <PdfUploader />

        <div className={styles.features}>
          <div className={styles.feature}>
            <div className={styles.featureIcon}>🤖</div>
            <h3>Agentic RAG</h3>
            <p>Smart document interaction with multi-step reasoning.</p>
          </div>
          <div className={styles.feature}>
            <div className={styles.featureIcon}>📊</div>
            <h3>Trend Analysis</h3>
            <p>Visualizing keywords, sentiment, and topics over time.</p>
          </div>
          <div className={styles.feature}>
            <div className={styles.featureIcon}>🔍</div>
            <h3>Semantic Search</h3>
            <p>Find exact information using vector-based retrieval.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
