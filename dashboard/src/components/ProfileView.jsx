import { useTranslation } from 'react-i18next';
import useStore from '../store';
import Icon from './Icon';

export default function ProfileView() {
  const { t } = useTranslation();
  const user = useStore(s => s.user);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="card">
        <div className="card-header">
          <div className="card-title">Account Security</div>
        </div>
        <div className="card-body">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Change Password</div>
                <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Ensure your account is using a long, random password to stay secure.</div>
              </div>
              <button style={{
                  background: 'var(--bg-glass)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-medium)',
                  borderRadius: 'var(--radius-md)',
                  padding: '8px 16px',
                  fontFamily: 'var(--font-family)',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}>
                Update Password
              </button>
            </div>
            
            <div style={{ borderTop: '1px solid var(--border-subtle)' }}></div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
               <div>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Two-Factor Authentication (2FA)</div>
                <div style={{ fontSize: '13px', color: 'var(--text-muted)', maxWidth: '400px' }}>Add an extra layer of security to your account. We recommend using a biometric setup alongside SMS.</div>
              </div>
              <button style={{
                  background: 'var(--accent-primary)',
                  color: 'white',
                  border: 'none',
                  borderRadius: 'var(--radius-md)',
                  padding: '8px 16px',
                  fontFamily: 'var(--font-family)',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}>
                Enable 2FA
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title">Linked Accounts</div>
        </div>
        <div className="card-body">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
             <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '16px',
                background: 'var(--status-info-bg)',
                border: '1px solid var(--accent-primary-light)',
                borderRadius: 'var(--radius-md)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '50%',
                    background: 'var(--accent-primary)',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700
                  }}>
                    {user.name.charAt(0)}
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '14px', color: 'var(--accent-primary)' }}>{user.name} ({user.role})</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 600 }}>{user.email} &mdash; Current Session</div>
                  </div>
                </div>
             </div>

             <div style={{
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
                    borderRadius: '50%',
                    background: 'var(--bg-secondary)',
                    color: 'var(--text-secondary)',
                    border: '1px solid var(--border-medium)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    SM
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-primary)' }}>Store Manager (Secondary)</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>manager-082@smartstore.com</div>
                  </div>
                </div>
                <button style={{
                    background: 'transparent',
                    border: '1px solid var(--border-medium)',
                    color: 'var(--text-secondary)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '6px 12px',
                    fontSize: '11px',
                    fontWeight: 700,
                    cursor: 'pointer'
                  }}>
                  Switch
                </button>
             </div>

             <button style={{
                  background: 'transparent',
                  border: '1px dashed var(--border-subtle)',
                  color: 'var(--text-muted)',
                  borderRadius: 'var(--radius-md)',
                  padding: '16px',
                  fontFamily: 'var(--font-family)',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  marginTop: '16px'
                }}>
                <Icon name="search" size={16} /> Link Another Account
              </button>
          </div>
        </div>
      </div>
    </div>
  );
}
