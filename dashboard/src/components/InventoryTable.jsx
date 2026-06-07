import useStore from '../store';
import Icon from './Icon';

export default function InventoryTable() {
  const shelfData = useStore(s => s.shelfData);
  
  // Categorize for better layout
  const sortedItems = [...shelfData.items].sort((a, b) => {
    if (a.status === 'empty_facing' && b.status !== 'empty_facing') return -1;
    if (a.status !== 'empty_facing' && b.status === 'empty_facing') return 1;
    return 0;
  });

  const uniqueProducts = [];
  const seen = new Set();
  for (const item of sortedItems) {
    if (!seen.has(item.product_id)) {
      uniqueProducts.push(item);
      seen.add(item.product_id);
    }
  }

  const displayedProducts = uniqueProducts.slice(0, 15);

  const getFallbackImage = (category, idx) => {
    const categoryMaps = {
      'Dairy': 'https://images.unsplash.com/photo-1550583760-5868a05ecf7f?auto=format&fit=crop&q=80&w=300',
      'Produce': 'https://images.unsplash.com/photo-1610832958506-aa56368176cf?auto=format&fit=crop&q=80&w=300',
      'Staples': 'https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&q=80&w=300',
      'Snacks': 'https://images.unsplash.com/photo-1599490659213-e2b9527bb087?auto=format&fit=crop&q=80&w=300',
      'Personal Care': 'https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&q=80&w=300',
      'Household': 'https://images.unsplash.com/photo-1584622650111-993a426fbf0a?auto=format&fit=crop&q=80&w=300',
      'Beverages': 'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&q=80&w=300',
      'Bakery': 'https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&q=80&w=300',
      'Instant Food': 'https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&q=80&w=300'
    };
    return categoryMaps[category] || `https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&q=80&w=300`;
  };

  const handleImageError = (e, category) => {
    e.target.src = getFallbackImage(category, 0);
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Icon name="cart" size={16} color="var(--accent-primary)" />
          Live Product Inventory Showcase
        </div>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          Showing {displayedProducts.length} of {uniqueProducts.length} unique SKUs
        </div>
      </div>
      <div className="product-grid" style={{ maxHeight: '600px', overflowY: 'auto' }}>
        {displayedProducts.map((item, idx) => (
          <div key={idx} className="product-card">
            <div className="product-image">
              <img 
                src={item.image || getFallbackImage(item.category, idx)} 
                alt={item.product_name} 
                loading="lazy"
                onError={(e) => handleImageError(e, item.category)}
              />
              {item.status === 'empty_facing' && (
                <div style={{
                  position: 'absolute',
                  inset: 0,
                  background: 'rgba(239, 68, 68, 0.1)',
                  backdropFilter: 'grayscale(1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyChild: 'center'
                }} />
              )}
            </div>
            <div className="product-info">
              <div className="product-meta">{item.category}</div>
              <div className="product-name">{item.product_name}</div>
              <div className="product-footer">
                <span className={`product-status-tag ${item.status === 'empty_facing' ? 'status-oos' : 'status-in-stock'}`}>
                  {item.status === 'empty_facing' ? 'Out of Stock' : 'In Stock'}
                </span>
                <span style={{ fontSize: '12px', fontWeight: 800, color: 'var(--text-primary)' }}>
                  ₹{item.price || '—'}
                </span>
              </div>
              <div style={{ marginTop: '8px', fontSize: '10px', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
                <span>Aisle {item.aisle}</span>
                <span>Bay {item.bay}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
