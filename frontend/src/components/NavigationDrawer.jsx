import React, { useEffect, useRef } from 'react';
import { X, ShieldAlert } from 'lucide-react';

export default function NavigationDrawer({
  isOpen,
  onClose,
  groups,
  activeTab,
  onSelectTab,
  backendHealth
}) {
  const dialogRef = useRef(null);
  const sheetRef = useRef(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen && !dialog.open) {
      dialog.showModal();
    } else if (!isOpen && dialog.open) {
      dialog.close();
    }
  }, [isOpen]);

  const handleBackdropClick = (e) => {
    if (sheetRef.current && !sheetRef.current.contains(e.target)) {
      onClose();
    }
  };

  const handleSelect = (tabId) => {
    onSelectTab(tabId);
    onClose();
  };

  return (
    <dialog
      ref={dialogRef}
      id="main-nav-drawer"
      aria-label="Platform Navigation"
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      onClick={handleBackdropClick}
      className="nav-drawer"
    >
      <div
        ref={sheetRef}
        className="h-full w-full bg-white border-r border-slate-200 shadow-2xl flex flex-col justify-between overflow-hidden"
      >
        {/* Drawer Header */}
        <div>
          <div className="h-14 px-4 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-sm">
                <ShieldAlert className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-bold text-slate-900 leading-tight">Honeypot Studio</div>
                <div className="text-[10px] text-slate-500">Red-Team Simulator</div>
              </div>
            </div>
            <button
              type="button"
              onClick={onClose}
              autoFocus
              aria-label="Close navigation menu"
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Navigation Groups */}
          <nav className="p-3 space-y-5 overflow-y-auto overscroll-contain max-h-[calc(100svh-120px)]">
            {groups.map((group) => (
              <div key={group.title}>
                <div className="px-3 mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                  {group.title}
                </div>
                <ul className="space-y-0.5">
                  {group.items.map((item) => {
                    const Icon = item.icon;
                    const isActive = activeTab === item.id;
                    return (
                      <li key={item.id}>
                        <button
                          type="button"
                          onClick={() => handleSelect(item.id)}
                          aria-current={isActive ? 'page' : undefined}
                          className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                            isActive
                              ? 'bg-indigo-50 text-indigo-700 font-semibold'
                              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                          }`}
                        >
                          <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-indigo-600' : 'text-slate-400'}`} />
                          <span className="truncate">{item.label}</span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </nav>
        </div>

        {/* Minimal Footer Status inside Drawer */}
        <div className="p-3.5 border-t border-slate-100 bg-slate-50/70">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-500">System API</span>
            <span className="inline-flex items-center gap-1.5 font-medium text-slate-700">
              <span className={`w-2 h-2 rounded-full ${backendHealth?.status === 'healthy' ? 'bg-emerald-500' : 'bg-rose-500'}`} />
              {backendHealth?.status === 'healthy' ? 'Connected' : 'Offline'}
            </span>
          </div>
          {backendHealth?.llm_model && (
            <div className="flex items-center justify-between text-[10px] text-slate-400 mt-1">
              <span>Model</span>
              <span className="font-mono truncate max-w-[160px]">{backendHealth.llm_model}</span>
            </div>
          )}
        </div>
      </div>
    </dialog>
  );
}
