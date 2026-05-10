# Lessons

## Mistake 1: trusted a prior-session "to verify" note as if it were a fact

**What happened**: an earlier addendum recorded an enum value as a guess with the explicit annotation "verify in next session". The next session treated it as verified and burned three deploy+test cycles before consulting the source. The guessed values (`anyFilter`, `allFilters`) were both rejected at runtime; the real enum values (`anyCondition`, `allConditions`) were one HTTP fetch away in the upstream repository's source file.

**Root cause**: prior-session notes carry a tone of confidence that hides their epistemic status. Any note marked "to verify", "pending", "hypothesis", "needs check" is a hypothesis, not a fact, regardless of the surrounding tone.

**Rule**: **never deploy a configuration value sourced from a prior-session note without re-verifying it against the upstream source first.** For open-source tools, the source repository (constants files, type definitions) is authoritative. For closed-source tools, the official docs are. If neither is conclusive, ask the user before consuming tokens on trial-and-error.

---

## Mistake 2: built a parser against a synthetic format the real input does not match

**What happened**: a regex parser was designed against a hand-constructed fixture that assumed a flat, single-line layout (`Field: value Field2: value2 ...`). The real source PDFs use a columnar transposed layout where field labels live on a header row and values live on subsequent rows aligned by spatial position. The parser passed every test against the synthetic fixture and produced zero claims when confronted with a real document.

**Root cause**: synthetic fixtures encode the developer's mental model of the format, not the format itself. They validate that the parser does what was intended, not that the intent matches reality.

**Rule**: **always obtain a real sample of the target document before designing extraction logic.** If a real sample is not available at design time, mark the parser as "specification-only" and block production use until validated against a real fixture. Treat the validation gate as part of the definition of done.

---

## Mistake 3: trusted a markdown converter to preserve tabular layout

**What happened**: a generic Markdown converter was used to extract PDF text for parsing. It produced linear, reading-order text that destroyed the spatial relationships between header labels and their column values. Same data, irrecoverable structure.

**Root cause**: Markdown converters target reading order, not spatial fidelity. For tabular sources, reading order is the wrong abstraction.

**Rule**: **always verify that the extraction tool preserves the structure your parser depends on, before designing the parser around it.** If the parser needs columns, the extractor must surface columns (coordinate-aware tools do this). If the parser only needs prose, any text extractor works.

---

## Mistake 4: assumed the SDK validator would catch runtime-fatal errors

**What happened**: a workflow validation returned `valid: true` with cosmetic warnings. The workflow was deployed, executed, and crashed at runtime with `unexpected match type`. The validator's `valid: true` was correct in scope (the SDK schema accepts the value as well-typed) but did not validate against the runtime's enum.

**Root cause**: validators check what they are designed to check. A schema validator does not run the workflow. A type checker does not exercise the runtime branches.

**Rule**: **never treat `valid: true` from a static validator as proof of runtime correctness.** Always run a smoke test before declaring a deploy successful. Idempotency, in particular, must be verified by running the workflow twice and inspecting downstream state — not by reading the configuration.

---

## Mistake 5: did not separate strategy/architecture decisions from runtime fixes in the same document

**What happened**: a single addendum file accumulated runtime fixes, hypotheses, decisions, and known issues over multiple sessions. New entries appended without clearly labeling their epistemic status. By session 3, the file mixed verified facts with unverified hypotheses with the same formatting weight, and the next agent (or the same agent on a fresh session) could not tell them apart at a glance.

**Root cause**: documents that grow over time degrade unless every section explicitly carries its provenance and verification state.

**Rule**: **every claim in a multi-session document must carry a verification tag** — `[verified <date>]`, `[hypothesis]`, `[deprecated]`. When a hypothesis is verified or refuted, update the tag rather than adding a new entry. The reader of the document tomorrow has none of the conversation context the writer has today.

---

## Validated assumptions worth recording

- **Deterministic hashing on `(filename, filesize)` tuples is a sufficient `batch_id` strategy** for use cases where re-running with the same input must produce the same outcome and not double-write. Confirmed by running the same input twice and verifying primary key and `createdAt` preservation.

- **Three parallel branches off a single parser node are the right shape** when the parser emits three semantic streams (records, errors, summary). Sequential chaining causes item multiplication; parallel branches with `executeOnce` on the summary leg keeps cardinality correct.
