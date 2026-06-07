import { useTranslation } from 'react-i18next';
import useStore from '../store';
import Icon from './Icon';

export default function KPICards() {
  const { t } = useTranslation();
  const shelfData = useStore(s => s.shelfData);
  const queueData = useStore(s => s.queueData);
  const alerts = useStore(s => s.alerts);

  const stockoutPct = (shelfData.stockout_rate * 100).toFixed(1);
  const compliancePct = (shelfData.planogram_compliance * 100).toFixed(1);
  const avgWaitMin = (queueData.average_wait_seconds / 60).toFixed(1);
  const activeAlerts = alerts.filter(a => !a.acknowledged).length;

  const cards = [
    {
      id: 'stockout',
      label: t('kpi.stockoutRate'),
      value: `${stockoutPct}%`,
      change: { value: '-2.9%', positive: true },
      target: `${t('kpi.target')}: ≤5.3%`,
      icon: 'stockout',
      status: stockoutPct <= 5.3 ? 'ok' : stockoutPct <= 8 ? 'warn' : 'danger',
    },
    {
      id: 'queue',
      label: t('kpi.queueWait'),
      value: `${avgWaitMin}m`,
      change: { value: '-1.9m', positive: true },
      target: `${t('kpi.target')}: ≤4.9m`,
      icon: 'timer',
      status: avgWaitMin <= 4.9 ? 'ok' : avgWaitMin <= 6.8 ? 'warn' : 'danger',
    },
    {
      id: 'shrinkage',
      label: t('kpi.shrinkage'),
      value: '1.9%',
      change: { value: '-0.9%', positive: true },
      target: `${t('kpi.target')}: ≤1.68%`,
      icon: 'shield',
      status: 'warn',
    },
    {
      id: 'compliance',
      label: t('kpi.compliance'),
      value: `${compliancePct}%`,
      change: { value: '+8.2%', positive: true },
      target: `${t('kpi.target')}: ≥90%`,
      icon: 'clipboard',
      status: compliancePct >= 90 ? 'ok' : compliancePct >= 75 ? 'warn' : 'danger',
    },
    {
      id: 'alerts',
      label: t('kpi.activeAlerts'),
      value: activeAlerts,
      change: activeAlerts > 5
        ? { value: `${activeAlerts} active`, positive: false }
        : { value: 'Under control', positive: true },
      target: '',
      icon: 'bell',
      status: activeAlerts <= 3 ? 'ok' : activeAlerts <= 8 ? 'warn' : 'danger',
    },
    {
      id: 'uptime',
      label: t('kpi.uptime'),
      value: '99.7%',
      change: { value: 'SLA: 99.5%', positive: true },
      target: `${t('kpi.target')}: ≥99.5%`,
      icon: 'monitor',
      status: 'info',
    },
  ];

  return (
    <div className="kpi-grid" role="region" aria-label="Key Performance Indicators">
      {cards.map(card => (
        <div key={card.id} className={`kpi-card kpi-${card.status}`} role="article" aria-label={card.label}>
          <div className="kpi-icon" aria-hidden="true">
            <Icon name={card.icon} size={32} />
          </div>
          <div className="kpi-label">{card.label}</div>
          <div className="kpi-value">{card.value}</div>
          <div className={`kpi-change ${card.change.positive ? 'positive' : 'negative'}`}>
            <span aria-hidden="true">{card.change.positive ? '↗' : '↘'}</span>
            {card.change.value}
          </div>
          {card.target && (
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>
              {card.target}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
