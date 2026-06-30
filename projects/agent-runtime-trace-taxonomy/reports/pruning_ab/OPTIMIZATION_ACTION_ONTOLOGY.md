# Optimization-Action Ontology (frozen v0)

Distinct mechanisms — prevents vague labels ("prune", "compress") from hiding distinct effects. Each action defined by mechanism/cache/risk/reversibility/recovery/support/unit/failure-mode.

| action | resource benefit | cache effect | semantic risk | reversible? | recovery cost | runtime support needed | trace unit | known failure mechanism |
|--------|-----------------|--------------|---------------|:--:|:--:|------------------------|-----------|------------------------|
| **NO_OP** | none (baseline) | preserves (append-only) | none | n/a | n/a | none | call | n/a — the control |
| **LINE_DEDUP** | drop exact-duplicate lines already seen earlier | content-stable (no prefix rewrite) | low IF every removed line has an earlier identical copy | yes (rehydrate) | low (text retained) | shim line-diff | segment | removes a line that was duplicate-looking but semantically needed in this position |
| **GENTLE_CAP** | head+tail cap of large observations (>6k) | content-stable | medium (mid-content can be unique) | yes | low | shim cap | segment | caps a large dump whose middle held a unique fact -> reread/loop |
| **RETRIEVABLE_REFERENCE** | replace large recoverable output w/ a pointer ("re-run X to see") | content-stable | low IF deterministically refetchable | yes | refetch cost (1 extra call) | shim + recompute hook | segment | content was NOT cheaply refetchable, or agent doesn't re-fetch |
| **EXTERNALIZE** | move superseded state to external store, keep handle | content-stable | low IF superseded & retrievable | yes | fetch from store | external KV store | segment | externalized state was still live |
| **KEEP_FULL_CONTENT** | none (explicit retention) | preserves | none | n/a | n/a | none | segment | over-retention (cost) when content was prunable |
| **REHYDRATE** | re-insert previously-removed content | restores info; **busts cache** (prefix change) | reduces drift risk | n/a | cache recreation | shim + retained originals | segment | rehydration too late (agent already looped) |
| **START_NEW_PREFIX_EPOCH** | deliberate cache reset + compaction | resets cache (1 creation) then stable | medium | partial | one full re-cache | shim | task | epoch reset cost > savings if horizon short |
| **PRESERVE_PREFIX** | avoid any mid-prefix mutation | preserves cache (cheap reads) | none | n/a | n/a | shim discipline | task | forgoes saving on genuinely redundant content |
| **ROLLBACK** | undo a speculative action after harm detected | restores pre-action state; busts cache | recovers quality | n/a | recreation + wasted action | shim + checkpoint | event | rollback after the harm already propagated (too late) |

## Mechanism groupings
- **Cache-stable removers** (LINE_DEDUP, GENTLE_CAP, RETRIEVABLE_REFERENCE, EXTERNALIZE): remove content without rewriting the cached prefix span. Differ in *what* they remove (redundant vs recoverable vs superseded vs truncated) -> different intelligence-tax risk.
- **Cache-busting** (REHYDRATE, START_NEW_PREFIX_EPOCH, ROLLBACK): change the cached prefix -> incur cache_creation tax (proven by CACHE_TAX_CAUSALITY). Used as recovery/feedback actions, not routine optimization.
- **Null/retain** (NO_OP, KEEP_FULL_CONTENT, PRESERVE_PREFIX): the safe defaults.

## Executable in first experiment (Phase 8 MRT)
- NO_OP ✅, LINE_DEDUP ✅ (line_level_dedup), GENTLE_CAP ✅ (cap_all_obs 6k), RETRIEVABLE_REFERENCE ✅ (retrieval_ref_large).
- EXTERNALIZE / REHYDRATE / ROLLBACK: defined but require runtime support (external store, checkpoint/replay) NOT yet built — Phase 10 roadmap.

## Why the ontology matters
The prior failure lumped all removal as "pruning." This ontology says: LINE_DEDUP (remove redundant) and GENTLE_CAP (truncate, may remove unique) are *different actions with different intelligence-tax risk* — the INTELLIGENCE_TAX_CAUSALITY result (drift caused by removing unique content, dose-controlled) predicts they should have different effects conditional on segment content. That is the action-specificity the new study tests.
