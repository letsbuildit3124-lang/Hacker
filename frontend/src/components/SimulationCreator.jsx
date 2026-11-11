import React, { useState } from 'react';
import { Play, Sliders, User, Layers } from 'lucide-react';

export default function SimulationCreator({ onCreateSession, actionLoading }) {
  const [personaId, setPersonaId] = useState('friendly_support');
  const [scenario, setScenario] = useState('fictional_bank_verification');
  const [channel, setChannel] = useState('SMS');
  const [language, setLanguage] = useState('English');
  const [locale, setLocale] = useState('IN');
  const [maxTurns, setMaxTurns] = useState(10);
  const [customInitialMessage, setCustomInitialMessage] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);

  const personas = [
    { id: 'friendly_support', name: 'Rahul', role: 'Friendly Support', desc: 'Polite, patient, warm & conversational.' },
    { id: 'urgent_support', name: 'Vikram', role: 'Urgent Officer', desc: 'Direct, serious, and time-critical.' },
    { id: 'tech_expert', name: 'Arjun', role: 'Tech Support', desc: 'Calm, structured, and technical.' },
    { id: 'confused_support', name: 'Amit', role: 'Confused Trainee', desc: 'Casual, hesitant, mixes Hinglish.' },
    { id: 'sales_persistent', name: 'Neha', role: 'Sales Associate', desc: 'Enthusiastic and persuasive.' }
  ];

  const scenarioOptions = [
    { id: 'fictional_bank_verification', name: 'Bank KYC Verification' },
    { id: 'fictional_upi_payment', name: 'UPI Payment Notification' },
    { id: 'fictional_customer_support', name: 'Customer Support Issue' },
    { id: 'fictional_cashback_notification', name: 'Cashback Reward Claim' },
    { id: 'fictional_account_security', name: 'Account Security Alert' },
    { id: 'fictional_tech_support', name: 'Workstation Tech Support' }
  ];

  const activePersona = personas.find((p) => p.id === personaId) || personas[0];

  const handleSubmit = async (e) => {
    e.preventDefault();
    const payload = {
      scenario,
      personaId,
      channel,
      language,
      locale,
      maxTurns: parseInt(maxTurns, 10),
      initialMessage: customInitialMessage.trim() || undefined
    };
    await onCreateSession(payload);
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-5 shadow-xs space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
        <h2 className="text-sm font-semibold text-slate-900">New Simulation</h2>
        <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700">
          Quick Launch
        </span>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3.5">
        {/* Compact Persona Selector Grid */}
        <div>
          <label className="text-xs font-medium text-slate-700 mb-1.5 flex items-center gap-1.5">
            <User className="w-3.5 h-3.5 text-indigo-600" />
            Attacker Persona
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
            {personas.map((p) => {
              const selected = personaId === p.id;
              return (
                <button
                  type="button"
                  key={p.id}
                  onClick={() => setPersonaId(p.id)}
                  className={`px-2.5 py-2 rounded-lg text-left border transition-colors ${
                    selected
                      ? 'border-indigo-600 bg-indigo-50/80 text-indigo-900'
                      : 'border-slate-200 bg-white hover:bg-slate-50 text-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between gap-1">
                    <span className="text-xs font-semibold truncate">{p.name}</span>
                    {selected && <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 shrink-0" />}
                  </div>
                  <div className="text-[10px] text-slate-500 truncate">{p.role}</div>
                </button>
              );
            })}
          </div>
          <p className="text-[11px] text-slate-500 mt-1.5 px-0.5 truncate">
            <span className="font-medium text-slate-700">{activePersona.name}:</span> {activePersona.desc}
          </p>
        </div>

        {/* Scenario Selector */}
        <div>
          <label className="text-xs font-medium text-slate-700 mb-1 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-indigo-600" />
            Scenario
          </label>
          <select
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100"
          >
            {scenarioOptions.map((opt) => (
              <option key={opt.id} value={opt.id}>
                {opt.name}
              </option>
            ))}
          </select>
        </div>

        {/* Compact Parameters Row */}
        <div className="grid grid-cols-3 gap-2">
          <div>
            <label className="block text-[11px] font-medium text-slate-600 mb-1">Language</label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full bg-white border border-slate-200 rounded-lg px-2 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-indigo-600"
            >
              <option value="English">English</option>
              <option value="Hinglish">Hinglish</option>
              <option value="Hindi">Hindi</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-slate-600 mb-1">Channel</label>
            <select
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
              className="w-full bg-white border border-slate-200 rounded-lg px-2 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-indigo-600"
            >
              <option value="SMS">SMS</option>
              <option value="WhatsApp">WhatsApp</option>
              <option value="Email">Email</option>
              <option value="WebChat">WebChat</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-slate-600 mb-1">Locale</label>
            <select
              value={locale}
              onChange={(e) => setLocale(e.target.value)}
              className="w-full bg-white border border-slate-200 rounded-lg px-2 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-indigo-600"
            >
              <option value="IN">IN</option>
              <option value="US">US</option>
              <option value="UK">UK</option>
            </select>
          </div>
        </div>

        {/* Turn Limit Slider */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <label className="text-[11px] font-medium text-slate-600">Turn Limit</label>
            <span className="text-[11px] font-mono font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">
              {maxTurns} turns
            </span>
          </div>
          <input
            type="range"
            min="3"
            max="25"
            step="1"
            value={maxTurns}
            onChange={(e) => setMaxTurns(e.target.value)}
            className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
          />
        </div>

        {/* Optional Custom Opening Prompt */}
        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-[11px] text-slate-500 hover:text-indigo-600 flex items-center gap-1.5 font-medium"
          >
            <Sliders className="w-3 h-3" />
            {showAdvanced ? 'Hide Custom Prompt' : 'Custom Opening Prompt (Optional)'}
          </button>
          {showAdvanced && (
            <textarea
              value={customInitialMessage}
              onChange={(e) => setCustomInitialMessage(e.target.value)}
              placeholder="Leave empty for persona to generate opening automatically..."
              rows={2}
              className="w-full mt-2 bg-white border border-slate-200 rounded-lg p-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-600"
            />
          )}
        </div>

        <button
          type="submit"
          disabled={actionLoading}
          className="w-full py-2.5 px-4 rounded-lg font-semibold text-xs flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white transition-colors shadow-xs disabled:opacity-50"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          {actionLoading ? 'Starting Simulation...' : 'Launch Simulation'}
        </button>
      </form>
    </div>
  );
}
