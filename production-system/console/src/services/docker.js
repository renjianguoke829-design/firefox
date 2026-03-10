import { EventEmitter } from 'node:events';
import { Docker } from 'node-docker-api';

export class DockerService extends EventEmitter {
  constructor(socketPath = '/var/run/docker.sock') {
    super();
    this.docker = new Docker({ socketPath });
    this.statusCache = new Map();
    this.poller = null;
  }

  async getAllContainerStatuses() {
    const containers = await this.docker.container.list({ all: true });
    return containers.map((container) => ({
      id: container.data.Id,
      name: container.data.Names?.[0]?.replace('/', '') || 'unknown',
      state: container.data.State,
      status: container.data.Status
    }));
  }

  async getContainerStatus(name) {
    const statuses = await this.getAllContainerStatuses();
    return statuses.find((item) => item.name === name) || null;
  }

  async startContainer(name) {
    const container = await this._findContainer(name);
    await container.start();
    return this.getContainerStatus(name);
  }

  async stopContainer(name) {
    const container = await this._findContainer(name);
    await container.stop();
    return this.getContainerStatus(name);
  }

  async getContainerLogs(name, lines = 50) {
    const container = await this._findContainer(name);
    const raw = await container.logs({ stdout: true, stderr: true, tail: lines });
    return raw.toString('utf-8');
  }

  async refreshStatuses() {
    const statuses = await this.getAllContainerStatuses();
    const next = new Map(statuses.map((item) => [item.name, item.state]));
    let changed = false;

    if (next.size !== this.statusCache.size) {
      changed = true;
    } else {
      for (const [name, state] of next.entries()) {
        if (this.statusCache.get(name) !== state) {
          changed = true;
          break;
        }
      }
    }

    if (changed) {
      this.statusCache = next;
      this.emit('status-changed', statuses);
    }

    return statuses;
  }

  startAutoRefresh(intervalMs = 30000) {
    if (this.poller) {
      clearInterval(this.poller);
    }
    this.poller = setInterval(() => {
      this.refreshStatuses().catch(() => {});
    }, intervalMs);
  }

  stopAutoRefresh() {
    if (this.poller) {
      clearInterval(this.poller);
      this.poller = null;
    }
  }

  async _findContainer(name) {
    const statuses = await this.getAllContainerStatuses();
    const match = statuses.find((item) => item.name === name);
    if (!match) {
      throw new Error(`Container not found: ${name}`);
    }
    return this.docker.container.get(match.id);
  }
}
