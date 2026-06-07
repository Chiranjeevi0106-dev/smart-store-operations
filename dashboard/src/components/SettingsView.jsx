import { useTranslation } from 'react-i18next';
import useStore from '../store';
import Icon from './Icon';

export default function SettingsView() {
  const { t } = useTranslation();
  const theme = useStore(s => s.theme);
  const setTheme = useStore(s => s.setTheme);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="card">
        <div className="card-header">
          <div className="card-title">Preferences</div>
        </div>
        <div className="card-body">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Interface Theme</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Choose between light or dark mode.</div>
              </div>
              <select
                value={theme}
                onChange={e => setTheme(e.target.value)}
                style={{
                  background: 'var(--bg-glass)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-medium)',
                  borderRadius: 'var(--radius-md)',
                  padding: '8px 12px',
                  fontFamily: 'var(--font-family)',
                  fontSize: '13px',
                  outline: 'none',
                  cursor: 'pointer'
                }}
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </select>
            </div>
            <div style={{ borderTop: '1px solid var(--border-subtle)' }}></div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Desktop Notifications</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Receive alerts for high-priority events.</div>
              </div>
              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                <input type="checkbox" defaultChecked style={{ width: '18px', height: '18px', accentColor: 'var(--accent-primary)' }} />
              </label>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title">Camera Intelligence Configurations</div>
        </div>
        <div className="card-body">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>Global Detection Confidence Threshold</div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px' }}>Adjust the minimum AI confidence required before registering a stockout or queue event. High confidence prevents false positives but may delay detections.</div>
              <input type="range" min="0" max="100" defaultValue="85" style={{ width: '100%', accentColor: 'var(--accent-primary)' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', fontWeight: 600 }}>
                <span>Faster detection</span>
                <span>85% Current Threshold</span>
                <span>Higher accuracy</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
