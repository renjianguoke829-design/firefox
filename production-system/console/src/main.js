import path from 'node:path';
import { app, BrowserWindow, Tray, Menu, ipcMain, nativeImage, dialog } from 'electron';
import Store from 'electron-store';
import pg from 'pg';
import { DockerService } from './services/docker.js';
import { StatsService } from './services/stats.js';

const { Pool } = pg;

const store = new Store({
  defaults: {
    backgroundPath: '',
    backgroundType: 'image',
    themeId: 10
  }
});

let mainWindow;
let tray;

const dockerService = new DockerService('/var/run/docker.sock');
const statsService = new StatsService(process.env.DATABASE_URL);
const pool = new Pool({ connectionString: process.env.DATABASE_URL });

function getBackgroundMeta(backgroundPath) {
  if (!backgroundPath) {
    return { type: 'none', path: '' };
  }
  const ext = path.extname(backgroundPath).toLowerCase();
  const videoExts = new Set(['.mp4', '.webm', '.mov', '.mkv']);
  const gifExts = new Set(['.gif']);
  if (videoExts.has(ext)) {
    return { type: 'video', path: backgroundPath };
  }
  if (gifExts.has(ext)) {
    return { type: 'gif', path: backgroundPath };
  }
  return { type: 'image', path: backgroundPath };
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    frame: false,
    autoHideMenuBar: true,
    titleBarStyle: 'hidden',
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  app.setLoginItemSettings({ openAtLogin: true });

  if (process.env.VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL);
  } else {
    mainWindow.loadFile(path.join(process.cwd(), 'dist/index.html'));
  }

  mainWindow.on('close', (event) => {
    if (!app.isQuiting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });
}

function createTray() {
  const icon = nativeImage.createEmpty();
  tray = new Tray(icon);
  tray.setToolTip('Production Console');
  const menu = Menu.buildFromTemplate([
    {
      label: '显示/隐藏',
      click: () => {
        if (mainWindow.isVisible()) {
          mainWindow.hide();
        } else {
          mainWindow.show();
        }
      }
    },
    {
      label: '退出',
      click: () => {
        app.isQuiting = true;
        app.quit();
      }
    }
  ]);
  tray.setContextMenu(menu);
  tray.on('click', () => {
    if (mainWindow.isVisible()) {
      mainWindow.hide();
    } else {
      mainWindow.show();
    }
  });
}

ipcMain.handle('background:get', async () => getBackgroundMeta(store.get('backgroundPath')));
ipcMain.handle('background:choose', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [
      { name: 'Media', extensions: ['png', 'jpg', 'jpeg', 'webp', 'gif', 'mp4', 'webm', 'mov', 'mkv'] }
    ]
  });

  if (result.canceled || !result.filePaths[0]) {
    return getBackgroundMeta(store.get('backgroundPath'));
  }

  store.set('backgroundPath', result.filePaths[0]);
  const meta = getBackgroundMeta(result.filePaths[0]);
  mainWindow.webContents.send('background:changed', meta);
  return meta;
});


ipcMain.handle('theme:get', async () => ({ themeId: Number(store.get('themeId') || 10) }));
ipcMain.handle('theme:set', async (_, themeId) => {
  const normalized = Number(themeId);
  store.set('themeId', Number.isFinite(normalized) ? normalized : 10);
  return { themeId: Number(store.get('themeId') || 10) };
});

ipcMain.handle('docker:list', async () => {
  try {
    return await dockerService.refreshStatuses();
  } catch (error) {
    return { error: error.message };
  }
});

ipcMain.handle('docker:status', async (_, name) => {
  try {
    return await dockerService.getContainerStatus(name);
  } catch (error) {
    return { error: error.message };
  }
});

ipcMain.handle('docker:start', async (_, name) => {
  try {
    const result = await dockerService.startContainer(name);
    const statuses = await dockerService.refreshStatuses();
    mainWindow?.webContents.send('docker:status-updated', statuses);
    return result;
  } catch (error) {
    return { error: error.message };
  }
});

ipcMain.handle('docker:stop', async (_, name) => {
  try {
    const result = await dockerService.stopContainer(name);
    const statuses = await dockerService.refreshStatuses();
    mainWindow?.webContents.send('docker:status-updated', statuses);
    return result;
  } catch (error) {
    return { error: error.message };
  }
});

ipcMain.handle('docker:logs', async (_, name, lines = 50) => {
  try {
    return await dockerService.getContainerLogs(name, lines);
  } catch (error) {
    return { error: error.message };
  }
});


ipcMain.handle('stats:getTodayStats', async () => {
  try {
    return await statsService.getTodayStats();
  } catch (error) {
    return { error: error.message };
  }
});

ipcMain.handle('stats:getWeekTrend', async () => {
  try {
    return await statsService.getWeekTrend();
  } catch (error) {
    return { error: error.message };
  }
});

ipcMain.handle('stats:getBottleneck', async () => {
  try {
    return await statsService.getBottleneck();
  } catch (error) {
    return { error: error.message };
  }
});

ipcMain.handle('stats:getQualityTrend', async () => {
  try {
    return await statsService.getQualityTrend();
  } catch (error) {
    return { error: error.message };
  }
});

ipcMain.handle('stats:getRecentCards', async (_, limit = 5) => {
  try {
    return await statsService.getRecentCards(limit);
  } catch (error) {
    return { error: error.message };
  }
});

ipcMain.handle('db:query', async (_, queryText, values = []) => {
  const client = await pool.connect();
  try {
    const result = await client.query(queryText, values);
    return { rows: result.rows, rowCount: result.rowCount };
  } catch (error) {
    return { error: error.message };
  } finally {
    client.release();
  }
});

app.whenReady().then(() => {
  createMainWindow();
  createTray();
  dockerService.on('status-changed', (statuses) => {
    mainWindow?.webContents.send('docker:status-updated', statuses);
  });
  dockerService.startAutoRefresh(30000);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  dockerService.stopAutoRefresh();
});
