import { useTranslation } from 'react-i18next';
import useStore from '../store';
import Icon from './Icon';

export default function QueuePanel({ fullView = false }) {
  const { t } = useTranslation();
  const queueData = useStore(s => s.queueData);

  const getQueueColor = (waitSec) => {
    if (waitSec > 360) return 'var(--status-danger)';
    if (waitSec > 240) return 'var(--status-warn)';
    return 'var(--status-ok)';
  };

  const getQueueFillPct = (qLen) => Math.min(100, (qLen / 12) * 100);

  const formatWait = (seconds) => {
    if (seconds === 0) return t('queue.noWait');
    const min = Math.floor(seconds / 60);
    const sec = Math.floor(seconds % 60);
    return min > 0 ? `${min}m ${sec}s` : `${sec}s`;
  };

  return (
    <div>
      <div className="card-header">
        <div className="card-title">{t('queue.title')}</div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          fontSize: '12px',
        }}>
          <span style={{ color: 'var(--text-muted)' }}>
            {queueData.total_customers} {t('queue.customers')}
          </span>
          <span style={{
            color: getQueueColor(queueData.average_wait_seconds),
            fontWeight: 700,
          }}>
            Avg: {formatWait(queueData.average_wait_seconds)}
          </span>
        </div>
      </div>

      <div className="card-body">
        <div className="queue-lanes" role="list" aria-label="Checkout lane statuses">
          {queueData.lanes.map(lane => {
            const fillColor = getQueueColor(lane.estimated_wait_seconds);
            const fillPct = getQueueFillPct(lane.queue_length);
            const isSCO = lane.lane_type === 'self_checkout';

            return (
              <div
                key={lane.lane_id}
                className="queue-lane"
                role="listitem"
                aria-label={`Lane ${lane.lane_id}: ${lane.is_open ? 'open' : 'closed'}, ${lane.queue_length} customers, wait ${formatWait(lane.estimated_wait_seconds)}`}
              >
                {/* Lane number */}
                <div className={`lane-id ${lane.is_open ? 'lane-open' : 'lane-closed'}`}>
                  {isSCO ? <Icon name="cart" size={20} /> : `L${lane.lane_id}`}
                </div>

                {/* Lane info */}
                <div className="lane-info">
                  <div className="lane-type">
                    {isSCO ? t('queue.selfCheckout') : t('queue.manned')}
                    {lane.cashier_id && (
                      <span style={{ marginLeft: '6px', color: 'var(--text-primary)', fontWeight: 600 }}>
                        · {lane.cashier_id}
                      </span>
                    )}
                  </div>
                  <div className="lane-detail" style={{ color: lane.is_open ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                    {lane.is_open ? (
                      <>
                        {lane.queue_length} {t('queue.customers')}
                      </>
                    ) : (
                      t('queue.closed')
                    )}
                  </div>
                </div>

                {/* Queue bar */}
                {lane.is_open && (
                  <div className="lane-queue-bar" role="progressbar" aria-valuenow={lane.queue_length} aria-valuemax={12}>
                    <div
                      className="lane-queue-fill"
                      style={{
                        width: `${fillPct}%`,
                        background: `linear-gradient(90deg, ${fillColor}, ${fillColor}88)`,
                      }}
                    />
                  </div>
                )}

                {/* Wait time */}
                <div className="lane-wait" style={{ color: lane.is_open ? fillColor : 'var(--text-muted)' }}>
                  {lane.is_open ? formatWait(lane.estimated_wait_seconds) : '—'}
                </div>

                {/* Status badge */}
                <div style={{
                  padding: '3px 8px',
                  borderRadius: 'var(--radius-full)',
                  fontSize: '10px',
                  fontWeight: 700,
                  background: lane.is_open ? 'var(--status-ok-bg)' : 'rgba(100, 116, 139, 0.15)',
                  color: lane.is_open ? 'var(--status-ok)' : 'var(--text-muted)',
                  minWidth: '42px',
                  textAlign: 'center',
                }}>
                  {lane.is_open ? t('queue.open') : t('queue.closed')}
                </div>
              </div>
            );
          })}
        </div>

        {/* Queue summary */}
        {fullView && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '12px',
            marginTop: '24px',
          }}>
            {[
              { label: 'Total in Queue', value: queueData.total_customers, icon: 'queue' },
              { label: 'Avg Wait', value: formatWait(queueData.average_wait_seconds), icon: 'timer' },
              { label: 'Lanes Open', value: queueData.lanes.filter(l => l.is_open).length, icon: 'checkCircle' },
              { label: 'SCO Available', value: queueData.lanes.filter(l => l.lane_type === 'self_checkout' && l.is_open && l.queue_length < 2).length, icon: 'cart' },
            ].map(stat => (
              <div
                key={stat.label}
                style={{
                  background: 'var(--bg-glass)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '16px',
                  textAlign: 'center',
                }}
              >
                <div style={{ marginBottom: '4px', display: 'flex', justifyContent: 'center' }}>
                  <Icon name={stat.icon} size={24} color="var(--accent-primary-light)" />
                </div>
                <div style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-primary)' }}>{stat.value}</div>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', marginTop: '2px' }}>{stat.label}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
