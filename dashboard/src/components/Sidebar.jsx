import { useTranslation } from 'react-i18next';
import useStore from '../store';
import Icon from './Icon';

const NAV_ITEMS = [
  { section: 'operations', items: [
    { id: 'overview', icon: 'overview', label: 'overview' },
    { id: 'shelf', icon: 'shelf', label: 'shelf' },
    { id: 'queue', icon: 'queue', label: 'queue' },
  ]},
  { section: 'analytics', items: [
    { id: 'alerts', icon: 'alerts', label: 'alerts', hasBadge: true },
    { id: 'lp', icon: 'lp', label: 'lp' },
    { id: 'stores', icon: 'stores', label: 'stores' },
  ]},
  { section: 'system', items: [
    { id: 'reports', icon: 'reports', label: 'reports' },
    { id: 'settings', icon: 'settings', label: 'settings' },
  ]},
];

export default function Sidebar() {
  const { t } = useTranslation();
  const activeView = useStore(s => s.activeView);
  const setActiveView = useStore(s => s.setActiveView);
  const stores = useStore(s => s.stores);
  const selectedStoreId = useStore(s => s.selectedStoreId);
  const setSelectedStore = useStore(s => s.setSelectedStore);
  const alerts = useStore(s => s.alerts);
  const currentRole = useStore(s => s.currentRole);
  const setRole = useStore(s => s.setRole);

  const unacknowledgedCount = alerts.filter(a => !a.acknowledged).length;

  const roleViews = {
    admin: ['overview', 'shelf', 'queue', 'alerts', 'lp', 'reports', 'stores', 'settings'],
    store_manager: ['overview', 'shelf', 'queue', 'alerts', 'lp', 'reports', 'stores'],
    cashier: ['queue'],
    lp_officer: ['alerts', 'lp'],
  };

  const allowedViews = roleViews[currentRole] || roleViews.admin;

  return (
    <aside className="sidebar" role="navigation" aria-label="Main navigation">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="logo-icon">SS</div>
        <div>
          <h1>{t('app.title')}</h1>
          <div className="logo-subtitle">{t('app.subtitle')}</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {NAV_ITEMS.map(section => {
          const visibleItems = section.items.filter(item => allowedViews.includes(item.id));
          if (visibleItems.length === 0) return null;

          return (
            <div key={section.section}>
              <div className="nav-section-title">{t(`nav.${section.section}`)}</div>
              {visibleItems.map(item => (
                <button
                  key={item.id}
                  className={`nav-item ${activeView === item.id ? 'active' : ''}`}
                  onClick={() => setActiveView(item.id)}
                  aria-current={activeView === item.id ? 'page' : undefined}
                  tabIndex={0}
                >
                  <span className="nav-icon" aria-hidden="true">
                    <Icon name={item.icon} size={18} color={activeView === item.id ? 'var(--accent-primary-light)' : 'var(--text-muted)'} />
                  </span>
                  <span>{t(`nav.${item.label}`)}</span>
                  {item.hasBadge && unacknowledgedCount > 0 && (
                    <span className="nav-badge" aria-label={`${unacknowledgedCount} unread alerts`}>
                      {unacknowledgedCount}
                    </span>
                  )}
                </button>
              ))}
            </div>
          );
        })}

        {/* Role switcher (dev only) */}
        <div className="nav-section-title" style={{ marginTop: '24px' }}>Role</div>
        <div style={{ padding: '4px 12px' }}>
          <select
            value={currentRole}
            onChange={e => setRole(e.target.value)}
            style={{
              width: '100%',
              background: 'var(--bg-secondary)',
              color: 'var(--text-primary)',
              border: 'none',
              boxShadow: 'var(--shadow-sm)',
              borderRadius: 'var(--radius-lg)',
              padding: '10px 14px',
              fontFamily: 'var(--font-family)',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
              outline: 'none',
            }}
          >
            <option value="admin">Admin</option>
            <option value="store_manager">Store Manager</option>
            <option value="cashier">Cashier</option>
            <option value="lp_officer">LP Officer</option>
          </select>
        </div>
      </nav>

      {/* Store Selector */}
      <div className="store-selector">
        <label htmlFor="store-select" style={{ display: 'block', fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1.2px', color: 'var(--text-muted)', marginBottom: '6px' }}>
          {t('store.select')}
        </label>
        <select
          id="store-select"
          value={selectedStoreId}
          onChange={e => setSelectedStore(e.target.value)}
        >
          {stores.map(s => (
            <option key={s.store_id} value={s.store_id}>{s.store_name}</option>
          ))}
        </select>
      </div>
    </aside>
  );
}
