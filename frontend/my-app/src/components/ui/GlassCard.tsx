import React from 'react';
import styles from './GlassCard.module.css';
import { clsx } from 'clsx';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
}

export const GlassCard: React.FC<GlassCardProps> = ({ children, className }) => {
  return (
    <div className={clsx(styles.card, className)}>
      {children}
    </div>
  );
};
