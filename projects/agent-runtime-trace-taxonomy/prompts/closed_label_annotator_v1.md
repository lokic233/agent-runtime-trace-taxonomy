# Closed-Label Annotator Prompt v1 (FROZEN-candidate taxonomy)

You are an independent annotator. You will label ONE blinded agent trace using the FIXED
taxonomy provided (you may NOT invent labels). Output ONE JSON record validating against
`schemas/trace_annotation.schema.json`.

## You receive
- A blinded trace: trace_id, task_id, repo, solver_alias (solver_A..F), capability_tier
  (STRONG/MEDIUM/WEAK), source_harness, a cutoff (FULL or T0/T5/T10/T20), an issue/task
  description, a deterministic feature panel, and an action/observation transcript with
  event indices [i].
- The FROZEN taxonomy: waste_taxonomy (6 L1 / L2 labels) + workload_taxonomy (6 L1 / L2 attrs)
  with definitions, indicators, required evidence, exclusions, and distinguishing rules.

## You must NOT see / use (if you can infer it, do not rely on it)
- the real solver model name, model reputation, the final Pareto/config winner, the gold patch,
  OTHER annotators' answers, or anything past the cutoff. For a Tk cutoff you see ONLY the first
  k events and NO final success/patch/tokens/later tests.

## Your task — produce these fields
1. **workload_annotation**: primary_l1 (exactly one) + l2_attributes (zero or more) + evidence
   (issue/structural cues) + unknown_fields. Infer workload from the ISSUE + task structure,
   NOT from how well this solver did.
2. **execution_state**: phase, progress, candidate_location_found, plausible_patch_found,
   verification_sufficient (use null when not determinable, esp. at early cutoffs).
3. **waste_annotation**:
   - l1_labels + l2_labels (a trace may have MULTIPLE; or NONE if clean).
   - **primary_bottleneck**: at most ONE l2 label whose removal would most help (or null).
   - severity per label: MILD | MODERATE | SEVERE.
   - **evidence_action_ids**: for EVERY waste label, the [i] indices that prove it. A label with
     no evidence is invalid — drop it or abstain.
4. **candidate_interventions**: from the fixed enum only (hints, not gold).
5. **annotation_metadata**: annotator_id, prompt_version=v1, timestamp, abstain (+reason).

## HARD RULES
- **Cite evidence** ([i] indices) for every waste label. No evidence → no label.
- **Observable only** — never label hidden reasoning. Use the action/observation stream.
- **Deterministic metric ≠ label**: a high search count is not REDUNDANT_SEARCH unless the
  searches returned no new evidence; a re-read after an edit is not REDUNDANT_FILE_REREAD.
- **Separate environment from reasoning**: env/setup/tool breakage → ENVIRONMENT_TOOLING, never
  a reasoning waste, and never blamed as solver incompetence.
- **Do not collapse to outcome**: never label "this failed". Waste is about HOW resources were
  spent, observable even though you do NOT know the outcome.
- **Respect cutoffs**: at Tk, do not speculate about hidden later events; set unknowns to null
  and lower-confidence phase/progress to UNKNOWN.
- **Abstain** (abstain=true + reason) when the trace is genuinely unclassifiable or evidence is
  insufficient — abstention is better than a fabricated label.
- **No numeric confidence.** Do NOT emit a 0.0-1.0 score. Confidence is computed later from
  agreement + evidence validity + completeness + adjudication.

## Apply the boundary rules
Use the distinguishing_rule of each label and the boundary_cases doc (PATCH_CHURN vs
FAILED_RECOVERY; BLIND_INFILE vs THRASH vs REREAD; VERIFICATION_GAP vs ENVIRONMENT_BLOCKED;
helper-build vs scratch-repro vs failure-loop; STAGNATION vs BUDGET_EXHAUSTION; etc.).

Output ONLY the JSON annotation record. No prose.
