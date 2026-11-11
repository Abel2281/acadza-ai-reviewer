# Acadza AI Triage System — Product Architecture & Thinking

---

### 1. Who loses the most when a question is broken, and how our design reflects that

The biggest loser is **the serious, borderline student** who solved the problem correctly under timed test pressure, only to receive a negative mark due to an erroneous answer key. In high-stakes examinations like JEE Advanced or NEET, where 1 mark separates thousands of ranks and determines college admission, an erroneous key doesn't just miscalculate a score—it erodes the student's conceptual confidence right before the exam.

Our design directly reflects this asymmetry:
- **Urgency-Ranked Queue**: Questions flagged with answer-key defects or multiple student reports bypass single-student cosmetic reports and float immediately to the top of the faculty queue.
- **Student Leads as Evidence, Not Instructions**: When three stressed 17-year-olds flag the LCR circuit (`60f744b3f1b9bc7cc7b4a949`), our system aggregates their independent signals to escalate urgency, but verifies the physical derivation from first principles.
- **Empathetic Student Replies**: Students receive an immediate, respectful reply clarifying whether their math was verified or explaining the subtle distinction (e.g. significant figures on `68dea715387eea3d0d95f790`), preventing conceptual self-doubt.

---

### 2. What we would NEVER let the AI auto-apply, and why

We strictly prohibit automated application (`auto: false` in `taxonomy.json`) for:
1. **`identical_options` & `unsound`**: Fabricating plausible distractors or fixing mathematically unsound questions requires pedagogical authorship. A hallucinated distractor could introduce ambiguity or make multiple options correct.
2. **`diagram`**: Inserting or altering geometric figures and circuit diagrams requires accurate graphical assets. LLMs cannot reliably author clean, vector-accurate engineering diagrams without visual faculty inspection.
3. **`wrong_question`**: Replacing an entire mismatched solution requires disciplinary mastery to ensure the explanation matches the intended curriculum nuance.
4. **`wrong_chapter` & `syllabus`**: Curricular taxonomy changes impact coaching test series syllabus mappings across hundreds of partner institutes.

Our deterministic safety layer rejects any attempt to auto-apply these categories regardless of model confidence.

---

### 3. One metric we would watch in week 1

**Post-Resolution Report Recurrence Rate (PRRR)**:
$$\text{PRRR} = \frac{\text{Questions receiving new reports within 7 days of an auto-applied fix}}{\text{Total auto-applied fixes}}$$

A high PRRR indicates that our automated triage introduced secondary errors (e.g. fixing a typo but corrupting a formula or replacing a key with another flawed option). If PRRR exceeds 1.5%, all auto-apply permissions are immediately throttled to mandatory human review.

---

### 4. One pitch beyond this brief: Automated Distractor Discrimination Index (ADDI)

Beyond passive report triage, we pitch **Proactive Distractor Quality Profiling**:
Instead of waiting for students to tap "Report Error", we analyze real student test response distributions across Acadza's 8 lakh questions. If a question exhibits an anomaly—such as top-decile students disproportionately selecting unkeyed Option D, or Option B receiving 0% selections across 10,000 attempts—the system automatically flags the question as a suspected key error or bad distractor. The AI pre-generates a candidate fix before students even feel the pain.

