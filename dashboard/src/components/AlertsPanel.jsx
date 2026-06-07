import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import useStore from '../store';
import Icon from './Icon';

const ALERT_ICONS = {
  shelf_oos: 'shelfAlert',
  queue_warn: 'queueAlert',
  queue_open: 'laneOpen',
  lp_behaviour: 'lpAlert',
  lp_rfid: 'rfidAlert',
};

export default function AlertsPanel({ fullView = false, filterType = null }) {
  const { t } = useTranslation();
  const alerts = useStore(s => s.alerts);
  const acknowledgeAlert = useStore(s => s.acknowledgeAlert);
  const dismissAlert = useStore(s => s.dismissAlert);
  const [filterPriority, setFilterPriority] = useState('all');

  let filtered = alerts;

  // Filter by type (lp view shows only LP alerts)
  if (filterType === 'lp') {
    filtered = filtered.filter(a => a.type.startsWith('lp_'));
  }

  // Filter by priority
  if (filterPriority !== 'all') {
    filtered = filtered.filter(a => a.priority === filterPriority);
  }

  // Only show unacknowledged unless in full view
  if (!fullView) {
    filtered = filtered.filter(a => !a.acknowledged).slice(0, 8);
  }

  const formatTime = (isoString) => {
    const diff = Date.now() - new Date(isoString).getTime();
    const min = Math.floor(diff / 60000);
    if (min < 1) return t('time.now');
    if (min < 60) return t('time.minutesAgo', { count: min });
    return t('time.hoursAgo', { count: Math.floor(min / 60) });
  };

  const getTypeLabel = (type) => {
    const labels = {
      shelf_oos: t('alerts.shelfOos'),
      queue_warn: t('alerts.queueWarn'),
      queue_open: t('alerts.queueOpen'),
      lp_behaviour: t('alerts.lpBehaviour'),
      lp_rfid: t('alerts.lpRfid'),
    };
    return labels[type] || type;
  };

  return (
    <div>
      <div className="card-header">
        <div className="card-title">
          {filterType === 'lp' ? t('nav.lp') : t('alerts.title')}
          <span style={{
            marginLeft: '8px',
            fontSize: '11px',
            background: filtered.filter(a => !a.acknowledged).length > 0 ? 'var(--status-danger)' : 'var(--status-ok-bg)',
            color: filtered.filter(a => !a.acknowledged).length > 0 ? 'white' : 'var(--status-ok)',
            padding: '2px 8px',
            borderRadius: 'var(--radius-full)',
            fontWeight: 700,
          }}>
            {filtered.filter(a => !a.acknowledged).length}
          </span>
        </div>

        {(fullView || filterType) && (
          <div style={{ display: 'flex', gap: '4px' }}>
            {['all', 'urgent', 'normal', 'low'].map(p => (
              <button
                key={p}
                className="alert-btn"
                onClick={() => setFilterPriority(p)}
                style={filterPriority === p ? {
                  background: 'var(--accent-primary)',
                  color: 'white',
                  borderColor: 'var(--accent-primary)',
                } : {}}
              >
                {p === 'all' ? 'All' : t(`alerts.${p}`)}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="card-body">
        {filtered.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '40px',
            color: 'var(--text-muted)',
          }}>
            <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'center' }}>
              <Icon name="checkCircle" size={32} color="var(--status-ok)" />
            </div>
            <div>{t('alerts.noAlerts')}</div>
          </div>
        ) : (
          <div className="alerts-list" role="list" aria-label="Active alerts">
            {filtered.map((alert, idx) => (
              <div
                key={alert.id}
                className={`alert-item severity-${alert.priority}`}
                role="listitem"
                aria-label={`${alert.priority} alert: ${alert.message}`}
                style={{
                  opacity: alert.acknowledged ? 0.5 : 1,
                  animationDelay: `${idx * 0.05}s`,
                }}
              >
                <div className="alert-icon" aria-hidden="true">
                  <Icon name={ALERT_ICONS[alert.type] || 'warning'} size={20} color={
                    alert.priority === 'urgent' ? 'var(--status-danger)' :
                    alert.priority === 'normal' ? 'var(--status-warn)' :
                    'var(--status-info)'
                  } />
                </div>

                <div className="alert-content">
                  <div className="alert-title">
                    <span style={{
                      display: 'inline-block',
                      padding: '1px 6px',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '10px',
                      fontWeight: 700,
                      marginRight: '6px',
                      background: alert.priority === 'urgent'
                        ? 'var(--status-danger-bg)'
                        : alert.priority === 'normal'
                        ? 'var(--status-warn-bg)'
                        : 'var(--status-info-bg)',
                      color: alert.priority === 'urgent'
                        ? 'var(--status-danger)'
                        : alert.priority === 'normal'
                        ? 'var(--status-warn)'
                        : 'var(--status-info)',
                    }}>
                      {t(`alerts.${alert.priority}`)}
                    </span>
                    {getTypeLabel(alert.type)}
                  </div>
                  <div className="alert-desc">{alert.message}</div>
                  <div className="alert-time">
                    {formatTime(alert.timestamp)} · {alert.store_id}
                    {alert.acknowledged && ' · Acknowledged'}
                  </div>
                </div>

                {!alert.acknowledged && (
                  <div className="alert-actions">
                    <button
                      className="alert-btn"
                      onClick={(e) => { e.stopPropagation(); acknowledgeAlert(alert.id); }}
                      aria-label={`Acknowledge alert: ${alert.message}`}
                    >
                      {t('alerts.acknowledge')}
                    </button>
                    <button
                      className="alert-btn btn-dismiss"
                      onClick={(e) => { e.stopPropagation(); dismissAlert(alert.id); }}
                      aria-label={`Dismiss alert: ${alert.message}`}
                    >
                      {t('alerts.dismiss')}
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
