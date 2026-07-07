from models import StudentSession, Exam, ExamResult, ExamPsychology, LearningStyle
from rule_engine import RuleEngine
er = ExamResult(exam_type=Exam.SAT, mock_score=1020)
er.correct_by_skill = {'Inferences': 2, 'Command of Evidence': 3, 'Nonlinear Functions': 2, 'Linear Functions': 7}
er.wrong_by_skill = {'Inferences': 6, 'Command of Evidence': 5, 'Nonlinear Functions': 5, 'Linear Functions': 2}
er.total_correct = sum(er.correct_by_skill.values())
er.total_questions = er.total_correct + sum(er.wrong_by_skill.values())
session = StudentSession(student_name='Sample Student', target_exam=Exam.SAT, exam_result=er, psychology=ExamPsychology(stress_before_exam=8.5, sleep_quality=8.0, in_exam_anxiety=8.0), learning_style=LearningStyle(rote_memorization=8.5, cramming=9.0, no_practice_tests=7.5))
report = RuleEngine().diagnose(session)
print(f'{report.student_name} ({report.exam_type}) — {report.overall_status}\n')
for d in report.diagnostics:
    print(f'{d.severity} [{d.category}] {d.warning}')
    print(f'   -> {d.suggestion}')
    if d.evidence:
        print(f'   evidence: {d.evidence}')
print('\nStudy priorities (weakest first):')
for p in report.study_priorities:
    print(f'  {p.urgency}: {p.skill_name} — {p.accuracy_pct}% ({p.n_correct}/{p.n_correct + p.n_wrong})')
