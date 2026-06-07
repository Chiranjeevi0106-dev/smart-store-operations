import { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import useStore from '../store';

const AISLE_LABELS = ['A1', 'A2', 'A3', 'B1', 'B2', 'C1'];

export default function ShelfHeatmap() {
  const { t } = useTranslation();
  const shelfData = useStore(s => s.shelfData);
  const [selectedAisle, setSelectedAisle] = useState(null);
  const [hoveredCell, setHoveredCell] = useState(null);

  // Aggregate data by aisle and bay for heatmap
  const heatmapData = useMemo(() => {
    const grid = {};
    for (const item of shelfData.items) {
      const key = `${item.aisle}-${item.bay}`;
      if (!grid[key]) {
        grid[key] = { aisle: item.aisle, bay: item.bay, items: [], emptyCount: 0, total: 0 };
      }
      grid[key].items.push(item);
      grid[key].total += 1;
      if (item.status === 'empty_facing') grid[key].emptyCount += 1;
    }
    return grid;
  }, [shelfData.items]);

  const getStatus = (cell) => {
    if (!cell) return 'status-ok';
    const ratio = cell.emptyCount / cell.total;
    if (ratio >= 0.3) return 'status-empty';
    if (ratio >= 0.1) return 'status-warn';
    return 'status-ok';
  };

  const aisles = selectedAisle ? [selectedAisle] : AISLE_LABELS;

  return (
    <div>
      <div className="card-header">
        <div className="card-title">{t('shelf.title')}</div>
        <div style={{ display: 'flex', gap: '4px' }}>
          <button
            className={`alert-btn ${!selectedAisle ? 'active' : ''}`}
            onClick={() => setSelectedAisle(null)}
            style={!selectedAisle ? { background: 'var(--accent-primary)', color: 'white', borderColor: 'var(--accent-primary)' } : {}}
          >
            All
          </button>
          {AISLE_LABELS.map(a => (
            <button
              key={a}
              className={`alert-btn ${selectedAisle === a ? 'active' : ''}`}
              onClick={() => setSelectedAisle(a)}
              style={selectedAisle === a ? { background: 'var(--accent-primary)', color: 'white', borderColor: 'var(--accent-primary)' } : {}}
            >
              {a}
            </button>
          ))}
        </div>
      </div>

      <div className="heatmap-container" role="img" aria-label="Shelf status heatmap showing stock levels by aisle and bay">
        {aisles.map(aisle => (
          <div key={aisle} style={{ marginBottom: '12px' }}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '40px repeat(8, 1fr)',
              gap: '4px',
              alignItems: 'center',
            }}>
              <div className="heatmap-row-label">{aisle}</div>
              {Array.from({ length: 8 }, (_, bay) => {
                const key = `${aisle}-${bay + 1}`;
                const cell = heatmapData[key];
                const status = getStatus(cell);
                const isHovered = hoveredCell === key;

                return (
                  <div
                    key={key}
                    className={`heatmap-cell ${status}`}
                    onMouseEnter={() => setHoveredCell(key)}
                    onMouseLeave={() => setHoveredCell(null)}
                    role="button"
                    aria-label={`${aisle} Bay ${bay + 1}: ${cell ? cell.emptyCount : 0} empty of ${cell ? cell.total : 0}`}
                    tabIndex={0}
                    style={{
                      position: 'relative',
                      aspectRatio: '1',
                    }}
                  >
                    <span style={{ fontSize: '9px' }}>
                      {cell ? `${cell.total - cell.emptyCount}/${cell.total}` : '—'}
                    </span>

                    {/* Tooltip */}
                    {isHovered && cell && (
                      <div style={{
                        position: 'absolute',
                        bottom: '110%',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        background: 'var(--bg-secondary)',
                        border: '1px solid var(--border-medium)',
                        borderRadius: 'var(--radius-md)',
                        padding: '8px 12px',
                        minWidth: '140px',
                        zIndex: 100,
                        fontSize: '11px',
                        boxShadow: 'var(--shadow-lg)',
                        pointerEvents: 'none',
                      }}>
                        <div style={{ fontWeight: 700, marginBottom: '4px' }}>
                          {t('shelf.aisle')} {aisle} · {t('shelf.bay')} {bay + 1}
                        </div>
                        <div style={{ color: 'var(--status-ok)' }}>
                          ✓ {t('shelf.ok')}: {cell.total - cell.emptyCount}
                        </div>
                        <div style={{ color: 'var(--status-danger)' }}>
                          ✗ {t('shelf.empty')}: {cell.emptyCount}
                        </div>
                        <div style={{ color: 'var(--text-muted)', marginTop: '4px' }}>
                          {((1 - cell.emptyCount / cell.total) * 100).toFixed(0)}% stocked
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}

        {/* Bay labels */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '40px repeat(8, 1fr)',
          gap: '4px',
          marginTop: '4px',
        }}>
          <div />
          {Array.from({ length: 8 }, (_, i) => (
            <div key={i} style={{ textAlign: 'center', fontSize: '10px', color: 'var(--text-muted)' }}>
              B{i + 1}
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="heatmap-legend">
          <div className="legend-item">
            <div className="legend-dot" style={{ background: 'rgba(34, 197, 94, 0.5)' }} />
            <span>{t('shelf.ok')} (&gt;90%)</span>
          </div>
          <div className="legend-item">
            <div className="legend-dot" style={{ background: 'rgba(245, 158, 11, 0.5)' }} />
            <span>{t('shelf.warn')} (70-90%)</span>
          </div>
          <div className="legend-item">
            <div className="legend-dot" style={{ background: 'rgba(239, 68, 68, 0.5)' }} />
            <span>{t('shelf.empty')} (&lt;70%)</span>
          </div>
        </div>

        {/* Summary stats */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '32px',
          marginTop: '16px',
          padding: '12px',
          background: 'var(--bg-glass)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)' }}>
              {shelfData.total_facings}
            </div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Total Facings
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--status-danger)' }}>
              {shelfData.empty_facings}
            </div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Empty
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--status-ok)' }}>
              {(shelfData.planogram_compliance * 100).toFixed(1)}%
            </div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Compliance
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
