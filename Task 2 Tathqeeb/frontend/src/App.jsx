import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { Menu } from 'lucide-react';
import Sidebar from './components/Sidebar';
import HomePage from './pages/HomePage';
import CheckPage from './pages/CheckPage';
import HistoryPage from './pages/HistoryPage';
import AnalyticsPage from './pages/AnalyticsPage';
import TokenDashboardPage from './pages/TokenDashboardPage';
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
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const isHomePage = location.pathname === '/';

  return (
    <div className="flex min-h-screen font-sans bg-white text-gray-900">
      {!isHomePage && <Sidebar mobileOpen={mobileSidebarOpen} setMobileOpen={setMobileSidebarOpen} />}
      {mobileSidebarOpen && <div className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden" onClick={() => setMobileSidebarOpen(false)} />}
      
      <main className={`${!isHomePage ? 'flex-1 md:ml-16 flex flex-col items-center' : 'flex-1'}`}>
        {!isHomePage && (
          <>
            <button 
              className="md:hidden fixed top-4 left-4 z-30 bg-white p-2 rounded-lg shadow-md"
              onClick={() => setMobileSidebarOpen(true)}
            >
              <Menu size={20} />
            </button>
            <div className="flex-1 flex flex-col p-4 md:p-8 w-full max-w-7xl pt-16 md:pt-4">
              <Routes>
                <Route path="/check" element={<CheckPage />} />
                <Route path="/history" element={<HistoryPage />} />
                <Route path="/analytics" element={<AnalyticsPage />} />
                <Route path="/tokens" element={<TokenDashboardPage />} />
                <Route path="/report/:contractId" element={<ReportPage />} />
                <Route path="/regulations" element={<RegulationsPage />} />
              </Routes>
            </div>
          </>
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
