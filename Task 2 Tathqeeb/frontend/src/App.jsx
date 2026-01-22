import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import HomePage from './pages/HomePage';
import CheckPage from './pages/CheckPage';
import HistoryPage from './pages/HistoryPage';
import AnalyticsPage from './pages/AnalyticsPage';
import ReportPage from './pages/ReportPage';
import RegulationsPage from './pages/RegulationsPage';

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

function AppContent() {
  const location = useLocation();
  const isHomePage = location.pathname === '/';

  return (
    <div className="flex min-h-screen font-sans bg-white text-gray-900">
      {!isHomePage && <Sidebar />}
      
      <main className={`${!isHomePage ? 'flex-1 ml-16 flex flex-col items-center' : 'flex-1'}`}>
        {!isHomePage && (
          <div className="flex-1 flex flex-col p-4 md:p-8 w-full max-w-7xl">
            <Routes>
              <Route path="/check" element={<CheckPage />} />
              <Route path="/history" element={<HistoryPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route path="/report/:contractId" element={<ReportPage />} />
              <Route path="/regulations" element={<RegulationsPage />} />
            </Routes>
          </div>
        )}
        {isHomePage && (
          <Routes>
            <Route path="/" element={<HomePage />} />
          </Routes>
        )}
      </main>
    </div>
  );
}

export default App;
