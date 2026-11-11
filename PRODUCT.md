# Acadza Report → Fix — Product Thinking

## 1. Who loses the most when a question is broken?

The student who trusts the question bank and uses it to judge their understanding loses the most. An incorrect answer key can penalise a student who reasoned correctly; an ambiguous or unsound question can waste preparation time and teach the wrong lesson. The impact is especially serious when students are practising independently and have no teacher immediately available to challenge the material.

The design treats reports as evidence to investigate, not instructions to obey. Reports are grouped by question so multiple reports about the same item are considered together without creating duplicate review work. The system records a verdict, supporting evidence, confidence, repair type, proposed edit, and route. Clear cases can proceed only within the automation rules defined by the taxonomy and validation layer. Uncertain or high-impact cases are sent to faculty review. A proposed correction is not silently treated as a confirmed correction, and the audit trail preserves the decision history. The generated student reply also gives the team a consistent way to explain the outcome.

## 2. What should AI never auto-apply?

The taxonomy is the source of truth. AI must never auto-apply a repair type marked `"auto": false`. It may identify the suspected issue and prepare a recommendation, but the change must wait for faculty approval. In the current taxonomy these repair types are `identical_options`, `diagram`, `wrong_question`, `unsound`, `wrong_chapter`, and `syllabus`.

These cases can involve creating or changing question content, interpreting visual material, judging whether a question is valid, or making a curriculum decision. A plausible-sounding model response is not enough to make those changes safely. The rule is enforced by the deterministic safety layer, not left to the model's judgement.

An `"auto": true` flag is permission to consider automation, not a guarantee that a change will be applied. The proposed edit must still use an allowed field, be supported by the source material, and pass validation. In particular, an answer-key correction requires separate verification; when verification is unavailable, inconclusive, or fails, the case stays with faculty. Missing source information must not be invented to make an edit appear complete.

## 3. One metric to watch in week one

**Median time from a report entering the review queue to an evidence-backed disposition.** This measures whether the workflow helps the team resolve or route reported problems faster. I would establish a baseline in the first week and inspect delayed cases before setting a target; speed matters only when the decision remains reliable.

## 4. One idea beyond the brief: a Question Health Ledger

Give each question a versioned history of reports, decisions, approved edits, and the reason for each change. After a correction is approved, make the updated status and a short explanation available to the instructors and learners who used that version. This builds on the audit trail already present in the workflow and gives Acadza a longer-term feedback loop: students can see that reports lead to action, faculty can trace why a decision was made, and recurring defects become easier to identify.
