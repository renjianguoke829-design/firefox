import React, { useEffect, useState } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

export default function Dashboard() {
  const ipc = window.electron || (globalThis.require ? globalThis.require('electron').ipcRenderer : null);
  const [todayStats, setTodayStats] = useState({ contradictionCount: 0, pipelineRuns: 0, avgDurationMs: 0 });
  const [weekTrend, setWeekTrend] = useState([]);
  const [qualityTrend, setQualityTrend] = useState([]);
  const [bottleneck, setBottleneck] = useState(null);
  const [recentCards, setRecentCards] = useState([]);

  useEffect(() => {
    const load = async () => {
      if (!ipc) {
        return;
      }
      const [today, week, bottleneckData, quality, cards] = await Promise.all([
        ipc.invoke('stats:getTodayStats'),
        ipc.invoke('stats:getWeekTrend'),
        ipc.invoke('stats:getBottleneck'),
        ipc.invoke('stats:getQualityTrend'),
        ipc.invoke('stats:getRecentCards', 5)
      ]);
      if (!today?.error) setTodayStats(today);
      if (Array.isArray(week)) setWeekTrend(week);
      if (bottleneckData?.bottleneck) setBottleneck(bottleneckData.bottleneck);
      if (Array.isArray(quality)) setQualityTrend(quality);
      if (Array.isArray(cards)) setRecentCards(cards);
    };

    load();
  }, [ipc]);

  return (
    <div className="grid h-full grid-cols-2 gap-4 overflow-auto">
      <div className="col-span-2 rounded-xl border p-4" style={{ borderColor: 'var(--color-border)' }}>
        <div className="mb-3 text-sm">今日指标</div>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-4xl font-bold">{todayStats.contradictionCount}</div>
            <div className="text-sm">矛盾卡数量</div>
          </div>
          <div>
            <div className="text-4xl font-bold">{todayStats.pipelineRuns}</div>
            <div className="text-sm">流水线运行次数</div>
          </div>
          <div>
            <div className="text-4xl font-bold">{todayStats.avgDurationMs}</div>
            <div className="text-sm">平均耗时(ms)</div>
          </div>
        </div>
      </div>

      <div className="rounded-xl border p-4" style={{ borderColor: 'var(--color-border)' }}>
        <div className="mb-2 text-sm">本周产出趋势</div>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={weekTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#64748b" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="outputCount" stroke="#3b82f6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-xl border p-4" style={{ borderColor: 'var(--color-border)' }}>
        <div className="mb-2 text-sm">质量评分趋势（最近20张）</div>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={qualityTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#64748b" />
              <XAxis dataKey="index" />
              <YAxis domain={[0, 10]} />
              <Tooltip />
              <Line type="monotone" dataKey="qualityScore" stroke="#22c55e" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-xl border p-4" style={{ borderColor: 'var(--color-border)' }}>
        <div className="mb-2 text-sm">瓶颈工序</div>
        <div className="text-base" style={{ color: '#ef4444' }}>
          {bottleneck ? `${bottleneck.stage} (${bottleneck.avgDurationMs}ms)` : '暂无数据'}
        </div>
      </div>

      <div className="rounded-xl border p-4" style={{ borderColor: 'var(--color-border)' }}>
        <div className="mb-2 text-sm">最新矛盾卡</div>
        <div className="space-y-2">
          {recentCards.map((card, index) => (
            <div className="rounded border p-2 text-sm" style={{ borderColor: 'var(--color-border)' }} key={`${card.title}-${index}`}>
              <div className="font-semibold">{card.title}</div>
              <div className="opacity-80">{card.summary}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
