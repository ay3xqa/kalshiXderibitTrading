import React from 'react';
import {
  LayoutDashboard,
  TrendingUp,
  Calculator,
  Briefcase,
  History,
  Wallet,
  Settings,
} from 'lucide-react';

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, enabled: true },
  { id: 'markets', label: 'Markets', icon: TrendingUp, enabled: true },
  { id: 'calculator', label: 'Calculator', icon: Calculator, enabled: true },
  { type: 'divider' },
  { id: 'portfolio', label: 'Portfolio', icon: Briefcase, enabled: false, badge: 'Soon' },
  { id: 'trades', label: 'Trades', icon: History, enabled: false, badge: 'Soon' },
  { id: 'balance', label: 'Balance', icon: Wallet, enabled: false, badge: 'Soon' },
  { type: 'divider' },
  { id: 'settings', label: 'Settings', icon: Settings, enabled: false, badge: 'Soon' },
];

export default function Sidebar({ activeTab, onTabChange }) {
  return (
    <aside className="sidebar">
      <nav className="sidebar__nav">
        {navItems.map((item, index) => {
          if (item.type === 'divider') {
            return <div key={`divider-${index}`} className="sidebar__divider" />;
          }

          const Icon = item.icon;
          const isActive = activeTab === item.id;
          const isDisabled = !item.enabled;

          return (
            <button
              key={item.id}
              className={`sidebar__item ${isActive ? 'sidebar__item--active' : ''} ${isDisabled ? 'sidebar__item--disabled' : ''}`}
              onClick={() => !isDisabled && onTabChange(item.id)}
              disabled={isDisabled}
            >
              <Icon className="sidebar__item-icon" size={20} />
              <span className="sidebar__item-label">{item.label}</span>
              {item.badge && <span className="sidebar__badge">{item.badge}</span>}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
