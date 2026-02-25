// frontend/src/components/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Area, AreaChart
} from 'recharts';
import { useWebSocket } from '../hooks/useWebSocket';
import {
  CreditCard, TrendingUp, AlertTriangle, DollarSign,
  Clock, ShoppingCart, Activity, Zap, Brain,
  ArrowUpRight, ArrowDownRight
} from 'lucide-react';

// ── Colour constants for charts ────────────────────────────────────
const CHART_COLORS = {
  blue: '#3b82f6',
  indigo: '#6366f1',
  purple: '#8b5cf6',
  cyan: '#22d3ee',
  emerald: '#10b981',
  amber: '#f59e0b',
  rose: '#f43f5e',
};

const PIE_COLORS = ['#6366f1', '#8b5cf6', '#3b82f6', '#22d3ee', '#10b981'];

// ── Custom tooltip ─────────────────────────────────────────────────
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p className="label">{label}</p>
      {payload.map((p, i) => (
        <p key={i} className="value" style={{ color: p.color }}>
          {p.name}: ${Number(p.value).toLocaleString()}
        </p>
      ))}
    </div>
  );
};

// ── Mock data generators ───────────────────────────────────────────
const spendingTrends = Array.from({ length: 14 }, (_, i) => {
  const day = new Date();
  day.setDate(day.getDate() - (13 - i));
  return {
    date: day.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    amount: Math.round(800 + Math.random() * 1200),
    average: Math.round(1100 + Math.sin(i / 2) * 200),
  };
});

const categoryData = [
  { name: 'Food & Dining', value: 1200 },
  { name: 'Shopping', value: 980 },
  { name: 'Entertainment', value: 750 },
  { name: 'Bills & Utilities', value: 1560 },
  { name: 'Transportation', value: 540 },
];

// ── Main Component ─────────────────────────────────────────────────
const Dashboard = ({ userId }) => {
  const [realTimeData, setRealTimeData] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [currentTime, setCurrentTime] = useState(new Date());

  const { isConnected, messages } = useWebSocket(userId);

  // Clock tick
  useEffect(() => {
    const t = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  // Process WebSocket messages
  useEffect(() => {
    if (messages.length > 0) {
      const last = messages[messages.length - 1];
      if (last.type === 'transaction') {
        setRealTimeData(prev => [...prev, last.data].slice(-20));
      } else if (last.type === 'alert') {
        setAlerts(prev => [last.data, ...prev.slice(0, 9)]);
      }
    }
  }, [messages]);

  // ── Stats cards config ───────────────────────────────────────────
  const stats = [
    {
      label: 'Total Balance',
      value: '$45,230.89',
      change: '+12.5%',
      positive: true,
      icon: DollarSign,
      iconClass: 'green',
    },
    {
      label: "Today's Spending",
      value: '$1,250.75',
      change: '-3.2%',
      positive: false,
      icon: ShoppingCart,
      iconClass: 'blue',
    },
    {
      label: 'Active Alerts',
      value: alerts.length,
      change: alerts.length > 0 ? 'Needs attention' : 'All clear',
      positive: alerts.length === 0,
      icon: AlertTriangle,
      iconClass: alerts.length > 0 ? 'red' : 'green',
    },
    {
      label: 'Investment Return',
      value: '+8.3%',
      change: '+2.1% this month',
      positive: true,
      icon: TrendingUp,
      iconClass: 'purple',
    },
  ];

  // ── Recent transactions from real-time data ──────────────────────
  const recentTx = realTimeData.map(tx => ({
    time: new Date(tx.timestamp).toLocaleTimeString(),
    merchant: tx.merchant,
    amount: tx.amount,
    category: tx.category,
    status: tx.status,
  }));

  // ── Render ───────────────────────────────────────────────────────
  return (
    <>
      {/* Background mesh */}
      <div className="bg-mesh" />

      <div className="dashboard">
        {/* ── Header ──────────────────────────────────────────────── */}
        <header className="dashboard-header">
          <div>
            <h1>Fintech Dashboard</h1>
          </div>
          <div className="header-meta">
            <div className="live-indicator">
              <span className={`live-dot ${isConnected ? '' : 'disconnected'}`} />
              {isConnected ? 'Live' : 'Offline'}
            </div>
            <span className="header-time">
              {currentTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
          </div>
        </header>

        {/* ── Stats Row ───────────────────────────────────────────── */}
        <div className="stats-grid">
          {stats.map((s, i) => (
            <div className="glass-card stat-card" key={i}>
              <div className="stat-info">
                <p className="stat-label">{s.label}</p>
                <p className="stat-value">{s.value}</p>
                <p className={`stat-change ${s.positive ? 'positive' : 'negative'}`}>
                  {s.positive
                    ? <ArrowUpRight size={13} style={{ display: 'inline', verticalAlign: '-2px', marginRight: 3 }} />
                    : <ArrowDownRight size={13} style={{ display: 'inline', verticalAlign: '-2px', marginRight: 3 }} />
                  }
                  {s.change}
                </p>
              </div>
              <div className={`stat-icon-box ${s.iconClass}`}>
                <s.icon />
              </div>
            </div>
          ))}
        </div>

        {/* ── Charts Row ──────────────────────────────────────────── */}
        <div className="charts-grid">
          {/* Spending Trends */}
          <div className="glass-card">
            <h3 className="section-title"><Activity size={18} /> Spending Trends</h3>
            <div style={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={spendingTrends}>
                  <defs>
                    <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={CHART_COLORS.indigo} stopOpacity={0.35} />
                      <stop offset="100%" stopColor={CHART_COLORS.indigo} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
                  <Area
                    type="monotone"
                    dataKey="amount"
                    stroke={CHART_COLORS.indigo}
                    fill="url(#areaGrad)"
                    strokeWidth={2}
                    name="Daily Spending"
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="average"
                    stroke={CHART_COLORS.cyan}
                    strokeWidth={2}
                    strokeDasharray="6 4"
                    name="7-Day Average"
                    dot={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Category Breakdown */}
          <div className="glass-card">
            <h3 className="section-title"><ShoppingCart size={18} /> Spending by Category</h3>
            <div style={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={4}
                    dataKey="value"
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  >
                    {categoryData.map((_, idx) => (
                      <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value) => [`$${value.toLocaleString()}`, 'Amount']}
                    contentStyle={{
                      background: 'rgba(15,23,42,0.92)',
                      border: '1px solid rgba(255,255,255,0.06)',
                      borderRadius: 8,
                      color: '#f1f5f9',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* ── Bottom Row: Transactions + Alerts ───────────────────── */}
        <div className="bottom-grid">
          {/* Live Transactions */}
          <div className="glass-card">
            <h3 className="section-title"><Zap size={18} /> Real-time Transactions</h3>
            <div className="tx-list">
              {recentTx.length > 0 ? (
                recentTx.map((tx, i) => (
                  <div className="tx-row" key={i} style={{ animationDelay: `${i * 40}ms` }}>
                    <div>
                      <p className="tx-merchant">{tx.merchant}</p>
                      <p className="tx-meta">{tx.time} · {tx.category}</p>
                    </div>
                    <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
                      <span className={`tx-amount ${tx.amount < 0 ? 'debit' : 'credit'}`}>
                        {tx.amount < 0 ? '-' : ''}${Math.abs(tx.amount).toFixed(2)}
                      </span>
                      <span className={`status-pill ${(tx.status || 'completed').toLowerCase()}`}>
                        {tx.status || 'COMPLETED'}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="empty-state">
                  <Clock />
                  <p className="label">Waiting for transactions…</p>
                  <p>Live data will appear here once the Kafka stream is running.</p>
                </div>
              )}
            </div>
          </div>

          {/* Alerts */}
          <div className="glass-card">
            <h3 className="section-title"><AlertTriangle size={18} /> Alerts & Notifications</h3>
            {alerts.length > 0 ? (
              alerts.map((a, i) => (
                <div
                  className={`alert-card ${(a.severity || 'low').toLowerCase()}`}
                  key={i}
                  style={{ animationDelay: `${i * 60}ms` }}
                >
                  <p className="alert-title">{a.title}</p>
                  <p className="alert-message">{a.message}</p>
                  <p className="alert-time">{new Date(a.timestamp).toLocaleString()}</p>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <TrendingUp />
                <p className="label">All systems normal</p>
                <p>No alerts at this time</p>
              </div>
            )}
          </div>
        </div>

        {/* ── AI Advisor Hero ─────────────────────────────────────── */}
        <div className="ai-hero">
          <div className="ai-hero-inner">
            <div className="ai-hero-header">
              <div>
                <h2>AI Financial Advisor</h2>
                <p>Get personalized financial advice powered by AI agents</p>
              </div>
              <div className="ai-hero-badge">
                <Brain />
              </div>
            </div>

            <div className="ai-features">
              <div className="ai-feature-card">
                <h4>Portfolio Health</h4>
                <p>Your portfolio is well-diversified with a risk score of 7.2/10</p>
                <button className="ai-btn">View Analysis</button>
              </div>
              <div className="ai-feature-card">
                <h4>Spending Insights</h4>
                <p>You're spending 15% more on dining this month than average</p>
                <button className="ai-btn">See Recommendations</button>
              </div>
              <div className="ai-feature-card">
                <h4>Ask Advisor</h4>
                <p>Ask any financial question to our AI-powered advisor</p>
                <button className="ai-btn">Start Conversation</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Dashboard;