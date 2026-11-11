import React from 'react';
import { Activity, CheckCircle2, AlertTriangle, MessageSquare, Layers } from 'lucide-react';

export default function DashboardOverview({ stats }) {
  const cards = [
    { label: 'Total Runs', value: stats.totalSimulations, icon: Layers, iconBg: 'bg-slate-100 text-slate-600' },
    { label: 'Running', value: stats.runningSimulations, icon: Activity, iconBg: 'bg-indigo-50 text-indigo-600', pulsing: stats.runningSimulations > 0 },
    { label: 'Completed', value: stats.completedSimulations, icon: CheckCircle2, iconBg: 'bg-emerald-50 text-emerald-600' },
    { label: 'Failed', value: stats.failedSimulations, icon: AlertTriangle, iconBg: 'bg-rose-50 text-rose-600' },
    { label: 'Messages', value: stats.totalMessages, icon: MessageSquare, iconBg: 'bg-indigo-50 text-indigo-600' }
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {cards.map((card, i) => {
        const Icon = card.icon;
        return (
          <div
            key={i}
            className="bg-white border border-slate-200 rounded-xl px-4 py-3 shadow-xs flex items-center justify-between gap-3"
          >
            <div className="min-w-0">
              <div className="text-[11px] font-medium text-slate-500 truncate">{card.label}</div>
              <div className="text-xl font-bold font-mono tracking-tight text-slate-900 mt-0.5">
                {card.value}
              </div>
            </div>
            <div className={`relative w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${card.iconBg}`}>
              <Icon className="w-4 h-4" />
              {card.pulsing && (
                <span className="absolute -top-0.5 -right-0.5 flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-600"></span>
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
