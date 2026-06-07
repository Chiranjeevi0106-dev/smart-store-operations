import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import useStore from '../store';
import Icon from './Icon';

export default function MultiStoreView() {
  const { t } = useTranslation();
  const kpis = useStore(s => s.multiStoreKPIs);

  const sortedByStockout = useMemo(
    () => [...kpis].sort((a, b) => a.stockout_rate - b.stockout_rate),
    [kpis]
  );

  const chainAvg = useMemo(() => ({
    stockout: (kpis.reduce((s, k) => s + k.stockout_rate, 0) / kpis.length * 100).toFixed(1),
    queue: (kpis.reduce((s, k) => s + k.avg_queue_wait_seconds, 0) / kpis.length / 60).toFixed(1),
    shrinkage: (kpis.reduce((s, k) => s + k.shrinkage_pct, 0) / kpis.length).toFixed(2),
    compliance: (kpis.reduce((s, k) => s + k.planogram_compliance, 0) / kpis.length * 100).toFixed(1),
    uptime: (kpis.reduce((s, k) => s + k.system_uptime_pct, 0) / kpis.length).toFixed(2),
  }), [kpis]);

  const getStatusColor = (value, thresholds) => {
    if (value <= thresholds[0]) return 'var(--status-ok)';
    if (value <= thresholds[1]) return 'var(--status-warn)';
    return 'var(--status-danger)';
  };

  return (
    <div>
      {/* Chain-wide summary */}
      <div className="kpi-grid" style={{ marginBottom: '32px' }}>
        {[
          { label: 'Chain Stockout Rate', value: `${chainAvg.stockout}%`, icon: 'stockout', status: chainAvg.stockout <= 5.3 ? 'ok' : 'warn' },
          { label: 'Chain Avg Queue Wait', value: `${chainAvg.queue}m`, icon: 'timer', status: chainAvg.queue <= 4.9 ? 'ok' : 'warn' },
          { label: 'Chain Shrinkage', value: `${chainAvg.shrinkage}%`, icon: 'shield', status: chainAvg.shrinkage <= 1.68 ? 'ok' : 'warn' },
          { label: 'Chain Compliance', value: `${chainAvg.compliance}%`, icon: 'clipboard', status: chainAvg.compliance >= 90 ? 'ok' : 'warn' },
          { label: 'Avg Uptime', value: `${chainAvg.uptime}%`, icon: 'monitor', status: 'info' },
        ].map(card => (
          <div key={card.label} className={`kpi-card kpi-${card.status}`}>
            <div className="kpi-icon"><Icon name={card.icon} size={32} /></div>
            <div className="kpi-label">{card.label}</div>
            <div className="kpi-value">{card.value}</div>
          </div>
        ))}
      </div>

      {/* Store comparison table */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">Multi-Store Benchmarking</div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Ranked by stockout rate (best → worst)
          </span>
        </div>
        <div className="card-body" style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }} role="table">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                {['Rank', 'Store', 'Stockout Rate', 'Avg Queue Wait', 'Shrinkage', 'Compliance', 'Active Alerts', 'Uptime'].map(h => (
                  <th key={h} style={{
                    padding: '10px 12px',
                    textAlign: 'left',
                    fontSize: '10px',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.8px',
                    color: 'var(--text-muted)',
                  }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedByStockout.map((store, idx) => (
                <tr
                  key={store.store_id}
                  style={{
                    borderBottom: '1px solid var(--border-subtle)',
                    transition: 'background var(--transition-fast)',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-glass-hover)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <td style={{ padding: '12px', fontWeight: 800, color: idx === 0 ? 'var(--status-ok)' : 'var(--text-primary)' }}>
                    {idx === 0 ? '#1' : `#${idx + 1}`}
                  </td>
                  <td style={{ padding: '12px' }}>
                    <div style={{ fontWeight: 600 }}>{store.store_name}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{store.store_id}</div>
                  </td>
                  <td style={{ padding: '12px' }}>
                    <span style={{
                      color: getStatusColor(store.stockout_rate * 100, [5.3, 8]),
                      fontWeight: 700,
                    }}>
                      {(store.stockout_rate * 100).toFixed(1)}%
                    </span>
                    <BarIndicator value={store.stockout_rate * 100} max={12} color={getStatusColor(store.stockout_rate * 100, [5.3, 8])} />
                  </td>
                  <td style={{ padding: '12px' }}>
                    <span style={{
                      color: getStatusColor(store.avg_queue_wait_seconds / 60, [4.9, 6.8]),
                      fontWeight: 700,
                    }}>
                      {(store.avg_queue_wait_seconds / 60).toFixed(1)}m
                    </span>
                    <BarIndicator value={store.avg_queue_wait_seconds / 60} max={10} color={getStatusColor(store.avg_queue_wait_seconds / 60, [4.9, 6.8])} />
                  </td>
                  <td style={{ padding: '12px' }}>
                    <span style={{
                      color: getStatusColor(store.shrinkage_pct, [1.68, 2.8]),
                      fontWeight: 700,
                    }}>
                      {store.shrinkage_pct}%
                    </span>
                  </td>
                  <td style={{ padding: '12px' }}>
                    <span style={{
                      color: store.planogram_compliance >= 0.9 ? 'var(--status-ok)' : store.planogram_compliance >= 0.75 ? 'var(--status-warn)' : 'var(--status-danger)',
                      fontWeight: 700,
                    }}>
                      {(store.planogram_compliance * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td style={{ padding: '12px' }}>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-full)',
                      fontSize: '11px',
                      fontWeight: 700,
                      background: store.active_alerts > 5 ? 'var(--status-danger-bg)' : 'var(--status-ok-bg)',
                      color: store.active_alerts > 5 ? 'var(--status-danger)' : 'var(--status-ok)',
                    }}>
                      {store.active_alerts}
                    </span>
                  </td>
                  <td style={{ padding: '12px', color: 'var(--status-ok)', fontWeight: 600 }}>
                    {store.system_uptime_pct}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function BarIndicator({ value, max, color }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div style={{
      width: '80px',
      height: '4px',
      background: 'var(--bg-primary)',
      borderRadius: 'var(--radius-full)',
      marginTop: '4px',
      overflow: 'hidden',
    }}>
      <div style={{
        width: `${pct}%`,
        height: '100%',
        background: color,
        borderRadius: 'var(--radius-full)',
        transition: 'width var(--transition-base)',
      }} />
    </div>
  );
}
