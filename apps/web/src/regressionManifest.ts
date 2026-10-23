/** Strict, client-only regression manifest creation.
 *  The exported file contains RAW PROMPTS. No data is sent to the server.
 */
export const PINNED_GPT2_REVISION = '607a30d783dfa663caf39e06633721c8d4cfcd7e';

export type Submission = {
  clean: string; corrupted: string; correct_token: string; incorrect_token: string;
  layer: number; token_index: number; device: 'cpu' | 'mps'; revision: string;
};

export type Evidence = {
  status: 'pass' | 'fail';
  model: { id: string; revision: string | null; device: string };
  input: { clean_sha256: string; corrupted_sha256: string };
  patch: { layer: number; token_index: number };
  scores: { patched: number; recovery: number | null };
  control: { max_abs_logit_delta: number; tolerance: number };
};

export type RegressionManifest = {
  schema_version: 1;
  model: { id: string; revision: string; device: 'cpu' | 'mps' };
  experiment: Omit<Submission, 'device' | 'revision'>;
  assertions: {
    control_delta_max: number;
    recovery_min: number;
    recovery_max: number;
    patched_margin_min: number;
    patched_margin_max: number;
  };
};

async function sha256(text: string): Promise<string> {
  if (!globalThis.crypto?.subtle) throw new Error('SHA-256 needs a secure browser context (localhost/HTTPS).');
  const bytes = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(digest)].map(x => x.toString(16).padStart(2, '0')).join('');
}

export async function createRegressionManifest(
  submitted: Submission, evidence: Evidence,
): Promise<RegressionManifest> {
  if (evidence.status !== 'pass') throw new Error('A passing experiment is required.');
  if (evidence.model?.id !== 'openai-community/gpt2'
    || evidence.model.revision !== PINNED_GPT2_REVISION
    || evidence.model.device !== submitted.device) {
    throw new Error('Model identity, pinned revision or device does not match.');
  }
  if (!['cpu', 'mps'].includes(submitted.device)) throw new Error('Unsupported compute device.');
  if (evidence.patch?.layer !== submitted.layer
    || evidence.patch.token_index !== submitted.token_index) {
    throw new Error('Patch location differs from the submitted experiment.');
  }
  const [source, target] = await Promise.all([sha256(submitted.clean), sha256(submitted.corrupted)]);
  if (source !== evidence.input?.clean_sha256 || target !== evidence.input?.corrupted_sha256) {
    throw new Error('Prompt hashes do not match the result. Regeneration is unsafe.');
  }
  if (!Number.isFinite(evidence.scores?.patched)
    || evidence.scores.recovery === null
    || !Number.isFinite(evidence.scores.recovery)
    || !Number.isFinite(evidence.control?.max_abs_logit_delta)
    || evidence.control.max_abs_logit_delta > evidence.control.tolerance) {
    throw new Error('Nonfinite measurements or failed numerical control.');
  }
  const r = evidence.scores.recovery;
  const margin = evidence.scores.patched;
  const recoveryAllowance = Math.max(.15, Math.abs(r) * .25);
  const marginAllowance = Math.max(.15, Math.abs(margin) * .3);
  return {
    schema_version: 1,
    model: { id: evidence.model.id, revision: PINNED_GPT2_REVISION, device: submitted.device },
    experiment: {
      clean: submitted.clean, corrupted: submitted.corrupted,
      correct_token: submitted.correct_token, incorrect_token: submitted.incorrect_token,
      layer: submitted.layer, token_index: submitted.token_index,
    },
    assertions: {
      control_delta_max: Math.max(.000001, Math.min(.1, evidence.control.tolerance)),
      recovery_min: Number((r - recoveryAllowance).toFixed(6)),
      recovery_max: Number((r + recoveryAllowance).toFixed(6)),
      patched_margin_min: Number((margin - marginAllowance).toFixed(6)),
      patched_margin_max: Number((margin + marginAllowance).toFixed(6)),
    },
  };
}

export function validateManifestBounds(manifest: RegressionManifest): string | null {
  const a = manifest.assertions;
  if (!Object.values(a).every(Number.isFinite)) return 'All limits must be finite numbers.';
  if (a.control_delta_max <= 0 || a.control_delta_max > .1) {
    return 'Control tolerance must be greater than 0 and no more than 0.1.';
  }
  if (a.recovery_min > a.recovery_max || a.patched_margin_min > a.patched_margin_max) {
    return 'Each minimum must not exceed its maximum.';
  }
  return null;
}
