import React, { useEffect, useMemo, useState } from 'react';
import { getTheme, themeEntries } from '../themes.js';
import Dashboard from '../components/Dashboard.jsx';

const modules = [
  { key: 'pipeline', label: '流水线', icon: 'PL' },
  { key: 'browser', label: '浏览器', icon: 'BR' },
  { key: 'llm', label: '大模型', icon: 'AI' },
  { key: 'database', label: '数据库', icon: 'DB' },
  { key: 'terminal', label: '终端', icon: 'SH' },
  { key: 'cloud', label: '云盘', icon: 'CL' }
];

const serviceNames = ['postgres', 'pgadmin', 'qinglong', 'ttyd'];

function BackgroundLayer({ background }) {
  if (!background || background.type === 'none' || !background.path) {
    return null;
  }
  if (background.type === 'video') {
    return (
      <video className="absolute inset-0 h-full w-full object-cover opacity-25" autoPlay muted loop>
        <source src={background.path} />
      </video>
    );
  }
  return <img className="absolute inset-0 h-full w-full object-cover opacity-20" src={background.path} alt="dynamic background" />;
}

export default function App() {
  const [now, setNow] = useState(new Date());
  const [activeModule, setActiveModule] = useState('pipeline');
  const [services, setServices] = useState({});
  const [todayOutput, setTodayOutput] = useState(0);
  const [pipelineState] = useState('待命中');
  const [recentCard, setRecentCard] = useState('暂无矛盾卡');
  const [selectedService, setSelectedService] = useState('postgres');
  const [serviceLogs, setServiceLogs] = useState('');
  const [background, setBackground] = useState({ type: 'none', path: '' });
  const [themeId, setThemeId] = useState(10);

  const ipc = window.electron || (globalThis.require ? globalThis.require('electron').ipcRenderer : null);
  const activeTheme = getTheme(themeId);

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const loadData = async () => {
      if (!ipc) {
        return;
      }
      const [{ themeId: storedThemeId }, bg, dockerInfo, cardStats, latestCard] = await Promise.all([
        ipc.invoke('theme:get'),
        ipc.invoke('background:get'),
        ipc.invoke('docker:list'),
        ipc.invoke('db:query', 'SELECT COUNT(*)::int AS total FROM contradiction_cards WHERE DATE(created_at) = CURRENT_DATE'),
        ipc.invoke('db:query', 'SELECT title FROM contradiction_cards ORDER BY created_at DESC LIMIT 1')
      ]);
      if (storedThemeId) {
        setThemeId(storedThemeId);
      }
      if (bg) {
        setBackground(bg);
      }
      if (Array.isArray(dockerInfo)) {
        setServices(
          dockerInfo.reduce((acc, item) => {
            acc[item.name] = item.state;
            return acc;
          }, {})
        );
      }
      if (cardStats?.rows?.[0]?.total >= 0) {
        setTodayOutput(cardStats.rows[0].total);
      }
      if (latestCard?.rows?.[0]?.title) {
        setRecentCard(latestCard.rows[0].title);
      }
    };

    loadData();
    const refresh = setInterval(loadData, 30000);
    return () => clearInterval(refresh);
  }, [ipc]);

  useEffect(() => {
    if (!ipc) {
      return undefined;
    }
    const handler = (_, payload) => setBackground(payload);
    ipc.on('background:changed', handler);
    return () => ipc.removeListener('background:changed', handler);
  }, [ipc]);

  useEffect(() => {
    if (!ipc) {
      return undefined;
    }
    const handler = (_, payload) => {
      if (!Array.isArray(payload)) {
        return;
      }
      setServices(
        payload.reduce((acc, item) => {
          acc[item.name] = item.state;
          return acc;
        }, {})
      );
    };
    ipc.on('docker:status-updated', handler);
    return () => ipc.removeListener('docker:status-updated', handler);
  }, [ipc]);

  const rootStyle = {
    '--color-background': activeTheme.background,
    '--color-surface': activeTheme.surface,
    '--color-primary': activeTheme.primary,
    '--color-text': activeTheme.text,
    '--color-accent': activeTheme.accent,
    '--color-border': activeTheme.border,
    backgroundColor: 'var(--color-background)',
    color: 'var(--color-text)'
  };

  const moduleContent = useMemo(() => {
    if (activeModule === 'pipeline') {
      return <Dashboard />;
    }
    const info = modules.find((item) => item.key === activeModule);
    return info ? `${info.label}模块内嵌界面` : '模块未找到';
  }, [activeModule]);

  return (
    <div className="relative h-screen w-screen overflow-hidden" style={rootStyle}>
      <BackgroundLayer background={background} />
      <div className="relative z-10 flex h-full">
        <aside className="w-24 border-r p-3" style={{ borderColor: 'var(--color-border)', backgroundColor: 'color-mix(in srgb, var(--color-surface) 85%, transparent)' }}>
          <div className="mb-4 text-center text-xs">左侧导航</div>
          <div className="space-y-2">
            {modules.map((item) => (
              <button
                key={item.key}
                style={{
                  backgroundColor: activeModule === item.key ? 'var(--color-primary)' : 'color-mix(in srgb, var(--color-surface) 70%, transparent)',
                  color: 'var(--color-text)'
                }}
                className="flex w-full flex-col items-center rounded-xl p-2 text-xs"
                onClick={() => setActiveModule(item.key)}
              >
                <span className="text-sm font-semibold">{item.icon}</span>
                <span>{item.label}</span>
              </button>
            ))}
          </div>
        </aside>

        <main className="flex min-w-0 flex-1 flex-col">
          <header className="flex items-center justify-between border-b px-5 py-3" style={{ borderColor: 'var(--color-border)', backgroundColor: 'color-mix(in srgb, var(--color-surface) 75%, transparent)' }}>
            <span className="sr-only">顶部状态栏</span>
            <div className="text-sm">{now.toLocaleString()}</div>
            <div className="flex items-center gap-4">
              {serviceNames.map((name) => (
                <div className="flex items-center gap-2 text-xs" key={name}>
                  <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: services[name] === 'running' ? '#22c55e' : '#ef4444' }} />
                  <span>{name}</span>
                </div>
              ))}
            </div>
            <div className="text-base font-semibold">今日产出 {todayOutput}</div>
          </header>

          <section className="flex min-h-0 flex-1">
            <div className="flex-1 p-6">
              <div className="mb-4 flex items-center justify-between gap-4">
                <h1 className="text-xl font-semibold">主控制台</h1>
                <div className="flex items-center gap-2">
                  <label className="text-sm" htmlFor="theme-select">主题</label>
                  <select
                    id="theme-select"
                    value={themeId}
                    className="rounded border px-2 py-1 text-sm"
                    style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-surface)', color: 'var(--color-text)' }}
                    onChange={async (event) => {
                      const nextThemeId = Number(event.target.value);
                      setThemeId(nextThemeId);
                      if (ipc) {
                        await ipc.invoke('theme:set', nextThemeId);
                      }
                    }}
                  >
                    {themeEntries.map((theme) => (
                      <option key={theme.id} value={theme.id}>
                        {theme.id}. {theme.name}
                      </option>
                    ))}
                  </select>
                  <button
                    className="rounded px-3 py-1.5 text-sm"
                    style={{ backgroundColor: 'var(--color-accent)', color: '#0b1020' }}
                    onClick={async () => {
                      if (!ipc) {
                        return;
                      }
                      const bg = await ipc.invoke('background:choose');
                      if (bg) {
                        setBackground(bg);
                      }
                    }}
                  >
                    设置动态背景
                  </button>
                </div>
              </div>
              <div className="h-[calc(100%-3rem)] rounded-2xl border p-6 text-lg" style={{ borderColor: 'var(--color-border)', backgroundColor: 'color-mix(in srgb, var(--color-surface) 80%, transparent)' }}>
                {moduleContent}
              </div>
            </div>

            <aside className="w-80 border-l p-5" style={{ borderColor: 'var(--color-border)', backgroundColor: 'color-mix(in srgb, var(--color-surface) 80%, transparent)' }}>
              <h2 className="mb-3 text-sm font-semibold">流水线状态</h2>
              <div className="rounded-xl border p-3 text-sm" style={{ borderColor: 'var(--color-border)' }}>{pipelineState}</div>
              <h2 className="mb-3 mt-6 text-sm font-semibold">Docker服务控制</h2>
              <div className="space-y-2 rounded-xl border p-3 text-sm" style={{ borderColor: 'var(--color-border)' }}>
                <select
                  className="w-full rounded border px-2 py-1 text-sm"
                  style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-surface)', color: 'var(--color-text)' }}
                  value={selectedService}
                  onChange={(event) => setSelectedService(event.target.value)}
                >
                  {serviceNames.map((name) => (
                    <option key={name} value={name}>{name}</option>
                  ))}
                </select>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    className="rounded px-2 py-1 text-xs"
                    style={{ backgroundColor: 'var(--color-primary)' }}
                    onClick={async () => {
                      if (ipc) {
                        await ipc.invoke('docker:start', selectedService);
                      }
                    }}
                  >启动</button>
                  <button
                    className="rounded px-2 py-1 text-xs"
                    style={{ backgroundColor: '#b91c1c' }}
                    onClick={async () => {
                      if (ipc) {
                        await ipc.invoke('docker:stop', selectedService);
                      }
                    }}
                  >停止</button>
                  <button
                    className="rounded px-2 py-1 text-xs"
                    style={{ backgroundColor: 'var(--color-accent)', color: '#0b1020' }}
                    onClick={async () => {
                      if (ipc) {
                        const logs = await ipc.invoke('docker:logs', selectedService, 50);
                        setServiceLogs(typeof logs === 'string' ? logs : JSON.stringify(logs));
                      }
                    }}
                  >日志</button>
                </div>
                <pre className="max-h-32 overflow-auto rounded border p-2 text-[11px]" style={{ borderColor: 'var(--color-border)' }}>{serviceLogs || '暂无日志输出'}</pre>
              </div>
              <h2 className="mb-3 mt-6 text-sm font-semibold">最新矛盾卡</h2>
              <div className="rounded-xl border p-3 text-sm" style={{ borderColor: 'var(--color-border)' }}>{recentCard}</div>
            </aside>
          </section>
        </main>
      </div>
    </div>
  );
}
