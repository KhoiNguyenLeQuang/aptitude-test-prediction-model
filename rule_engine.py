from dataclasses import dataclass, field
from typing import Optional
from models import StudentSession, Exam
DEFAULT_HIGH = 7.5
DEFAULT_MED = 5.5

@dataclass
class DiagnosticItem:
    severity: str
    category: str
    warning: str
    suggestion: str
    evidence: str = ''
    threshold_used: Optional[float] = None
    threshold_method: str = ''

@dataclass
class StudyPriorityItem:
    skill_name: str
    accuracy_pct: float
    n_wrong: int
    n_correct: int
    urgency: str

@dataclass
class DiagnosisReport:
    student_name: str
    exam_type: str
    mock_score: Optional[float]
    overall_status: str
    data_sources: dict
    diagnostics: list = field(default_factory=list)
    study_priorities: list = field(default_factory=list)
    teacher_flags: list = field(default_factory=list)
    threshold_summary: dict = field(default_factory=dict)

class RuleEngine:
    SKILL_CRITICAL = 40.0
    SKILL_WEAK = 60.0

    def __init__(self):
        self._used_features = set()

    def _th(self, feature_key: str) -> tuple:
        self._used_features.add(feature_key)
        return (DEFAULT_HIGH, DEFAULT_MED, 'static')

    def diagnose(self, session: StudentSession) -> DiagnosisReport:
        self._used_features = set()
        report = DiagnosisReport(student_name=session.student_name, exam_type=session.target_exam.value, mock_score=session.exam_result.mock_score if session.has_exam_data() else None, overall_status='', data_sources=session.data_completeness())
        if session.has_exam_data():
            self._rules_knowledge_gaps(session, report)
        if session.has_psychology_data():
            self._rules_psychology(session, report)
        if session.has_learning_data():
            self._rules_learning_style(session, report)
        self._rules_combos(session, report)
        if session.has_teacher_data():
            self._rules_teacher(session, report)
        report.overall_status = self._overall_status(report)
        report.threshold_summary = {feat: (DEFAULT_HIGH, DEFAULT_MED, 'static') for feat in self._used_features}
        return report

    def _rules_knowledge_gaps(self, session: StudentSession, report: DiagnosisReport):
        er = session.exam_result
        all_skills = set(list(er.correct_by_skill) + list(er.wrong_by_skill))
        for skill in all_skills:
            acc = er.skill_accuracy(skill)
            if acc is None:
                continue
            n_correct = er.correct_by_skill.get(skill, 0)
            n_wrong = er.wrong_by_skill.get(skill, 0)
            n_total = n_correct + n_wrong
            if acc < self.SKILL_CRITICAL:
                urgency = 'Ưu tiên 1'
                report.diagnostics.append(DiagnosticItem(severity='🔴 NGUY CẤP', category='Kiến thức', warning=f"Dạng bài '{skill}' rất yếu", suggestion=f"Dành 60% thời gian ôn tập cho '{skill}'. Tìm 30–50 câu luyện tập dạng này trước khi chuyển sang skill khác.", evidence=f'Đúng {n_correct}/{n_total} câu ({acc}%)', threshold_used=self.SKILL_CRITICAL, threshold_method='fixed_pct'))
            elif acc < self.SKILL_WEAK:
                urgency = 'Ưu tiên 2'
                report.diagnostics.append(DiagnosticItem(severity='🟠 CẦN XỬ LÝ', category='Kiến thức', warning=f"Dạng bài '{skill}' cần củng cố", suggestion=f"Luyện thêm 20–30 câu dạng '{skill}'. Xem lại lý thuyết cốt lõi của dạng này.", evidence=f'Đúng {n_correct}/{n_total} câu ({acc}%)', threshold_used=self.SKILL_WEAK, threshold_method='fixed_pct'))
            else:
                urgency = 'Ôn thêm'
            report.study_priorities.append(StudyPriorityItem(skill_name=skill, accuracy_pct=acc, n_wrong=n_wrong, n_correct=n_correct, urgency=urgency))
        report.study_priorities.sort(key=lambda x: x.accuracy_pct)
        critical_skills = [p for p in report.study_priorities if p.urgency == 'Ưu tiên 1']
        if session.target_exam == Exam.SAT and er.mock_score < 1000 and (len(critical_skills) >= 4):
            report.diagnostics.insert(0, DiagnosticItem(severity='🔴 NGUY CẤP', category='Kiến thức', warning='Điểm SAT dưới 1000 và hổng nhiều dạng bài — cần restructure toàn bộ study plan', suggestion="Không ôn theo kiểu 'giải đề'. Phải quay lại build từng skill từ đầu, có timeline rõ ràng: 2 tuần/skill.", evidence=f'Mock score: {er.mock_score} | {len(critical_skills)} dạng bài dưới 40%'))
        elif session.target_exam == Exam.IELTS and er.mock_score < 5.5 and (len(critical_skills) >= 3):
            report.diagnostics.insert(0, DiagnosticItem(severity='🔴 NGUY CẤP', category='Kiến thức', warning='Điểm IELTS dưới 5.5 và hổng nhiều dạng bài — cần restructure toàn bộ study plan', suggestion='Ưu tiên Reading + Listening trước (dễ nâng điểm nhất). Writing Task 2 và Speaking cần thời gian dài hơn.', evidence=f'Mock score: {er.mock_score} | {len(critical_skills)} dạng bài dưới 40%'))

    def _rules_psychology(self, session: StudentSession, report: DiagnosisReport):
        p = session.psychology
        stress_high, _, stress_m = self._th('psych_stress_before_exam')
        expect_high, _, expect_m = self._th('psych_self_expectation')
        if p.stress_before_exam >= stress_high and p.self_expectation >= expect_high:
            report.diagnostics.append(DiagnosticItem(severity='🔴 NGUY CẤP', category='Tâm lý', warning='Áp lực thi cử & kỳ vọng bản thân đều rất cao — nguy cơ overthink, performance anxiety, và block khi gặp câu khó.', suggestion="Luyện kỹ thuật thi thật: sau mỗi mock test, practice 'bỏ câu khó, làm câu dễ trước'. Dùng kỹ thuật thở 4-7-8 trước khi thi.", evidence=f'Stress: {p.stress_before_exam}/10 (ngưỡng {stress_high}) | Kỳ vọng: {p.self_expectation}/10 (ngưỡng {expect_high})', threshold_used=stress_high, threshold_method=stress_m))
        sleep_high, sleep_med, sleep_m = self._th('psych_sleep_quality')
        if p.sleep_quality >= sleep_high:
            report.diagnostics.append(DiagnosticItem(severity='🔴 NGUY CẤP', category='Tâm lý', warning='Thiếu ngủ nghiêm trọng — ảnh hưởng trực tiếp đến trí nhớ ngắn hạn và tốc độ xử lý trong phòng thi.', suggestion='Ngủ đủ 7-8h, đặc biệt 1 tuần trước thi. Tuyệt đối không thức khuya đêm trước ngày thi.', evidence=f'Sleep quality: {p.sleep_quality}/10 (ngưỡng nguy cấp: {sleep_high})', threshold_used=sleep_high, threshold_method=sleep_m))
        elif p.sleep_quality >= sleep_med:
            report.diagnostics.append(DiagnosticItem(severity='🟡 THEO DÕI', category='Tâm lý', warning='Giấc ngủ chưa ổn định.', suggestion='Cố gắng đi ngủ cùng giờ mỗi ngày. Tránh màn hình 1h trước khi ngủ.', evidence=f'Sleep quality: {p.sleep_quality}/10 (ngưỡng theo dõi: {sleep_med})', threshold_used=sleep_med, threshold_method=sleep_m))
        block_high, _, block_m = self._th('psych_mental_block_frequency')
        if p.mental_block_frequency >= block_high:
            report.diagnostics.append(DiagnosticItem(severity='🟠 CẦN XỬ LÝ', category='Tâm lý', warning="Hay bị 'đứng hình' khi gặp câu khó trong phòng thi.", suggestion="Luyện chiến thuật: đặt dấu '?' và bỏ qua câu khó ngay lập tức, làm hết phần còn lại rồi quay lại. Thực hành điều này trong mọi mock test.", evidence=f'Mental block frequency: {p.mental_block_frequency}/10 (ngưỡng: {block_high})', threshold_used=block_high, threshold_method=block_m))
        time_high, _, time_m = self._th('psych_time_pressure_feeling')
        if p.time_pressure_feeling >= time_high:
            report.diagnostics.append(DiagnosticItem(severity='🟠 CẦN XỬ LÝ', category='Tâm lý', warning='Thường xuyên cảm thấy thiếu thời gian trong phòng thi.', suggestion='Luyện time pacing: SAT Verbal ~1.2 phút/câu, Math ~1.6 phút/câu. Dùng đồng hồ trong mọi buổi luyện đề.', evidence=f'Time pressure: {p.time_pressure_feeling}/10 (ngưỡng: {time_high})', threshold_used=time_high, threshold_method=time_m))
        family_high, _, family_m = self._th('psych_family_pressure')
        motiv_high, _, motiv_m = self._th('psych_motivation_level')
        if p.family_pressure >= family_high and p.motivation_level >= motiv_high:
            report.diagnostics.append(DiagnosticItem(severity='🟠 CẦN XỬ LÝ', category='Tâm lý', warning='Áp lực gia đình lớn nhưng động lực nội tâm thấp — học vì người khác, không vì bản thân.', suggestion='Cần có cuộc trò chuyện thật sự với HS về lý do thi và mục tiêu cá nhân. Động lực ngoại sinh không bền, cần tìm động lực nội sinh.', evidence=f'Family pressure: {p.family_pressure}/10 (ngưỡng {family_high}) | Motivation: {p.motivation_level}/10 (ngưỡng {motiv_high})', threshold_used=family_high, threshold_method=family_m))
        noise_high, noise_med, noise_m = self._th('psych_exam_room_noise')
        self._th('psych_supervisor_pressure')
        env_high_count = sum((1 for v in [p.exam_room_noise, p.uncomfortable_temp, p.supervisor_pressure] if v >= noise_med))
        if env_high_count >= 2:
            report.diagnostics.append(DiagnosticItem(severity='🟡 THEO DÕI', category='Tâm lý', warning=f'Nhạy cảm với {env_high_count}/3 yếu tố môi trường phòng thi.', suggestion='Luyện thi trong nhiều môi trường khác nhau: thư viện, quán cà phê, nhà có tiếng ồn. Mang đồng hồ analog vào phòng thi.', evidence=f'Noise: {p.exam_room_noise} | Temp: {p.uncomfortable_temp} | Supervisor: {p.supervisor_pressure} (ngưỡng theo dõi: {noise_med})', threshold_used=noise_med, threshold_method=noise_m))

    def _rules_learning_style(self, session: StudentSession, report: DiagnosisReport):
        ls = session.learning_style
        rote_high, _, rote_m = self._th('learn_rote_memorization')
        if ls.rote_memorization >= rote_high:
            report.diagnostics.append(DiagnosticItem(severity='🔴 NGUY CẤP', category='Phương pháp', warning='Học vẹt nặng — SAT/IELTS đánh giá tư duy & suy luận, không phải ghi nhớ.', suggestion="Chuyển sang Conceptual Learning: với mỗi bài, hỏi 'Tại sao đáp án này đúng?' Dùng kỹ thuật Feynman: giải thích lại bằng lời mình.", evidence=f'Rote memorization: {ls.rote_memorization}/10 (ngưỡng: {rote_high})', threshold_used=rote_high, threshold_method=rote_m))
        cram_high, _, cram_m = self._th('learn_cramming')
        review_high, _, review_m = self._th('learn_no_review')
        if ls.cramming >= cram_high and ls.no_review >= review_high:
            report.diagnostics.append(DiagnosticItem(severity='🔴 NGUY CẤP', category='Phương pháp', warning='Học dồn + không ôn lại → kiến thức mất 70% sau 24h (Ebbinghaus Forgetting Curve).', suggestion='Bắt buộc áp dụng Spaced Repetition: ôn lại sau 1 ngày → 1 tuần → 2 tuần. Dùng Anki hoặc tạo spreadsheet để track.', evidence=f'Cramming: {ls.cramming}/10 (ngưỡng {cram_high}) | No review: {ls.no_review}/10 (ngưỡng {review_high})', threshold_used=cram_high, threshold_method=cram_m))
        practice_high, practice_med, practice_m = self._th('learn_no_practice_tests')
        if ls.no_practice_tests >= practice_high:
            report.diagnostics.append(DiagnosticItem(severity='🟠 CẦN XỬ LÝ', category='Phương pháp', warning='Thiếu luyện đề nghiêm trọng — không quen format và không biết phân bổ thời gian.', suggestion='Tối thiểu 1 full mock test/tuần trong điều kiện thi thật. Phân tích lỗi sai ngay sau khi làm xong.', evidence=f'No practice tests: {ls.no_practice_tests}/10 (ngưỡng: {practice_high})', threshold_used=practice_high, threshold_method=practice_m))
        elif ls.no_practice_tests >= practice_med:
            report.diagnostics.append(DiagnosticItem(severity='🟡 THEO DÕI', category='Phương pháp', warning='Luyện đề chưa đủ.', suggestion='Tăng tần suất luyện đề lên ít nhất 3 buổi/tuần, mỗi buổi 1 section.', evidence=f'No practice tests: {ls.no_practice_tests}/10 (ngưỡng: {practice_med})', threshold_used=practice_med, threshold_method=practice_m))
        notes_high, _, notes_m = self._th('learn_disorganized_notes')
        if ls.disorganized_notes >= notes_high:
            report.diagnostics.append(DiagnosticItem(severity='🟡 THEO DÕI', category='Phương pháp', warning='Tài liệu học tập thiếu hệ thống — khó ôn tập và dễ bỏ sót kiến thức.', suggestion='Tổ chức lại notes theo dạng bài (1 skill = 1 trang). Dùng Cornell Note format: cột Key Points | Notes | Summary.', evidence=f'Disorganized notes: {ls.disorganized_notes}/10 (ngưỡng: {notes_high})', threshold_used=notes_high, threshold_method=notes_m))
        if ls.study_hours_per_day < 1.5:
            report.diagnostics.append(DiagnosticItem(severity='🟠 CẦN XỬ LÝ', category='Phương pháp', warning=f'Thời gian học quá ít ({ls.study_hours_per_day}h/ngày) — không đủ để build và duy trì kiến thức.', suggestion='Tăng lên tối thiểu 2h/ngày, focus vào chất lượng hơn số lượng. Dùng Pomodoro (25 phút học + 5 phút nghỉ).', evidence=f'Study hours/day: {ls.study_hours_per_day}h', threshold_used=1.5, threshold_method='fixed_hours'))

    def _rules_combos(self, session: StudentSession, report: DiagnosisReport):
        if session.has_learning_data() and session.has_exam_data():
            ls = session.learning_style
            rote_high, _, rote_m = self._th('learn_rote_memorization')
            verbal_weak = [p for p in report.study_priorities if p.accuracy_pct < self.SKILL_WEAK and any((kw in p.skill_name.lower() for kw in ['inference', 'evidence', 'context', 'heading', 'tfng', 'reading', 'synthesis', 'purpose']))]
            if ls.rote_memorization >= rote_high and len(verbal_weak) >= 2:
                report.diagnostics.append(DiagnosticItem(severity='🔴 NGUY CẤP', category='COMBO', warning=f'COMBO: Học vẹt + Yếu {len(verbal_weak)} dạng bài đòi hỏi tư duy — luyện đề thêm sẽ không hiệu quả nếu không thay đổi cách học.', suggestion='Phải giải quyết học vẹt TRƯỚC khi tiếp tục luyện đề. 2 tuần đầu: đọc giải thích từng đáp án, không chỉ đánh dấu đúng/sai.', evidence=f'Rote: {ls.rote_memorization}/10 (ngưỡng {rote_high}) | Weak verbal skills: {[p.skill_name for p in verbal_weak]}', threshold_used=rote_high, threshold_method=rote_m))
        if session.has_exam_data() and session.has_psychology_data():
            er = session.exam_result
            p = session.psychology
            sleep_high, _, sleep_m = self._th('psych_sleep_quality')
            stress_high, _, stress_m = self._th('psych_stress_before_exam')
            score_low = session.target_exam == Exam.SAT and er.mock_score < 1100 or (session.target_exam == Exam.IELTS and er.mock_score < 6.0)
            if score_low and p.sleep_quality >= sleep_high and (p.stress_before_exam >= stress_high):
                report.diagnostics.append(DiagnosticItem(severity='🔴 NGUY CẤP', category='COMBO', warning='COMBO: Điểm mock thấp + Thiếu ngủ + Áp lực cao — ngày thi thực tế có thể ra điểm thấp hơn mock nhiều.', suggestion='Ưu tiên cải thiện giấc ngủ và quản lý stress NGAY BÂY GIỜ, song song với ôn tập. Điểm thi thật phụ thuộc 30-40% vào trạng thái ngày thi.', evidence=f'Mock: {er.mock_score} | Sleep: {p.sleep_quality}/10 (ngưỡng {sleep_high}) | Stress: {p.stress_before_exam}/10 (ngưỡng {stress_high})', threshold_used=sleep_high, threshold_method=sleep_m))
        if session.has_learning_data() and session.has_exam_data():
            ls = session.learning_style
            practice_high, _, practice_m = self._th('learn_no_practice_tests')
            critical_count = len([p for p in report.study_priorities if p.urgency == 'Ưu tiên 1'])
            if ls.no_practice_tests >= practice_high and critical_count >= 3:
                report.diagnostics.append(DiagnosticItem(severity='🟠 CẦN XỬ LÝ', category='COMBO', warning=f'COMBO: Thiếu luyện đề + {critical_count} dạng bài dưới 40% — chưa đủ exposure để nhận dạng dạng bài trong phòng thi.', suggestion='Sau khi ôn từng skill 1-2 tuần, làm ngay đề thật để test. Mỗi tuần phải có ít nhất 1 timed mock test đầy đủ.', evidence=f'No practice: {ls.no_practice_tests}/10 (ngưỡng {practice_high}) | Critical skills: {critical_count}', threshold_used=practice_high, threshold_method=practice_m))

    def _rules_teacher(self, session: StudentSession, report: DiagnosisReport):
        t = session.teacher_obs
        if t.teacher_knowledge_gap_notes.strip():
            report.teacher_flags.append(f'📋 GV ghi nhận: {t.teacher_knowledge_gap_notes}')
        if t.teacher_overall_comment.strip():
            report.teacher_flags.append(f'💬 Nhận xét GV: {t.teacher_overall_comment}')
        if t.class_engagement <= 3.0:
            report.diagnostics.append(DiagnosticItem(severity='🟠 CẦN XỬ LÝ', category='Hành vi học', warning='GV quan sát: học sinh rất thụ động trên lớp.', suggestion='Cần có 1:1 session với GV để tìm nguyên nhân: không hiểu bài, mất động lực, hay vấn đề cá nhân khác?', evidence=f'Class engagement: {t.class_engagement}/10 (điểm GV)'))
        if t.homework_completion <= 3.0:
            report.diagnostics.append(DiagnosticItem(severity='🟠 CẦN XỬ LÝ', category='Hành vi học', warning='GV quan sát: học sinh thường không hoàn thành bài tập về nhà.', suggestion='Kiểm tra lại workload và difficulty của bài tập. Có thể bài quá khó → HS bỏ, hoặc HS thiếu thời gian.', evidence=f'Homework completion: {t.homework_completion}/10 (điểm GV)'))
        if t.teaching_pace_fit <= 4.0:
            report.teacher_flags.append(f'⚠️ Tốc độ học chưa phù hợp với HS (GV đánh giá: {t.teaching_pace_fit}/10). Cân nhắc điều chỉnh pace hoặc tăng thêm giờ 1:1.')

    def _overall_status(self, report: DiagnosisReport) -> str:
        n_critical = sum((1 for d in report.diagnostics if 'NGUY CẤP' in d.severity))
        n_high = sum((1 for d in report.diagnostics if 'CẦN XỬ LÝ' in d.severity))
        n_priority1 = sum((1 for p in report.study_priorities if p.urgency == 'Ưu tiên 1'))
        if n_critical >= 2 or n_priority1 >= 5:
            return '🚨 NGUY CẤP — Cần can thiệp và cơ cấu lại toàn bộ study plan ngay.'
        elif n_critical >= 1 or n_high >= 2 or n_priority1 >= 3:
            return '⚠️ CẦN CẢI THIỆN — Có vấn đề rõ rệt, xử lý các mục đỏ/cam trước.'
        elif n_high >= 1 or n_priority1 >= 1:
            return '📋 CẦN THEO DÕI — Một số điểm yếu cần attention.'
        else:
            return '✅ ỔN ĐỊNH — Không có rủi ro lớn. Tinh chỉnh và duy trì.'
