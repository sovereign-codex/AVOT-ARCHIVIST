export type LifecycleState =
  | "S0" | "S1" | "S2" | "S3" | "S4"
  | "S5" | "S6" | "S7" | "S8" | "S9";

export type MaturityLevel = "M0" | "M1" | "M2" | "M3" | "M4";

export type ActionType = "think" | "communicate" | "execute" | "bind" | "propose";

export interface AvotIdentity {
  avot_id: string;
  purpose?: string;
  steward?: string;
  header_ref?: string;
}

export interface AvotState {
  lifecycle_state: LifecycleState;
  maturity: MaturityLevel;
  binding: boolean;
}

export interface AvotRefusal {
  reason: string;
  reference: string;
  next_step: "wait" | "propose" | "escalate" | "dissolve";
}

export interface AvotSignal {
  avot_id: string;
  signal_type: string;
  payload: Record<string, unknown>;
  timestamp: string;
}

export interface AVOT {
  identify(): AvotIdentity;
  state(): AvotState;
  classifyAction(intent: string): ActionType;
  canAttempt(action: ActionType): boolean;
  refuse(reason: string, reference: string, nextStep?: AvotRefusal["next_step"]): AvotRefusal;
  emitSignal(signalType: string, payload?: Record<string, unknown>): AvotSignal;
}
