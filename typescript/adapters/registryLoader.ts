import fs from "fs";
import yaml from "js-yaml";

export class RegistryReadError extends Error {}

export class RegistryLoader {
  constructor(private registryPath: string) {
    if (!fs.existsSync(this.registryPath)) {
      throw new RegistryReadError(`Registry file not found at ${this.registryPath}`);
    }
  }

  loadRegistry(): Record<string, unknown> {
    const raw = fs.readFileSync(this.registryPath, "utf-8");
    return (yaml.load(raw) as Record<string, unknown>) || {};
  }

  getAvotEntry(avotId: string): Record<string, unknown> {
    const registry: any = this.loadRegistry();
    const avots = registry?.avot_registry?.avots ?? {};
    return { ...(avots[avotId] || {}) };
  }
}
