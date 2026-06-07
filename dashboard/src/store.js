import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://smart-store-api-bzz2.onrender.com'

const INITIAL_STORES = [
  { store_id: 'IND-BGR-082', store_name: 'Reliance Fresh - Indiranagar' },
  { store_id: 'IND-MUM-112', store_name: 'Reliance Fresh - Bandra West' },
  { store_id: 'IND-DEL-401', store_name: 'Reliance Smart - Connaught Place' },
  { store_id: 'IND-HYD-205', store_name: 'Reliance Fresh - Jubilee Hills' },
  { store_id: 'IND-CHE-309', store_name: 'Reliance Smart - T-Nagar' }
];

const useStore = create(persist((set, get) => ({
  // ── User & Auth ──
  isAuthenticated: false,
  user: { user_id: 'admin-001', role: 'admin', name: 'Admin User', email: 'admin@smartstore.com' },
  currentRole: 'admin',
  accounts: {
    'admin@smartstore.com': { password: 'password123', role: 'admin', name: 'Admin Manager' },
    'cashier@smartstore.com': { password: 'password123', role: 'cashier', name: 'Front Desk' }
  },
  login: (email, password) => {
    // Strict Mock Authentication
    const targetAccount = get().accounts[email.toLowerCase()];
    if (targetAccount && targetAccount.password === password) {
      set({ 
        isAuthenticated: true, 
        user: { user_id: 'user-' + Date.now(), role: targetAccount.role, name: targetAccount.name, email: email },
        currentRole: targetAccount.role,
      });
      return true;
    }
    return false;
  },
  signup: (email, password, name, role) => {
    const emailLower = email.toLowerCase();
    if (get().accounts[emailLower]) {
      return false; // Account exists
    }
    
    // Add to mock registry
    set(state => ({
      accounts: {
        ...state.accounts,
        [emailLower]: { password, role, name }
      }
    }));
    return true;
  },
  logout: () => set({ isAuthenticated: false }),
  setRole: (role) => set({ currentRole: role }),

  // ── Store Selection ──
  stores: INITIAL_STORES,
  selectedStoreId: 'IND-BGR-082',
  setSelectedStore: (id) => {
    set({ selectedStoreId: id });
    get().refreshData();
  },

  // ── Navigation ──
  activeView: 'overview',
  setActiveView: (view) => set({ activeView: view }),

  // ── Data State ──
  theme: 'light',
  toggleTheme: () => set(state => ({ theme: state.theme === 'light' ? 'dark' : 'light' })),
  shelfData: { items: [], total_facings: 0, empty_facings: 0, stockout_rate: 0, planogram_compliance: 0 },
  queueData: { total_customers: 0, average_wait_seconds: 0, lanes: [] },
  alerts: [],
  multiStoreKPIs: [],
  isLoading: false,
  error: null,

  // ── WebSocket ──
  wsConnected: false,
  setWsConnected: (v) => set({ wsConnected: v }),

  // ── Actions ──
  fetchShelfData: async () => {
    const { selectedStoreId } = get();
    try {
      const res = await fetch(`${API_BASE_URL}/stores/${selectedStoreId}/shelf-status`);
      const data = await res.json();
      set({ shelfData: data });
    } catch (err) {
      console.error('Failed to fetch shelf data', err);
    }
  },

  fetchQueueData: async () => {
    const { selectedStoreId } = get();
    try {
      const res = await fetch(`${API_BASE_URL}/stores/${selectedStoreId}/queue-status`);
      const data = await res.json();
      set({ queueData: { 
        total_customers: data.total_customers_in_queue,
        average_wait_seconds: data.average_wait_seconds,
        lanes: data.lanes
      }});
    } catch (err) {
      console.error('Failed to fetch queue data', err);
    }
  },

  fetchMultiStoreKPIs: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/reports/multi-store-kpis`);
      const data = await res.json();
      set({ multiStoreKPIs: data.stores });
    } catch (err) {
      console.error('Failed to fetch KPIs', err);
    }
  },

  acknowledgeAlert: async (alertId) => {
    const { selectedStoreId } = get();
    try {
      await fetch(`${API_BASE_URL}/stores/${selectedStoreId}/alerts/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alert_id: alertId, officer_id: 'admin', action: 'acknowledge' })
      });
      set(state => ({
        alerts: state.alerts.map(a => a.id === alertId ? { ...a, acknowledged: true } : a)
      }));
    } catch (err) {
      console.error('Failed to acknowledge alert', err);
    }
  },

  dismissAlert: (alertId) => set(state => ({
    alerts: state.alerts.filter(a => a.id !== alertId)
  })),

  addAlert: (alert) => set(state => {
    const exists = state.alerts.find(a => a.id === alert.id);
    if (exists) return state;
    return { alerts: [alert, ...state.alerts].slice(0, 50) };
  }),

  refreshData: () => {
    get().fetchShelfData();
    get().fetchQueueData();
    get().fetchMultiStoreKPIs();
  }
}), {
  name: 'smartstore-auth-storage',
  partialize: (state) => ({
    accounts: state.accounts,
    isAuthenticated: state.isAuthenticated,
    user: state.user,
    currentRole: state.currentRole,
    theme: state.theme
  })
}));

// Initialize data
useStore.getState().refreshData();

// Periodic refresh (fallback if WebSockets miss something)
setInterval(() => {
  useStore.getState().refreshData();
}, 60000);

export default useStore;
