import fs from "fs";
import yaml from "js-yaml";
import { v4 as uuidv4 } from "uuid";

export class SignalLedgerError extends Error {}

export class SignalLedger {
  constructor(private ledgerPath: string) {
    if (!fs.existsSync(this.ledgerPath)) {
      throw new SignalLedgerError(`Signal ledger not found at ${this.ledgerPath}`);
    }
  }

  private load(): any {
    const raw = fs.readFileSync(this.ledgerPath, "utf-8");
    return yaml.load(raw) || {};
  }

  private write(data: any) {
    fs.writeFileSync(this.ledgerPath, yaml.dump(data, { sortKeys: false }), "utf-8");
  }

  readSignals(): any[] {
    const ledger: any = this.load();
    return ledger?.signal_ledger?.signals ?? [];
  }

  appendSignal(avotId: string, signalType: string, description: string, severity = "low", context: any = {}, metadata: any = {}) {
    const ledger: any = this.load();
    if (!ledger.signal_ledger) throw new SignalLedgerError("Invalid signal ledger structure");

    const signal = {
      signal_id: `SIG-${uuidv4()}`,
      avot_id: avotId,
      signal_type: signalType,
      timestamp: new Date().toISOString(),
      severity,
      description,
      context,
      metadata,
    };

    ledger.signal_ledger.signals.push(signal);
    this.write(ledger);
    return signal;
  }
}
