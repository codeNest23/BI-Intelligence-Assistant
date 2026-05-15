import React from 'react';
import { AppLayout } from './components/layout/AppLayout';
import { useAppStore } from './context/appStore';
import { UploadPage } from './pages/UploadPage';
import { RagPage } from './pages/RagPage';
import { TrendPage } from './pages/TrendPage';

const App: React.FC = () => {
  const { currentPage } = useAppStore();

  const renderPage = () => {
    switch (currentPage) {
      case 'upload':
        return <UploadPage />;
      case 'rag':
        return <RagPage />;
      case 'trend':
        return <TrendPage />;
      default:
        return <UploadPage />;
    }
  };

  return (
    <AppLayout>
      {renderPage()}
    </AppLayout>
  );
};

export default App;
