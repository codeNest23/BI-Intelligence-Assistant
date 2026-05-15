import React, { useCallback, useState } from 'react';
import { useAppStore } from '../../context/appStore';
import { GlassCard } from '../ui/GlassCard';
import { Upload, CheckCircle2, Loader2 } from 'lucide-react';
import styles from './PdfUploader.module.css';
import { clsx } from 'clsx';

export const PdfUploader: React.FC = () => {
  const { setPdfData, pdfName } = useAppStore();
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    if (file.type !== 'application/pdf') {
      alert('Please upload a PDF file.');
      return;
    }

    setIsUploading(true);

    // Simulate upload and processing
    // In a real app, this would call an API
    setTimeout(() => {
      setPdfData({
        pdfFile: file,
        pdfName: file.name,
        pdfSizeKb: file.size / 1024,
        pdfPages: 12, // Mocked
        pdfText: 'Mocked PDF text content...',
      });
      setIsUploading(false);
    }, 2000);
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  }, []);

  const onFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFiles(e.target.files);
  };

  return (
    <div className={styles.container}>
      <GlassCard className={clsx(styles.dropzone, isDragging && styles.dragging)}>
        <input
          type="file"
          id="fileInput"
          className={styles.fileInput}
          accept=".pdf"
          onChange={onFileSelect}
        />
        <label htmlFor="fileInput" className={styles.label} onDragOver={onDragOver} onDragLeave={onDragLeave} onDrop={onDrop}>
          {isUploading ? (
            <div className={styles.status}>
              <Loader2 className={styles.spinner} size={48} />
              <h3>Processing Document...</h3>
              <p>Extracting text and generating embeddings</p>
            </div>
          ) : pdfName ? (
            <div className={styles.status}>
              <CheckCircle2 className={styles.successIcon} size={48} />
              <h3>{pdfName}</h3>
              <p>Document ready for analysis</p>
            </div>
          ) : (
            <div className={styles.status}>
              <div className={styles.uploadIconContainer}>
                <Upload size={32} />
              </div>
              <h3>Upload your PDF</h3>
              <p>Drag and drop or click to browse</p>
              <span className={styles.hint}>Supported format: PDF</span>
            </div>
          )}
        </label>
      </GlassCard>
    </div>
  );
};
