import random
import names

from model_mommy import mommy

from django.core.management.base import BaseCommand
from core.models import University, Course, Student


class Command(BaseCommand):
    help = "My shiny new management command."

    def add_arguments(self, parser):
        parser.add_argument('count', nargs=1, type=int)

    def handle(self, *args, **options):
        print 'lala'
        self.clear()
        self.make_universities()
        self.make_courses()
        self.make_students(options)
        self.connect_courses()

    def clear(self):
        Student.objects.all().delete()
        University.objects.all().delete()
        Course.objects.all().delete()

    def make_universities(self):
        university_names = (
            'MIT', 'MGU', 'CalTech', 'KPI', 'DPI', 'PSTU'
        )
        self.universities = []
        for name in university_names:
            uni = mommy.make(University, name=name)
            self.universities.append(uni)

    def make_courses(self):
        template_options = ['CS%s0%s', 'MATH%s0%s', 'CHEM%s0%s', 'PHYS%s0%s']
        self.courses = []
        for num in range(1, 4):
            for course_num in range(1, 4):
                for template in template_options:
                    name = template % (course_num, num)
                    course = mommy.make(Course, name=name)
                    self.courses.append(course)

    def make_students(self, options):
        self.students = []
        for _ in xrange(options.get('count')[0]):
            stud = mommy.prepare(
                Student,
                university=random.choice(self.universities),
                first_name=names.get_first_name(),
                last_name=names.get_last_name(),
                age=random.randint(17, 25)
            )
            self.students.append(stud)
        Student.objects.bulk_create(self.students)

    def connect_courses(self):
        ThroughModel = Student.courses.through
        stud_courses = []
        for student_id in Student.objects.values_list('pk', flat=True):
            courses_already_linked = []
            for _ in range(random.randint(1, 10)):
                index = random.randint(0, len(self.courses) - 1)
                if index not in courses_already_linked:
                    courses_already_linked.append(index)
                else:
                    continue
                stud_courses.append(
                    ThroughModel(
                        student_id=student_id,
                        course_id=self.courses[index].pk
                    )
                )
        ThroughModel.objects.bulk_create(stud_courses)



