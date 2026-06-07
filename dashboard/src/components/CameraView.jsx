import { useState, useEffect, useRef } from 'react';
import useStore from '../store';
import Icon from './Icon';

export default function CameraView() {
  const selectedStoreId = useStore(s => s.selectedStoreId);
  const shelfData = useStore(s => s.shelfData);
  const [isVideoLoaded, setIsVideoLoaded] = useState(false);
  const videoRef = useRef(null);

  // Filter alerts for the current store that have low confidence or are OOS
  const detections = shelfData.items.slice(0, 8).map((item, idx) => ({
    id: idx,
    x: 10 + (idx % 4) * 22,
    y: 10 + Math.floor(idx / 4) * 40,
    width: 18,
    height: 35,
    label: item.product_name,
    status: item.status,
    confidence: item.fused_confidence
  }));

  return (
    <div className="card" style={{ height: '100%', minHeight: '500px' }}>
      <div className="card-header">
        <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Icon name="monitor" size={16} color="var(--accent-primary)" />
          AI Vision Feed — AISLE A1
        </div>
        <div className="live-indicator">
          <div className="live-dot"></div>
          {selectedStoreId} — 4K STREAM
        </div>
      </div>
      <div className="card-body" style={{ padding: 0, position: 'relative', overflow: 'hidden', minHeight: '340px', background: '#000' }}>
        {/* Actual Store AI Snapshot */}
        <img 
          src={`/snapshots/A1.png`}
          alt="Store AI Feed"
          style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.8 }}
          onLoad={() => setIsVideoLoaded(true)}
        />

        {!isVideoLoaded && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
            <div className="live-dot" style={{ marginRight: '8px' }}></div> Fetching Camera Snapshots...
          </div>
        )}

        {/* AI Overlay (Bounding Boxes) */}
        <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
          {detections.map(det => (
            <div 
              key={det.id}
              style={{
                position: 'absolute',
                left: `${det.x}%`,
                top: `${det.y}%`,
                width: `${det.width}%`,
                height: `${det.height}%`,
                border: `2px solid ${det.status === 'empty_facing' ? 'var(--status-danger)' : 'var(--status-ok)'}`,
                boxShadow: det.status === 'empty_facing' ? '0 0 10px rgba(239, 68, 68, 0.4)' : '0 0 10px rgba(34, 197, 94, 0.4)',
                borderRadius: '4px',
                transition: 'all 0.5s ease'
              }}
            >
              <div style={{
                position: 'absolute',
                top: '-20px',
                left: '-2px',
                background: det.status === 'empty_facing' ? 'var(--status-danger)' : 'var(--status-ok)',
                color: '#fff',
                fontSize: '9px',
                fontWeight: 700,
                padding: '2px 5px',
                borderRadius: '2px 2px 0 0',
                whiteSpace: 'nowrap',
                maxWidth: '120px',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}>
                {det.label} ({(det.confidence * 100).toFixed(0)}%)
              </div>
            </div>
          ))}
        </div>

        {/* CV Metrics HUD */}
        <div style={{
          position: 'absolute',
          bottom: '16px',
          left: '16px',
          background: 'rgba(0,0,0,0.6)',
          backdropFilter: 'blur(8px)',
          borderRadius: 'var(--radius-md)',
          padding: '12px',
          border: '1px solid rgba(255,255,255,0.1)',
          color: '#fff',
          fontSize: '11px',
          minWidth: '200px'
        }}>
          <div style={{ marginBottom: '8px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--accent-cyan)' }}>AI Engine Output</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
            <span>Inference Time:</span>
            <span style={{ color: 'var(--status-ok)', fontFamily: 'var(--font-mono)' }}>12.4ms</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
            <span>Model:</span>
            <span>YOLOv9m-Shelf</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Detections:</span>
            <span>{detections.length} Items</span>
          </div>
        </div>
      </div>
    </div>
  );
}
