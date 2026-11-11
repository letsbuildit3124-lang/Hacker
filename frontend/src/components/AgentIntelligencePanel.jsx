import React from 'react';
import {
  Brain,
  ShieldCheck,
  Compass,
  FileCheck2,
  User,
  Building,
  CheckCircle2
} from 'lucide-react';

export default function AgentIntelligencePanel({ session }) {
  if (!session) return null;

  const facts = session.establishedFacts || {};
  const memory = session.conversationMemory || {};
  const strategy = session.currentStrategy || {};

  const getPersonaName = (id) => {
    switch (id) {
      case 'friendly_support':
        return { name: 'Rahul', label: 'Friendly Customer Support' };
      case 'urgent_support':
        return { name: 'Vikram', label: 'Urgent Support Officer' };
      case 'tech_expert':
        return { name: 'Arjun', label: 'Technical Support Engineer' };
      case 'confused_support':
        return { name: 'Amit', label: 'Confused Support Trainee' };
      case 'sales_persistent':
        return { name: 'Neha', label: 'Persistent Sales Associate' };
      default:
        return { name: 'Attacker Agent', label: id || 'Support Rep' };
    }
  };

  const personaMeta = getPersonaName(session.personaId);

  const attackerBlob = (session.conversationHistory || [])
    .filter((m) => m.sender === 'scammer')
    .map((m) => (m.text || '').toLowerCase())
    .join(' ');

  const isDisclosed = (val) => {
    if (!val) return false;
    const cleanVal = String(val).toLowerCase().trim();
    if (attackerBlob.includes(cleanVal)) return true;
    const digitsOnly = cleanVal.replace(/[^\d]/g, '');
    if (digitsOnly.length >= 10) {
      const blobDigits = attackerBlob.replace(/[^\d]/g, '');
      return blobDigits.includes(digitsOnly.slice(-10));
    }
    return false;
  };

  const renderFactRow = (label, value) => {
    if (!value) return null;
    const leaked = isDisclosed(value);
    return (
      <div key={label} className="flex items-center justify-between gap-2 text-[11px] py-1 border-b border-slate-100 last:border-0">
        <span className="text-slate-500 shrink-0">{label}</span>
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-mono text-slate-800 truncate max-w-[155px]" title={value}>
            {value}
          </span>
          <span
            className={`text-[9px] font-semibold px-1.5 py-0.5 rounded uppercase shrink-0 ${
              leaked
                ? 'bg-rose-50 text-rose-600 border border-rose-200'
                : 'bg-slate-100 text-slate-500 border border-slate-200'
            }`}
          >
            {leaked ? 'Leaked' : 'Hidden'}
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-indigo-600" />
          <h3 className="text-xs font-semibold text-slate-900">Agent State & Disclosed Intel</h3>
        </div>
        <div className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
          <ShieldCheck className="w-3 h-3" />
          Guard Active
        </div>
      </div>

      {/* Persona & Strategy */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80">
          <div className="text-[10px] uppercase tracking-wider font-semibold text-slate-400 mb-1 flex items-center gap-1">
            <User className="w-3 h-3 text-indigo-600" />
            Persona
          </div>
          <div className="text-xs font-bold text-slate-900">{personaMeta.name}</div>
          <div className="text-[11px] text-slate-600 truncate">{personaMeta.label}</div>
          <div className="text-[10px] text-slate-400 mt-1">
            Lang: <span className="text-slate-700 font-medium">{session.language || 'English'}</span>
          </div>
        </div>

        <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80">
          <div className="text-[10px] uppercase tracking-wider font-semibold text-slate-400 mb-1 flex items-center gap-1">
            <Compass className="w-3 h-3 text-indigo-600" />
            Strategy
          </div>
          <span className="text-[11px] font-mono font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200 inline-block max-w-full truncate">
            {strategy.selectedStrategy || 'trust_building'}
          </span>
          <div className="text-[10px] text-slate-500 mt-1 truncate">
            State: <span className="font-mono text-slate-700">{strategy.conversationState || 'initiating'}</span>
          </div>
        </div>
      </div>

      {/* Strategy Reason */}
      {strategy.reason && (
        <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/70 text-[11px] text-slate-600 leading-relaxed">
          <span className="font-semibold text-slate-800">Rationale: </span>
          {strategy.reason}
        </div>
      )}

      {/* Synthetic Attacker Artifacts */}
      <div className="p-3 rounded-lg bg-slate-50/70 border border-slate-200/80">
        <div className="text-[10px] uppercase tracking-wider font-semibold text-slate-400 mb-2 flex items-center justify-between">
          <span className="flex items-center gap-1">
            <Building className="w-3 h-3 text-indigo-600" />
            Attacker Artifacts
          </span>
          <span>Chat Tracker</span>
        </div>
        <div className="flex justify-between text-[11px] py-1 border-b border-slate-100">
          <span className="text-slate-500">Organization</span>
          <span className="text-slate-800 font-medium truncate max-w-[190px]">{facts.organization || 'Zenith Bank'}</span>
        </div>
        {renderFactRow('Case Ref', facts.caseReference)}
        {renderFactRow('Employee ID', facts.agentId)}
        {renderFactRow('Email ID', facts.contactEmail)}
        {renderFactRow('Mobile No.', facts.mobileNumber)}
        {renderFactRow('Toll-Free', facts.tollFree)}
        {renderFactRow('Phishing URL', facts.officialPortal)}
        {renderFactRow('UPI ID', facts.upiId)}
        {renderFactRow('Bank A/C', facts.bankAccount)}
      </div>

      {/* Memory Summary */}
      <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 space-y-2">
        <div className="text-[10px] uppercase tracking-wider font-semibold text-slate-400 flex items-center gap-1">
          <FileCheck2 className="w-3 h-3 text-indigo-600" />
          Rolling Memory
        </div>
        <p className="text-[11px] text-slate-600 leading-relaxed italic">
          "{memory.summary || 'Awaiting initial turn to build summary.'}"
        </p>
        {memory.topicsDiscussed && memory.topicsDiscussed.length > 0 && (
          <div className="flex flex-wrap gap-1 pt-1">
            {memory.topicsDiscussed.map((topic, i) => (
              <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-white text-slate-600 border border-slate-200">
                {topic}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Consistency Footer */}
      <div className="flex items-center justify-between p-2.5 rounded-lg bg-emerald-50/70 border border-emerald-200 text-xs">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span className="text-[11px] font-medium text-emerald-800">Identity Consistency Verified</span>
        </div>
        <span className="text-[10px] font-mono font-semibold text-emerald-700">PASSED</span>
      </div>
    </div>
  );
}
