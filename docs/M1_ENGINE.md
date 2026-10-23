# M1 paired-prompt engine

## What runs

`cortex pair` runs two GPT-2 inputs with equal tokenized lengths, caches each block's `blocks.{layer}.hook_out` residual, calculates descriptive per-layer/per-token RMS activation differences, and substitutes a clean activation at a chosen layer/position into a corrupted run. It measures the next-token correct-vs-incorrect logit margin before and after intervention. A separate same-target self-patch control flags unexpected numerics.

```bash
python -m pip install -e '.[ml]'
cortex pair \
  --clean 'The dog runs' \
  --corrupted 'The cat runs' \
  --correct-token ' dog' \
  --incorrect-token ' cat' \
  --layer 5 --token-index 1 --device cpu \
  --output artifacts/dog-cat.json
```

This is a mechanical demo example, **not a proven or scientifically meaningful IOI circuit**. Tokenization may differ: the engine checks length and candidate IDs before execution, and rejects incompatible prompts. GPT-2 weights download on the first run; GPU acceleration is not required.

## Constraints and evidence

- `clean` and `corrupted` must tokenize to the same length of 1–128 tokens; matching position does not prove semantic alignment.
- Both candidate strings must map to exactly one token **without automatically inserting BOS/EOS**; candidates must have distinct IDs.
- Model fixed to `openai-community/gpt2`; CPU or Apple MPS only, no arbitrary model code.
- Optional `--revision` **must** be an exact 40-character commit SHA; without it, JSON marks the revision `null`. Cross-run reproducibility assertions must not accept an unpinned revision.
- JSON contains prompt hashes, **raw token IDs**, candidate IDs, layer/position, output margins, residual RMS map, self-patch tolerance and result. Raw prompts and tensor arrays are omitted.
- The recovery ratio may be undefined when clean/corrupted logit margins are too close; negative and >1 values are valid.
- No full model-backed experiment has been run inside this development environment yet; synthetic Torch-backed tests prove tensor manipulation and validation but **not TransformerLens 4.2 execution compatibility**.

## Next steps

1. Run model smoke and paired-prompt commands with TransformerLens 4.2.0 on macOS and Linux CPU; pin the exact Hugging Face model revision and record checksums.
2. Verify observed GPT-2 hook output shapes/names; test clean and corrupted prompts with meaningful aligned tokens.
3. Implement bounded backend job queue and experiment persistence; expose per-layer RMS/patch summary in React.
4. Add experiment schema, test assertions, and CI regression runner after revision and reproducibility gates pass.
