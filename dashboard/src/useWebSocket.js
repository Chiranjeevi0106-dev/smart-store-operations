import { useEffect, useRef, useCallback } from 'react';
import useStore from './store';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/alerts';
const RECONNECT_DELAYS = [1000, 2000, 4000, 8000, 16000, 30000];

export function useWebSocket(storeId) {
  const wsRef = useRef(null);
  const reconnectAttempt = useRef(0);
  const reconnectTimer = useRef(null);
  const setWsConnected = useStore(s => s.setWsConnected);
  const addAlert = useStore(s => s.addAlert);
  const refreshData = useStore(s => s.refreshData);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const url = `${WS_URL}/${storeId}`;
      const ws = new WebSocket(url);

      ws.onopen = () => {
        setWsConnected(true);
        reconnectAttempt.current = 0;
        ws.send(JSON.stringify({ type: 'ping' }));
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'alert' && msg.data) {
            addAlert({
              id: msg.data.alert_id || `ALT-${Date.now()}`,
              type: msg.data.alert_type,
              icon: getAlertIcon(msg.data.alert_type),
              priority: msg.data.priority || 'normal',
              message: msg.data.message || `Alert: ${msg.data.alert_type}`,
              timestamp: msg.data.timestamp || new Date().toISOString(),
              acknowledged: false,
              store_id: msg.data.store_id || storeId,
              details: msg.data.details,
            });
          } else if (msg.type === 'shelf_update') {
            refreshData();
          } else if (msg.type === 'queue_update') {
            refreshData();
          }
        } catch (e) {
          // Ignore parse errors
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
        scheduleReconnect();
      };

      ws.onerror = () => {
        setWsConnected(false);
      };

      wsRef.current = ws;
    } catch (e) {
      setWsConnected(false);
      scheduleReconnect();
    }
  }, [storeId, setWsConnected, addAlert, refreshData]);

  const scheduleReconnect = useCallback(() => {
    const delay = RECONNECT_DELAYS[
      Math.min(reconnectAttempt.current, RECONNECT_DELAYS.length - 1)
    ];
    reconnectAttempt.current += 1;
    reconnectTimer.current = setTimeout(connect, delay);
  }, [connect]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [storeId, connect]);

  return wsRef;
}

function getAlertIcon(type) {
  const icons = {
    shelf_oos: 'shelfAlert',
    queue_warn: 'queueAlert',
    queue_open: 'laneOpen',
    lp_behaviour: 'lpAlert',
    lp_rfid: 'rfidAlert',
  };
  return icons[type] || 'warning';
}
