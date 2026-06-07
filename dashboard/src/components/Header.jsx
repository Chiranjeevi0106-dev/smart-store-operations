import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import useStore from '../store';
import Icon from './Icon';

const VIEW_TITLES = {
  overview: 'nav.overview',
  shelf: 'nav.shelf',
  queue: 'nav.queue',
  alerts: 'nav.alerts',
  lp: 'nav.lp',
  stores: 'nav.stores',
  reports: 'nav.reports',
  settings: 'nav.settings',
};

export default function Header() {
  const { t, i18n } = useTranslation();
  const activeView = useStore(s => s.activeView);
  const theme = useStore(s => s.theme);
  const toggleTheme = useStore(s => s.toggleTheme);
  const wsConnected = useStore(s => s.wsConnected);
  const selectedStoreId = useStore(s => s.selectedStoreId);
  const user = useStore(s => s.user);
  const setActiveView = useStore(s => s.setActiveView);
  const logout = useStore(s => s.logout);
  const [time, setTime] = useState(new Date());
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const changeLang = (lng) => {
    i18n.changeLanguage(lng);
  };

  return (
    <header className="header" role="banner">
      <div className="header-left">
        <h2>{t(VIEW_TITLES[activeView] || 'nav.overview')}</h2>
        <span style={{
          fontSize: '11px',
          color: 'var(--text-muted)',
          background: 'var(--bg-glass)',
          padding: '3px 10px',
          borderRadius: 'var(--radius-full)',
          border: '1px solid var(--border-subtle)',
        }}>
          {selectedStoreId}
        </span>
      </div>

      <div className="header-right">
        {/* Language Switcher */}
        <div className="lang-switcher" role="group" aria-label="Language selector">
          {['en', 'hi', 'kn'].map(lng => (
            <button
              key={lng}
              className={`lang-btn ${i18n.language === lng ? 'active' : ''}`}
              onClick={() => changeLang(lng)}
              aria-pressed={i18n.language === lng}
            >
              {lng.toUpperCase()}
            </button>
          ))}
        </div>

        {/* Connection Status */}
        <div
          className={`connection-status ${wsConnected ? 'connected' : 'disconnected'}`}
          role="status"
          aria-live="polite"
        >
          <span className={wsConnected ? 'live-dot' : ''} aria-hidden="true">
            {!wsConnected && '●'}
          </span>
          {wsConnected ? t('connection.connected') : t('connection.disconnected')}
        </div>


        {/* Theme Toggle */}
        <button 
          className="btn-ghost" 
          onClick={toggleTheme}
          style={{ width: '34px', height: '34px', padding: 0, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          title={theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
        >
          <Icon name={theme === 'light' ? 'moon' : 'sun'} size={18} />
        </button>

        {/* Time */}
        <div className="header-time" aria-label={`Current time: ${time.toLocaleTimeString()}`}>
          {time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
        </div>

        {/* Avatar */}
        <div style={{ position: 'relative' }}>
          <div
            className="header-avatar"
            title={user.name}
            role="button"
            aria-label={`User: ${user.name}`}
            tabIndex={0}
            onClick={() => setShowDropdown(!showDropdown)}
          >
            {user.name.charAt(0)}
          </div>
          
          {showDropdown && (
            <div style={{
              position: 'absolute',
              top: 'calc(100% + 8px)',
              right: 0,
              width: '200px',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              boxShadow: 'var(--shadow-lg)',
              padding: '8px',
              zIndex: 1000,
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
              animation: 'slide-in 0.15s ease-out'
            }}>
              <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--border-subtle)', marginBottom: '4px' }}>
                <div style={{ fontWeight: 700, fontSize: '13px', color: 'var(--text-primary)' }}>{user.name}</div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{user.email || 'admin@smartstore.com'}</div>
              </div>
              <button style={{
                textAlign: 'left',
                padding: '8px 12px',
                background: 'transparent',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                transition: 'background var(--transition-fast)'
              }} onClick={() => {
                setShowDropdown(false);
                setActiveView('profile');
              }} onMouseOver={e => e.target.style.background = 'var(--bg-glass-hover)'} onMouseOut={e => e.target.style.background = 'transparent'}>
                Profile Settings
              </button>
              <button style={{
                textAlign: 'left',
                padding: '8px 12px',
                background: 'transparent',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
                fontSize: '12px',
                color: 'var(--status-danger)',
                fontWeight: 700,
                transition: 'background var(--transition-fast)'
              }} onClick={() => {
                setShowDropdown(false);
                logout();
              }} onMouseOver={e => e.target.style.background = 'var(--status-danger-bg)'} onMouseOut={e => e.target.style.background = 'transparent'}>
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
