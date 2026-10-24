# Prior art: what others have built, and what we take from it

Scanned on Oct 24, ~11:20. Purpose: borrow proven mechanics, avoid known failure modes, and have
answers ready when the board asks "why did you build it this way?"

## 1. The landscape in one table

| Work | What it is | What we take |
|---|---|---|
| [Generative Agents](https://arxiv.org/abs/2304.03442) (Park et al., 2023; [code](https://github.com/joonspk-research/generative_agents)) | 25 agents in a sandbox town. Each has a **memory stream**, **retrieval** by recency × importance × relevance, periodic **reflection** that turns memories into higher-level beliefs, and planning. Ablations: removing observation, reflection or planning each cuts believability. | Per-persona memory that carries across weeks; a cheap weekly "reflection" line ("what I now believe about Cobalt"). |
| [Generative Agent Simulations of 1,000 People](https://arxiv.org/abs/2411.10109) (Park et al., 2024; [code](https://github.com/joonspk-research/genagents)) | Agents built from 2-hour interviews reproduce people's survey answers at ~85% of human test-retest consistency. Rich narrative beats demographic labels and **reduces bias across groups**. | Personas as a narrative with a life story, not a list of attributes. |
| [OASIS](https://arxiv.org/abs/2411.11581) (CAMEL-AI; [code](https://github.com/camel-ai/oasis)) | Twitter/Reddit simulator up to 1M agents; 23 actions; recommendation feed; reproduces information spread, polarization, herd effects. | A social feed between personas: posts from week N are visible to connected personas in week N+1. |
| [TinyTroupe](https://github.com/microsoft/TinyTroupe) (Microsoft, started as an internal hackathon) | Persona JSON spec (identity, goals, occupation, style, Big Five, beliefs), `TinyWorld.run(n)`, `ResultsExtractor` to pull structured results, **LLM call cache** so re-runs are cheap and reproducible. Explicit stance: outputs are for insight generation, not direct decisions. | JSON persona spec; call cache keyed on prompt+seed; a results extractor step. |
| [Concordia](https://arxiv.org/abs/2312.03664) (DeepMind; [code](https://github.com/google-deepmind/concordia)) | **Game Master** pattern: agents say what they do in natural language, a GM decides what actually happens and narrates consequences. | A thin "world" step that resolves actions (support wait, transfer failed during migration) and writes the consequence into next week's prompt. |
| [Bank Run, Interrupted](https://pubsonline.informs.org/doi/10.1287/mnsc.2024.06807) (Kazinnik, *Management Science*) | Synthetic depositors see a viral panic post; bank messages are randomized. **Direct, personalized messages with strong reassurance and explicit "we will be fine" clauses cut withdrawal intent substantially.** Withdrawal propensities are then spread over a proximity network. | Our decisions' `message` text is a first-class experimental variable: test wording variants, not just actions. |
| [Social Contagion and Bank Runs](https://arxiv.org/abs/2602.15066) (Rajan & Ruaño, 2026) | ABM with LLM depositors (gpt-4.1-mini, T=0.7). Each agent: risk tolerance, weight on fundamentals α, weight on social info β, insured/uninsured. Sees fundamentals + last round's withdrawal rate + neighbors' posts (one-round lag). Outputs **withdraw/stay + optional post**. Heavy-tailed core–periphery network. Insured withdraw 34.5%, uninsured 81.3%. Few-shot examples made it *worse*. Invalid output defaults to "stay" (a bias they flag). | Exactly our shape: structured decision + optional post, one-week lag, heavy-tailed network, insured-limit awareness (dossier attribute "knows the FDIC limit"). |
| Census-grounded personas ([Agentic Society](https://arxiv.org/abs/2409.10550), [Scaling Law in Simulated Personality](https://arxiv.org/abs/2510.11734), [CivicSim](https://www.ischool.berkeley.edu/projects/2026/civicsim-synthetic-personas-inclusive-policy-testing)) | Sample a demographic "skeleton" from Census/ACS first (ideally joint, not marginal, distributions), then let the LLM write the texture. Validate the narrative didn't drift from the skeleton. Weight agents to population with integer replication. | Our persona generator: skeleton sampled from our chosen distributions → LLM narrative → check the narrative keeps the skeleton → `weight_customers`. |
| [BehaviorLens](https://github.com/meryemsakin/BehaviorLens) (2026, pre-registered) | LLM personas vs. real retail purchases. **Personas over-predicted demand (52% vs 33% observed), did worse than the raw record they were written from, ranked campaigns badly (ρ = −0.10)**; gradient boosting beat every LLM condition. Calibration narrowed but didn't close the gap. | Trust **direction and ranking** between runs, not absolute levels. Say this out loud in `CLIENT_MEMO.md`. |

## 2. Failure modes everyone hits

1. **Over-optimism / social desirability.** LLMs skew Likert answers to the "good" end and over-predict
   buying and loyalty ([Big Five study](https://arxiv.org/abs/2405.06058), BehaviorLens). Our probe
   scores will start high; the useful number is the *change* and the *gap between runs*.
2. **Homogenization.** Models drift to the modal answer; subgroup differences vanish
   ([ANES study](https://arxiv.org/abs/2507.02919), ["heterogeneity masking"](https://www.alphaxiv.org/overview/2604.06663)).
   Fix: strong, specific personas with a stance and a history; segment by group when reporting.
3. **Inflated effect sizes.** Replications reproduce the direction but with bigger effects than humans
   ([mobilization experiment](https://neurips.cc/virtual/2026/171745)). Expect our decisions to look
   more powerful than they are.
4. **Belief drift / over-updating.** Agents update beliefs faster than people, and drift over many
   steps ([belief update study](https://arxiv.org/pdf/2607.28347)). With 10 weeks and a social feed,
   cascades are the risk the organizers warn about ("half the customers leave in a week").
5. **Option-order and recency bias.** Models favor the last-listed option ([prompt perturbations](https://arxiv.org/html/2507.07188v3)).
   Keep status options in the same order everywhere and don't put "left" last... or do, consistently,
   and know it.
6. **Fallback bias.** Invalid output → default status silently biases results (bank-run ABM). Retry on
   invalid JSON; never default.
7. **Few-shot examples anchor.** The bank-run paper dropped them because they reduced realism.

## 3. What we build (recommendations)

### Personas (workstream B)
- **Skeleton → narrative → check.** Sample attributes from distributions we justify (dossier numbers
  first, ACS for age/income/occupation, our own guesses stated as guesses), then one LLM call writes a
  first-person life story, then a cheap check that the story kept the skeleton.
- **Each persona gets a stance and a scar:** why they chose Cobalt, one past bad experience (with
  Cobalt or a rival), their main fear this quarter. This is what fights homogenization.
- **Weights match the dossier:** 2.1M customers, $6.0B deposits with ~50% in the top 5%, 310k paycheck,
  42k card readers. Savers are few personas with huge `weight_deposits`; everyday customers many
  personas with small weights. Weights are integers ("stands for 60,000 customers").
- **Insured-limit awareness** (`knows the FDIC limit`) as a real attribute: in both bank-run papers it is
  the single biggest split in behavior.

### World (workstream C)
- **Game-master step** resolves what each action actually did: during migration week, "transfer" →
  "failed, app read-only"; "call support" → wait time depends on extra-staff decision; "post" → goes
  into next week's feed. The consequence is text in next week's prompt.
- **Memory = a rolling summary + last 2 weeks verbatim** (not the full history: prompt size and
  speed). One line of "reflection" per week: "what I now believe about Cobalt."
- **Social feed with a one-week lag** over a fixed heavy-tailed network generated with the personas
  (opinion leaders have more followers). Each persona sees ≤ 5 posts from its own neighbors, plus one
  "what's trending" line. Posts are the persona's own words, never the company message verbatim.
- **Rivals act on the known date:** a rival rate offer appears in the feed around week 5–6 (dossier:
  "rivals know the date too").

### LLM calls (workstream A)
- **One structured call per persona per week** (`response_mime_type="application/json"` + schema):
  `feeling`, `actions[]`, `post` (nullable), `status`, `money`, `reflection`, and a final plain-text
  line `Status: <status>` for the checker.
- **Retry on invalid output; never default.** Log every attempt to `calls.jsonl`.
- **Cache keyed on (prompt, model, seed)** so re-running after a late announcement only recomputes
  weeks whose prompts changed.
- No few-shot examples. Temperature 1.0 as the brief suggests; seed per run.

### Metrics (workstream F)
- Report **deltas between runs**, not levels: `plan − nodecision` is the number the board can use.
- Translate behavior to goals with explicit, written formulas (e.g. active = status ≠ dormant/left;
  deposits = Σ weight_deposits × money factor {kept: 1.0, moved some: 0.6, moved most: 0.1}; rating =
  4.6 + f(share who post a review and its sentiment); CFPB = 120 × (regulator complaints / baseline)).
  Those factors are assumptions: list them in `TEAM_DOC.md`.
- **Sanity anchors:** a quiet week should keep ≈100% / 100% / 4.6 / 120. If `nodecision` collapses,
  the sim is wrong, not the bank.

### Experiments (Phase 3)
- Vary the **message wording** as much as the actions: the Kazinnik paper's main finding is that the
  words matter (direct, personal, concrete reassurance with a commitment).
- Compare by **ranking** across ≥ 2 seeds; don't quote a single-seed level.

### What we tell the board it cannot tell (jury criterion 5)
- Absolute levels (over-optimism, inflated effects): directions and rankings only.
- Anything about customers unlike our 30–40 personas; no real behavioral data to calibrate against.
- Rare tail events (fraud wave, regulator action) that none of our personas would generate.
- Next step with more time: calibrate factors on Cobalt's real complaint and churn history, run
  hundreds of personas, hold out a real past incident and check the sim reproduces its direction.

## Sources
- [Generative Agents (2023)](https://arxiv.org/abs/2304.03442) · [genagents / 1,000 people (2024)](https://arxiv.org/abs/2411.10109) · [Stanford HAI summary](https://hai.stanford.edu/news/ai-agents-simulate-1052-individuals-personalities-with-impressive-accuracy)
- [OASIS paper](https://arxiv.org/abs/2411.11581) · [camel-ai/oasis](https://github.com/camel-ai/oasis)
- [microsoft/TinyTroupe](https://github.com/microsoft/TinyTroupe) · [Concordia paper](https://arxiv.org/abs/2312.03664)
- [Bank Run, Interrupted (Kazinnik)](https://digitaleconomy.stanford.edu/publication/bank-run-interrupted-modeling-deposit-withdrawals-with-generative-ai) · [Social Contagion and Bank Runs (2026)](https://arxiv.org/abs/2602.15066)
- [Agentic Society (census skeleton)](https://arxiv.org/abs/2409.10550) · [Scaling law in simulated personality](https://arxiv.org/abs/2510.11734) · [LLM Generated Persona is a Promise with a Catch](https://arxiv.org/abs/2503.16527) · [CivicSim](https://www.ischool.berkeley.edu/projects/2026/civicsim-synthetic-personas-inclusive-policy-testing)
- [BehaviorLens](https://github.com/meryemsakin/BehaviorLens) · [Social desirability in LLM surveys](https://arxiv.org/abs/2405.06058) · [Homogenization on ANES](https://arxiv.org/abs/2507.02919) · [Heterogeneity masking](https://www.alphaxiv.org/overview/2604.06663) · [Prompt perturbations / recency bias](https://arxiv.org/html/2507.07188v3) · [Belief-update drift](https://arxiv.org/pdf/2607.28347) · [Mobilization experiment lessons](https://neurips.cc/virtual/2026/171745) · [Social simulations require a boundary](https://arxiv.org/pdf/2506.19806)
