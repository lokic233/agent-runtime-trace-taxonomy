# TraceController Go/No-Go — Hostile-Committee Memo

Decision: **C_NO_USEFUL_PARITY** · signal learning proceed: **False**.
Existence probe on existing paid data (analysis-only; no new trajectories run). Primary objective =
task-total effective cost under a frozen quality-loss tolerance.

**1. Does the action ladder create a real cost-quality tradeoff?**
Weakly. Direct token savings and cache behavior differ by dose, but on TASK-TOTAL cost the aggressive
end loses to the cache tax, and quality falls monotonically with dose. The tradeoff favors KEEP/low-dose.

**2. Does the optimal action change across tasks/states?**
No credibly. Naive per-task argmin is mixed (M6x19, M4x15, KEEP x11, M7x5) but this is a min over
single NOISY draws. 0/50 tasks show a stable crossing above the SHAM noise floor.

**3. Does the optimal action change across tolerance levels?**
No. KEEP is best static at eps in {0,0.02,0.05,0.10}; tolerance is not binding (quality barely
differs across actions).

**4. Naive oracle gap:** ~15% (provider-$ proxy, ladder, eps=0.05).

**5. Conservative bias-corrected oracle gap:** **~0%** — indistinguishable from the noise floor. A
byte-identical NO_OP (SHAM) manufactures a 40.6% gap at the observed noise sigma; the observed gap is
below that.

**6. Is the gap large enough to justify a controller?** No.

**7. Stable across repeated runs?** Cannot be — there is 1 rep/cell and the SHAM control shows a
median 31% run-to-run cost swing. No repetition evidence supports any ranking.

**8. Stable across repositories?** The NOISE gap is repo-stable (LORO 18-24%), which is NOT evidence
of parity — repo-stable noise is still noise.

**9. How much explained by cache-tax amortization?** Substantially. Aggressive recency net saving is
negative on 9/10 tasks; cache ratio collapses 11.8 -> 0.37. Cache tax dominates direct saving.

**10. How much by rework/recovery?** Not separately identified (rework proxies not logged), but
aggressive-action quality regressions (M7: 5 vs C0) indicate a rework/quality cost at higher dose.

**11. Does any action dominate almost everywhere?** Yes — KEEP (A0) / low-dose dominates on
task-total cost after taxes and on quality.

**12. Should signal learning proceed?** **No.**

**13. Which action family to retain?** A1 prefix-preserving LINEDEDUP as a STATIC primitive.

**14. Which to kill?** A2/A3 aggressive/recency compaction as adaptive-controller candidates.

**15. Strongest claim the paper may safely make:**
> "Visible token reduction is not equivalent to runtime cost reduction: prefix-cache destruction and
> trajectory rework reverse apparent savings. Evaluating a dose-ordered action family by task-total
> effective cost and quality, we find that for this family one static low-dose policy dominates after
> cache and trajectory effects. Apparent per-task action crossings do not exceed the run-to-run noise
> floor established by a byte-identical control, leaving insufficient oracle headroom to justify
> trace-conditioned adaptive control. Prefix-preserving line-deduplication is retained as a static
> optimization primitive."

**Caveats a reviewer can still raise:** provider-$ proxy (not the exact custom cost) for the 6x50
matrix; single rep/cell; exact cache-aware cost + SHAM floor available for only 10 tasks. These are
disclosed; the negative is robust because the observed gap is below even the generous-proxy noise null,
and the exact-cost cache-amortization sub-analysis independently agrees. **The committee's preference
for a credible negative over a fragile positive is satisfied.**
