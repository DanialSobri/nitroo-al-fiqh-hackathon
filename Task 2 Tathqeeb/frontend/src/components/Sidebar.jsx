import React from 'react';
import { Home, Plus, Compass, BarChart3, BookOpen, Coins } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';

const Sidebar = ({ mobileOpen, setMobileOpen }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    if (path === '/check') {
      return location.pathname === '/check' || location.pathname.startsWith('/report');
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className={`fixed left-0 top-0 h-full w-16 bg-white border-r border-gray-200 flex flex-col items-center py-4 z-50 transition-transform duration-300 ${mobileOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0`}>
      {/* Logo */}
      <div className="mb-6 p-2 cursor-pointer" onClick={() => navigate('/')}>
        <div className="w-8 h-8 flex items-center justify-center">
          <svg viewBox="0 0 24 24" className="w-full h-full text-gray-800" fill="currentColor">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" />
            <path d="M2 17L12 22L22 17V12L12 17L2 12V17Z" opacity="0.6" />
          </svg>
        </div>
      </div>
      
      {/* Navigation Items */}
      <div className="flex-1 flex flex-col gap-2 w-full items-center">
        <NavItem 
          icon={<Home size={20} />} 
          active={isActive('/')} 
          onClick={() => navigate('/')}
          label="Home"
        />
        <NavItem 
          icon={<Plus size={20} strokeWidth={2.5} />} 
          active={isActive('/check')}
          onClick={() => navigate('/check')}
          label="New"
        />
        <NavItem 
          icon={<Compass size={20} />} 
          active={isActive('/history')}
          onClick={() => navigate('/history')}
          label="History"
        />
        <NavItem 
          icon={<BarChart3 size={20} />} 
          active={isActive('/analytics')}
          onClick={() => navigate('/analytics')}
          label="Analytics"
        />
        <NavItem 
          icon={<Coins size={20} />} 
          active={isActive('/tokens')}
          onClick={() => navigate('/tokens')}
          label="Tokens"
        />
        <NavItem 
          icon={<BookOpen size={20} />} 
          active={isActive('/regulations')}
          onClick={() => navigate('/regulations')}
          label="Regulations"
        />
      </div>
      
      {/* User Avatar at bottom */}
      <div className="mt-auto">
        <button className="w-10 h-10 rounded-full bg-teal-600 flex items-center justify-center text-white font-semibold text-sm hover:bg-teal-700 transition-colors">
          N
        </button>
      </div>
    </div>
  );
};

const NavItem = ({ icon, active, onClick, label }) => (
  <button 
    onClick={onClick}
    title={label}
    className={`w-10 h-10 flex items-center justify-center rounded-lg transition-all duration-200 ${
      active 
        ? 'bg-gray-900 text-white' 
        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
    }`}
  >
    {icon}
  </button>
);

export default Sidebar;
