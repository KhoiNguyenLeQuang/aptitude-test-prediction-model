# Student Skill Diagnostic Engine

An open-source, rule-based diagnostic engine for SAT / IELTS prep. Feed it a
student's per-skill exam results — optionally with self-reported psychology
and study-habit scores — and it returns a prioritized, evidence-backed
revision plan: which skill types are critically weak, which warning patterns
are firing, and what to work on first.

## What's included

| File | Purpose |
|---|---|
| `sat.py` | Standalone CLI: reads an intake spreadsheet, prints a per-skill accuracy report per student (weakest skills first, with bar charts) |
| `rule_engine.py` | The core diagnostic algorithm: skill-gap detection, psychology / study-habit / environment warnings, and multi-factor combo pattern detection |
| `models.py` | Plain dataclasses: `StudentSession`, `ExamResult`, `ExamPsychology`, `LearningStyle`, `TeacherObservation` |
| `example.py` | Minimal runnable example — build one student in code, print the full diagnosis |
| `student_intake.xlsx` | Intake spreadsheet template (one column per student) |

## Quick start

```bash
pip install openpyxl
python example.py                    # diagnosis demo, no spreadsheet needed
python sat.py student_intake.xlsx    # per-skill accuracy report from a filled sheet
```

Example `sat.py` output:

```
=== Alice (SAT) ===
   20.0%  ████                 Right Triangles & Trig  (1/5)
   25.0%  █████                Inferences  (2/8)
   37.5%  ████████             Command of Evidence  (3/8)
   88.9%  ██████████████████   Linear Equations (1 var)  (8/9)
  Overall accuracy: 45.7%  |  Weakest first — start revising from the top.
```

## How the algorithm works

1. **Skill gaps.** Every skill type is scored by accuracy. Below 40% is
   critical (priority 1), below 60% is weak (priority 2). Each flag carries
   its evidence (`correct/total`) so the output is auditable.

2. **Single-factor rules.** Psychology and study-habit indicators (1–10
   scale, 10 = worst) fire warnings against two thresholds: HIGH = 7.5 and
   MED = 5.5.

3. **Combo patterns.** The interesting part. Some risks only exist when
   factors co-occur — e.g. heavy rote memorization *combined with* weakness
   in two or more inference-type reading skills is a fundamentally different
   problem than either signal alone, and gets a different intervention.

Everything is deterministic: same input, same output, every rule explainable.
There is no ML in this repository by design — a rule engine you can read and
audit is the right foundation, and thresholds you can see beat a black box
you can't.

## Data format

`sat.py` and the template use one column per student (column C onward). Rows
are matched by **label text**, not position, so you can reorder or insert
rows freely. Input is validated: `correct > total`, zero totals, and unknown
exam types produce warnings instead of silent wrong numbers.

To use `rule_engine.py` directly, build a `StudentSession` in code — see
`example.py`. All psychology / habit / teacher sections are optional; the
engine diagnoses with whatever data exists and reports what's missing.

## A note on the psychology indicators

The 1–10 self-assessment scores exist to flag exam-stress patterns for a
*teacher* to follow up on. They are not clinical instruments, and this
engine does not diagnose anything about a student's mental health. If
multiple indicators are simultaneously severe, the right response is a
caring human conversation — treat the engine's output as a pointer, never
a verdict. If you collect this data, restrict access to it and get
appropriate consent; it is sensitive information about (usually) minors.

## Scope of this repository

This is the open-source core of a larger system. Adaptive threshold
learning, score prediction models, and reporting layers built on top of this
engine are not part of this release. The interfaces here (`StudentSession`
in, `DiagnosisReport` out) are stable extension points — build your own
layers on top.

## License

MIT — see `LICENSE`.

## Credits

This project exists thanks to:

- **Le Truong Hai Tran** (tranletruonghai@gmail.com) — tree model selection & score prediction co-build
- **Gia Vinh Nguyen** (giavinh11012009@gmail.com) — psychology indicators & rule-based engine
- **Bao Chau Ngo** (ngobaochau1312@gmail.com) — aptitude test indicators & rule-based engine
- **Tien Thanh Le** (thor.le1234@gmail.com) — aptitude test indicators & rule-based engine, tree model selection & score prediction co-build
