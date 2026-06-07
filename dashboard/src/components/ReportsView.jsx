import { useTranslation } from 'react-i18next';
import Icon from './Icon';

export default function ReportsView() {
  const { t } = useTranslation();

  const reports = [
    { id: 1, title: 'Weekly Shrinkage Summary', date: '2026-04-10', type: 'PDF', icon: 'shield' },
    { id: 2, title: 'Queue Wait Times Analysis', date: '2026-04-09', type: 'CSV', icon: 'timer' },
    { id: 3, title: 'Planogram Compliance Report', date: '2026-04-07', type: 'PDF', icon: 'clipboard' },
    { id: 4, title: 'Stockout Frequency Log', date: '2026-04-05', type: 'Excel', icon: 'stockout' },
  ];

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <div className="card-title">Generated Reports</div>
          <button style={{
            background: 'var(--accent-primary)',
            color: 'white',
            border: 'none',
            padding: '8px 16px',
            borderRadius: 'var(--radius-sm)',
            fontSize: '12px',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <Icon name="reports" size={16} /> Generate New Report
          </button>
        </div>
        <div className="card-body">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {reports.map(report => (
              <div key={report.id} style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '16px',
                background: 'var(--bg-glass)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--status-info-bg)',
                    color: 'var(--accent-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <Icon name={report.icon} size={20} />
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-primary)' }}>{report.title}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Generated: {report.date}</div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    color: 'var(--text-muted)',
                    background: 'var(--bg-secondary)',
                    padding: '4px 8px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)'
                  }}>{report.type}</span>
                  <button style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--accent-primary-light)',
                    cursor: 'pointer',
                    fontWeight: 600,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}>
                     Download
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
