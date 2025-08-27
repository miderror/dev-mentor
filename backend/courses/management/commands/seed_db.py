from textwrap import dedent

from django.core.management.base import BaseCommand
from django.db import transaction

from backend.courses.models import Course, DifficultyLevel, Module, Task

COURSES_DATA = [
    {
        "course_title": "Python для начинающих",
        "modules": [
            {
                "module_title": "Модуль 1: Основы синтаксиса",
                "levels": [
                    {
                        "level_title": "Easy",
                        "tasks": [
                            {
                                "number": 1,
                                "title": "Привет, мир!",
                                "description": dedent("""
                                    Напишите программу, которая выводит строку `Hello, World!`.

                                    *Дано:*
                                    Никаких входных данных не требуется.

                                    *Результат:*
                                    Программа должна напечатать в консоль:
                                    ```
                                    Hello, World!
                                    ```
                                """),
                                "tests": {
                                    "tests": [
                                        {"input": [], "expected": "Hello, World!"}
                                    ]
                                },
                            },
                            {
                                "number": 2,
                                "title": "Сумма двух чисел",
                                "description": dedent("""
                                    Напишите программу, которая принимает на вход два целых числа, разделенных пробелом, и выводит их сумму.

                                    *Дано:*
                                    Одна строка, содержащая два целых числа `a` и `b` (`-1000 <= a, b <= 1000`).

                                    *Результат:*
                                    Одно целое число — сумма `a + b`.

                                    _Пример:_
                                    Вход: `5 10`
                                    Выход: `15`
                                """),
                                "tests": {
                                    "tests": [
                                        {"input": ["5 10"], "expected": "15"},
                                        {"input": ["-1 -2"], "expected": "-3"},
                                        {"input": ["0 0"], "expected": "0"},
                                    ]
                                },
                            },
                        ],
                    },
                    {
                        "level_title": "Medium",
                        "tasks": [
                            {
                                "number": 1,
                                "title": "Переворот строки",
                                "description": dedent("""
                                    Напишите программу, которая принимает на вход строку и выводит её в обратном порядке.

                                    *Дано:*
                                    Одна строка `s`.

                                    *Результат:*
                                    Строка `s`, записанная наоборот.

                                    _Пример:_
                                    Вход: `python`
                                    Выход: `nohtyp`
                                """),
                                "tests": {
                                    "tests": [
                                        {"input": ["python"], "expected": "nohtyp"},
                                        {"input": ["racecar"], "expected": "racecar"},
                                        {"input": ["12345"], "expected": "54321"},
                                    ]
                                },
                            }
                        ],
                    },
                    {
                        "level_title": "Hard",
                        "tasks": [
                            {
                                "number": 1,
                                "title": "Проверка на простое число",
                                "description": dedent("""
                                    Напишите программу, которая проверяет, является ли введенное число простым.

                                    *Дано:*
                                    Одно целое положительное число `n` (1 <= n <= 1000).

                                    *Результат:*
                                    Выведите `True`, если число простое, и `False` в противном случае.

                                    _Пример 1:_
                                    Вход: `7`
                                    Выход: `True`

                                    _Пример 2:_
                                    Вход: `10`
                                    Выход: `False`
                                """),
                                "tests": {
                                    "tests": [
                                        {"input": ["2"], "expected": True},
                                        {"input": ["7"], "expected": True},
                                        {"input": ["10"], "expected": False},
                                        {"input": ["1"], "expected": False},
                                        {"input": ["97"], "expected": True},
                                    ]
                                },
                            }
                        ],
                    },
                ],
            },
            {
                "module_title": "Модуль 2: Условные операторы и циклы",
                "levels": [
                    {
                        "level_title": "Easy",
                        "tasks": [
                            {
                                "number": 1,
                                "title": "Чётное или нечётное",
                                "description": dedent("""
                                    Напишите программу, которая определяет, является ли число чётным или нечётным.

                                    *Дано:*
                                    Одно целое число `n`.

                                    *Результат:*
                                    Слово `Четное` или `Нечетное`.

                                    _Пример:_
                                    Вход: `10`
                                    Выход: `Четное`
                                """),
                                "tests": {
                                    "tests": [
                                        {"input": ["10"], "expected": "Четное"},
                                        {"input": ["7"], "expected": "Нечетное"},
                                        {"input": ["0"], "expected": "Четное"},
                                        {"input": ["-1"], "expected": "Нечетное"},
                                    ]
                                },
                            }
                        ],
                    },
                    {
                        "level_title": "Medium",
                        "tasks": [
                            {
                                "number": 1,
                                "title": "Факториал числа",
                                "description": dedent("""
                                    Напишите программу для вычисления факториала числа.

                                    *Дано:*
                                    Одно неотрицательное целое число `n` (0 <= n <= 15).

                                    *Результат:*
                                    Факториал числа `n`.

                                    _Пример:_
                                    Вход: `5`
                                    Выход: `120`
                                """),
                                "tests": {
                                    "tests": [
                                        {"input": ["5"], "expected": "120"},
                                        {"input": ["0"], "expected": "1"},
                                        {"input": ["1"], "expected": "1"},
                                        {"input": ["10"], "expected": "3628800"},
                                    ]
                                },
                            }
                        ],
                    },
                ],
            },
            {
                "module_title": "Модуль 3: Структуры данных",
                "levels": [
                    {
                        "level_title": "Easy",
                        "tasks": [
                            {
                                "number": 1,
                                "title": "Найти максимальный элемент",
                                "description": dedent("""
                                    Напишите программу, которая находит максимальное число в списке целых чисел.

                                    *Дано:*
                                    Строка чисел, разделенных пробелом.

                                    *Результат:*
                                    Максимальное число из списка.

                                    _Пример:_
                                    Вход: `1 9 3 4 5`
                                    Выход: `9`
                                """),
                                "tests": {
                                    "tests": [
                                        {"input": ["1 9 3 4 5"], "expected": "9"},
                                        {"input": ["-1 -5 -2"], "expected": "-1"},
                                        {"input": ["10"], "expected": "10"},
                                    ]
                                },
                            }
                        ],
                    },
                    {
                        "level_title": "Medium",
                        "tasks": [
                            {
                                "number": 1,
                                "title": "Подсчет гласных",
                                "description": dedent("""
                                    Напишите программу, которая подсчитывает количество гласных букв (a, e, i, o, u) в строке. Регистр не учитывается.

                                    *Дано:*
                                    Одна строка текста.

                                    *Результат:*
                                    Количество гласных.

                                    _Пример:_
                                    Вход: `Hello World`
                                    Выход: `3`
                                """),
                                "tests": {
                                    "tests": [
                                        {"input": ["Hello World"], "expected": "3"},
                                        {"input": ["PYTHON"], "expected": "1"},
                                        {"input": ["AEIOUaeiou"], "expected": "10"},
                                        {"input": ["xyz"], "expected": "0"},
                                    ]
                                },
                            }
                        ],
                    },
                ],
            },
        ],
    },
    {
        "course_title": "Продвинутый Python",
        "modules": [
            {
                "module_title": "Модуль 1: Функции и алгоритмы",
                "levels": [
                    {
                        "level_title": "Medium",
                        "tasks": [
                            {
                                "number": 1,
                                "title": "Проверка на палиндром",
                                "description": dedent("""
                                    Напишите программу, которая проверяет, является ли строка палиндромом.
                                    Палиндром — это строка, которая читается одинаково слева направо и справа налево, без учета регистра и небуквенных символов.

                                    *Дано:*
                                    Одна строка для проверки.

                                    *Результат:*
                                    `True`, если строка — палиндром, иначе `False`.

                                    _Пример:_
                                    Вход: `А роза упала на лапу Азора`
                                    Выход: `True`
                                """),
                                "tests": {
                                    "tests": [
                                        {
                                            "input": ["А роза упала на лапу Азора"],
                                            "expected": True,
                                        },
                                        {"input": ["racecar"], "expected": True},
                                        {"input": ["hello"], "expected": False},
                                    ]
                                },
                            }
                        ],
                    },
                    {
                        "level_title": "Hard",
                        "tasks": [
                            {
                                "number": 1,
                                "title": "Сумма двух",
                                "description": dedent("""
                                    Напишите программу, которая определяет, есть ли в данном списке чисел пара, сумма которой равна заданному числу K.

                                    *Дано:*
                                    Первая строка: числа, разделенные пробелом.
                                    Вторая строка: целевое число K.

                                    *Результат:*
                                    `True`, если такая пара существует, иначе `False`.

                                    _Пример:_
                                    Вход:
                                    `2 7 11 15`
                                    `9`
                                    Выход: `True` (потому что 2 + 7 = 9)
                                """),
                                "tests": {
                                    "tests": [
                                        {"input": ["2 7 11 15", "9"], "expected": True},
                                        {"input": ["3 2 4", "6"], "expected": True},
                                        {"input": ["3 3", "6"], "expected": True},
                                        {"input": ["10 20 30", "7"], "expected": False},
                                    ]
                                },
                            }
                        ],
                    },
                ],
            },
            {
                "module_title": "Модуль 2: Работа с коллекциями",
                "levels": [
                    {
                        "level_title": "Medium",
                        "tasks": [
                            {
                                "number": 1,
                                "title": "Удаление дубликатов",
                                "description": dedent("""
                                    Напишите программу, которая принимает строку чисел, разделенных пробелами, и выводит их в том же порядке, но без дубликатов.

                                    *Дано:*
                                    Строка чисел, разделенных пробелом.

                                    *Результат:*
                                    Строка уникальных чисел, разделенных пробелом.

                                    _Пример:_
                                    Вход: `1 2 3 2 4 1 5`
                                    Выход: `1 2 3 4 5`
                                """),
                                "tests": {
                                    "tests": [
                                        {
                                            "input": ["1 2 3 2 4 1 5"],
                                            "expected": "1 2 3 4 5",
                                        },
                                        {"input": ["5 5 5 5 5"], "expected": "5"},
                                        {"input": ["10 20 30"], "expected": "10 20 30"},
                                    ]
                                },
                            }
                        ],
                    },
                    {
                        "level_title": "Hard",
                        "tasks": [
                            {
                                "number": 1,
                                "title": "Самый частый элемент",
                                "description": dedent("""
                                    Напишите программу, которая находит самый часто встречающийся элемент в списке. Если таких элементов несколько, выведите любой из них.

                                    *Дано:*
                                    Строка элементов, разделенных пробелом.

                                    *Результат:*
                                    Самый часто встречающийся элемент.

                                    _Пример:_
                                    Вход: `apple banana apple orange banana apple`
                                    Выход: `apple`
                                """),
                                "tests": {
                                    "tests": [
                                        {
                                            "input": [
                                                "apple banana apple orange banana apple"
                                            ],
                                            "expected": "apple",
                                        },
                                        {
                                            "input": ["1 2 2 3 3 3 4 4 4 4"],
                                            "expected": "4",
                                        },
                                        {"input": ["a b c"], "expected": "a"},
                                    ]
                                },
                            }
                        ],
                    },
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Fills the database with initial courses, modules, levels, and tasks."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("Starting database seeding...")

        Task.objects.all().delete()
        DifficultyLevel.objects.all().delete()
        Module.objects.all().delete()
        Course.objects.all().delete()
        self.stdout.write(self.style.WARNING("Cleared existing course data."))

        for course_data in COURSES_DATA:
            course, created = Course.objects.get_or_create(
                title=course_data["course_title"]
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Course: {course.title}"))

            for module_order, module_data in enumerate(course_data["modules"]):
                module, created = Module.objects.get_or_create(
                    course=course,
                    title=module_data["module_title"],
                    defaults={"order": module_order},
                )
                if created:
                    self.stdout.write(f"  - Created Module: {module.title}")

                for level_order, level_data in enumerate(module_data["levels"]):
                    level, created = DifficultyLevel.objects.get_or_create(
                        module=module,
                        title=level_data["level_title"],
                        defaults={"order": level_order},
                    )
                    if created:
                        self.stdout.write(f"    - Created Level: {level.title}")

                    for task_data in level_data["tasks"]:
                        task, created = Task.objects.get_or_create(
                            level=level,
                            number=task_data["number"],
                            defaults={
                                "title": task_data["title"],
                                "description": task_data["description"],
                                "tests": task_data["tests"],
                            },
                        )
                        if created:
                            self.stdout.write(
                                f"      - Created Task: #{task.number} {task.title}"
                            )

        self.stdout.write(
            self.style.SUCCESS("Database seeding completed successfully!")
        )
