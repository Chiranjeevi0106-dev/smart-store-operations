import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import useStore from './store';
import { useWebSocket } from './useWebSocket';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import KPICards from './components/KPICards';
import ShelfHeatmap from './components/ShelfHeatmap';
import QueuePanel from './components/QueuePanel';
import AlertsPanel from './components/AlertsPanel';
import MultiStoreView from './components/MultiStoreView';
import CameraView from './components/CameraView';
import InventoryTable from './components/InventoryTable';
import ReportsView from './components/ReportsView';
import SettingsView from './components/SettingsView';
import ProfileView from './components/ProfileView';
import Icon from './components/Icon';
import Login from './components/Login';

export default function App() {
  const { t } = useTranslation();
  const isAuthenticated = useStore(s => s.isAuthenticated);
  const activeView = useStore(s => s.activeView);
  const theme = useStore(s => s.theme);
  const selectedStoreId = useStore(s => s.selectedStoreId);
  const currentRole = useStore(s => s.currentRole);

  // Theme sync
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Connect WebSocket
  useWebSocket(selectedStoreId);

  // If not authenticated, force the login screen
  if (!isAuthenticated) {
    return <Login />;
  }

  // Role-based view filtering
  const canView = (view) => {
    const roleViews = {
      admin: ['overview', 'shelf', 'queue', 'alerts', 'lp', 'reports', 'stores', 'settings', 'profile'],
      store_manager: ['overview', 'shelf', 'queue', 'alerts', 'lp', 'reports', 'stores', 'profile'],
      cashier: ['queue', 'profile'],
      lp_officer: ['alerts', 'lp', 'profile'],
    };
    return (roleViews[currentRole] || roleViews.admin).includes(view);
  };

  const renderView = () => {
    if (!canView(activeView)) {
      return (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
          <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
            <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'center' }}>
              <Icon name="lock" size={48} color="var(--text-muted)" />
            </div>
            <h3 style={{ color: 'var(--text-secondary)' }}>Access Restricted</h3>
            <p>Your role doesn't have access to this view.</p>
          </div>
        </div>
      );
    }

    switch (activeView) {
      case 'overview':
        return <OverviewDashboard />;
      case 'shelf':
        return (
          <div className="dashboard-grid">
            <CameraView />
            <div className="card">
              <ShelfHeatmap />
            </div>
          </div>
        );
      case 'queue':
        return (
          <div>
            <QueuePanel fullView />
          </div>
        );
      case 'alerts':
      case 'lp':
        return (
          <div>
            <AlertsPanel fullView filterType={activeView === 'lp' ? 'lp' : null} />
          </div>
        );
      case 'stores':
        return <MultiStoreView />;
      case 'profile':
        return <ProfileView />;
      case 'reports':
        return <ReportsView />;
      case 'settings':
        return <SettingsView />;
      default:
        return <OverviewDashboard />;
    }
  };

  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-content">
        <Header />
        <div className="page-content">
          {renderView()}
        </div>
      </div>
    </div>
  );
}

function OverviewDashboard() {
  return (
    <>
      <KPICards />
      <div className="dashboard-grid">
        <CameraView />
        <div className="card">
          <ShelfHeatmap />
        </div>
        <div className="card full-width">
          <InventoryTable />
        </div>
        <div className="card full-width">
          <AlertsPanel />
        </div>
      </div>
    </>
  );
}
