from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class Exam(Enum):
    SAT = 'SAT'
    IELTS = 'IELTS'

@dataclass
class ExamResult:
    exam_type: Exam
    mock_score: Optional[float] = None
    correct_by_skill: dict = field(default_factory=dict)
    wrong_by_skill: dict = field(default_factory=dict)
    total_correct: int = 0
    total_questions: int = 0

    @property
    def accuracy_pct(self) -> Optional[float]:
        if self.total_questions <= 0:
            return None
        return round(self.total_correct / self.total_questions * 100, 1)

    def skill_accuracy(self, skill: str) -> Optional[float]:
        c = self.correct_by_skill.get(skill, 0)
        w = self.wrong_by_skill.get(skill, 0)
        total = c + w
        if total <= 0:
            return None
        return round(c / total * 100, 1)

@dataclass
class ExamPsychology:
    stress_before_exam: float = 0.0
    sleep_quality: float = 0.0
    self_expectation: float = 0.0
    family_pressure: float = 0.0
    motivation_level: float = 0.0
    in_exam_anxiety: float = 0.0
    time_pressure_feeling: float = 0.0
    mental_block_frequency: float = 0.0
    distraction_sensitivity: float = 0.0
    exam_room_noise: float = 0.0
    uncomfortable_temp: float = 0.0
    supervisor_pressure: float = 0.0
    no_clock_available: float = 0.0

@dataclass
class LearningStyle:
    rote_memorization: float = 0.0
    cramming: float = 0.0
    no_practice_tests: float = 0.0
    disorganized_notes: float = 0.0
    no_review: float = 0.0
    poor_comprehension: float = 0.0
    lack_of_preparation: float = 0.0
    exam_skill_weakness: float = 0.0
    study_hours_per_day: float = 0.0
    study_consistency: float = 0.0

@dataclass
class TeacherObservation:
    class_engagement: float = 0.0
    question_asking: float = 0.0
    homework_completion: float = 0.0
    focus_in_class: float = 0.0
    curriculum_exam_alignment: float = 0.0
    teaching_pace_fit: float = 0.0
    teacher_knowledge_gap_notes: str = ''
    teacher_overall_comment: str = ''

@dataclass
class StudentSession:
    student_id: str = ''
    student_name: str = ''
    target_exam: Exam = Exam.SAT
    exam_result: Optional[ExamResult] = None
    psychology: Optional[ExamPsychology] = None
    learning_style: Optional[LearningStyle] = None
    teacher_obs: Optional[TeacherObservation] = None
    actual_score: Optional[float] = None

    def has_exam_data(self) -> bool:
        return self.exam_result is not None and (bool(self.exam_result.correct_by_skill) or bool(self.exam_result.wrong_by_skill))

    def has_psychology_data(self) -> bool:
        return self.psychology is not None

    def has_learning_data(self) -> bool:
        return self.learning_style is not None

    def has_teacher_data(self) -> bool:
        return self.teacher_obs is not None

    def data_completeness(self) -> dict:
        return {'Kết quả bài thi': '✅' if self.has_exam_data() else '❌ thiếu', 'Form tâm lý HS': '✅' if self.has_psychology_data() else '❌ thiếu', 'Form học tập HS': '✅' if self.has_learning_data() else '❌ thiếu', 'Form giáo viên': '✅' if self.has_teacher_data() else '❌ thiếu', 'Điểm thi thật': '✅' if self.actual_score is not None else '— chưa có'}
