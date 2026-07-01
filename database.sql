-- Database schema for Africa Technology Innovation (AIT)

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE courses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  description TEXT,
  price TEXT DEFAULT 'Free',
  status TEXT NOT NULL DEFAULT 'draft',
  created_by INTEGER,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT,
  event_date DATE NOT NULL,
  location TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  created_by INTEGER,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE enrollments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  course_id INTEGER NOT NULL,
  enrolled_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (course_id) REFERENCES courses(id)
);

CREATE TABLE progress (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  course_id INTEGER NOT NULL,
  percentage INTEGER DEFAULT 0,
  UNIQUE(user_id, course_id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (course_id) REFERENCES courses(id)
);

CREATE TABLE lessons (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  course_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  content TEXT,
  order_index INTEGER DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (course_id) REFERENCES courses(id)
);

CREATE TABLE exercises (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lesson_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  starter_code TEXT,
  solution_code TEXT,
  test_cases TEXT,
  difficulty TEXT DEFAULT 'beginner',
  points INTEGER DEFAULT 10,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (lesson_id) REFERENCES lessons(id)
);

CREATE TABLE submissions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  exercise_id INTEGER NOT NULL,
  code TEXT NOT NULL,
  passed INTEGER DEFAULT 0,
  submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (exercise_id) REFERENCES exercises(id)
);

-- Example course
INSERT INTO courses (title, summary, description, price, status, created_by) VALUES
('AI for African Startups', 'Practical AI skills for founders', 'Learn how to apply machine learning to real business problems.', '19/mo', 'published', 1),
('Python Programming Basics', 'Learn Python from scratch', 'Interactive Python course with hands-on exercises and real-world examples.', 'Free', 'published', 1);

-- Python course lessons
INSERT INTO lessons (course_id, title, description, content, order_index) VALUES
(2, 'Introduction to Python', 'Get started with Python basics', 'Python is a powerful, easy-to-learn programming language. In this lesson, you will learn the basics of Python syntax and how to write your first program.', 0),
(2, 'Variables and Data Types', 'Work with strings, numbers, and more', 'Learn about variables, integers, floats, strings, and booleans. These are the building blocks of any Python program.', 1),
(2, 'Control Flow', 'Conditionals and loops', 'Understand how to use if/else statements and loops to control program flow and repeat actions.', 2);

-- Python exercises

-- Python exercises (expanded)
INSERT INTO exercises (lesson_id, title, description, starter_code, solution_code, test_cases, difficulty, points) VALUES
(1, 'Hello, World!', 'Write a program that prints "Hello, World!"', 'print("Hello, World!")', 'print("Hello, World!")', '["Hello, World!"]', 'beginner', 10),
(2, 'Simple Variables', 'Create variables and print them', 'name = ""\nage = 0\nprint(name, age)', 'name = "Alice"\nage = 25\nprint(name, age)', '["Alice 25"]', 'beginner', 10),
(3, 'Even or Odd', 'Check if a number is even or odd', 'number = 0\nif number % 2 == 0:\n    print("even")\nelse:\n    print("odd")', 'number = 4\nif number % 2 == 0:\n    print("even")\nelse:\n    print("odd")', '["even"]', 'beginner', 15),

-- New lessons for Python Programming Basics
(2, 'Functions', 'Define and use functions in Python', 'Functions help you organize code into reusable blocks. In this lesson, you will learn how to define and call functions.', 3),
(2, 'Lists and Loops', 'Work with lists and iterate over them', 'Lists are ordered collections. You can use loops to process each item in a list.', 4),
(2, 'Dictionaries', 'Store key-value pairs with dictionaries', 'Dictionaries map keys to values. They are useful for storing related data.', 5),
(2, 'File I/O', 'Read from and write to files', 'Python can read and write files using the open() function.', 6),
(2, 'Object-Oriented Programming', 'Classes and objects in Python', 'OOP lets you model real-world things as code. Learn about classes and objects.', 7);

-- New exercises for new lessons
INSERT INTO exercises (lesson_id, title, description, starter_code, solution_code, test_cases, difficulty, points) VALUES
(4, 'Define a Function', 'Write a function called greet that prints "Hello!"', 'def greet():\n    pass', 'def greet():\n    print("Hello!")\ngreet()', '["Hello!"]', 'beginner', 10),
(5, 'Sum a List', 'Write code to sum all numbers in a list and print the result.', 'numbers = [1, 2, 3, 4]\n# Your code here', 'numbers = [1, 2, 3, 4]\nprint(sum(numbers))', '["10"]', 'beginner', 10),
(6, 'Dictionary Lookup', 'Print the value for key "age" in the dictionary.', 'person = {"name": "Bob", "age": 30}\n# Your code here', 'person = {"name": "Bob", "age": 30}\nprint(person["age"] )', '["30"]', 'beginner', 10),
(7, 'Write to File', 'Write "AIT" to a file named output.txt', '# Your code here', 'with open("output.txt", "w") as f:\n    f.write("AIT")\nprint("AIT")', '["AIT"]', 'intermediate', 15),
(8, 'Create a Class', 'Create a class Dog with a method bark() that prints "Woof!"', 'class Dog:\n    pass', 'class Dog:\n    def bark(self):\n        print("Woof!")\nd = Dog()\nd.bark()', '["Woof!"]', 'intermediate', 15);

-- Seed 10 Python courses organized by level (beginner -> advanced)
INSERT INTO courses (title, summary, description, price, status, created_by) VALUES
('Python: Foundations (Beginner)', 'Start programming with Python', 'Basics of Python syntax, REPL, and writing your first programs.', 'Free', 'published', 1),
('Python: Data Types & Operations (Beginner)', 'Work confidently with Python types', 'Numbers, strings, lists, tuples, and basic operations.', 'Free', 'published', 1),
('Python: Control Flow (Beginner)', 'Conditionals and loops', 'if/else, for/while loops, and basic iteration patterns.', 'Free', 'published', 1),
('Python: Functions & Modules (Beginner)', 'Reusable code with functions', 'Defining functions, parameters, return values, and modules.', 'Free', 'published', 1),
('Python: Data Structures (Intermediate)', 'Collections and data handling', 'Lists, dicts, sets, comprehensions and common operations.', 'Free', 'published', 1),
('Python: File I/O & Error Handling (Intermediate)', 'Files and exceptions', 'Reading/writing files, context managers, and catching errors.', 'Free', 'published', 1),
('Python: Object-Oriented Programming (Intermediate)', 'Classes and objects', 'Create classes, methods, and basic OOP patterns.', 'Free', 'published', 1),
('Python: Web & APIs (Advanced)', 'Interacting with web services', 'Requests, parsing JSON, and simple API clients.', 'Free', 'published', 1),
('Python: Testing & Debugging (Advanced)', 'Write tests and debug code', 'unittest/pytest basics and debugging strategies.', 'Free', 'published', 1),
('Python: Projects & Deployment (Advanced)', 'Build and deploy Python apps', 'Packaging, virtualenv, and simple deployment workflows.', 'Free', 'published', 1);

-- Lessons for the new Python courses (use subqueries to resolve course IDs)
INSERT INTO lessons (course_id, title, description, content, order_index) VALUES
((SELECT id FROM courses WHERE title = 'Python: Foundations (Beginner)'), 'Introduction & Setup', 'Install Python, use the REPL, and write your first script.', 'Intro content and setup instructions.', 0),
((SELECT id FROM courses WHERE title = 'Python: Foundations (Beginner)'), 'Hello World and Print', 'Your first Python program and printing.', 'Examples and exercises on print()', 1),

((SELECT id FROM courses WHERE title = 'Python: Data Types & Operations (Beginner)'), 'Numbers and Math', 'Integers, floats, basic arithmetic and built-in functions.', 'Content on numeric types.', 0),
((SELECT id FROM courses WHERE title = 'Python: Data Types & Operations (Beginner)'), 'Strings and Formatting', 'String operations, f-strings, and formatting.', 'String methods and exercises.', 1),

((SELECT id FROM courses WHERE title = 'Python: Control Flow (Beginner)'), 'Conditionals', 'if, elif, else and boolean logic.', 'Practical examples and quizzes.', 0),
((SELECT id FROM courses WHERE title = 'Python: Control Flow (Beginner)'), 'Loops', 'for and while loops, break/continue.', 'Loop patterns and exercises.', 1),

((SELECT id FROM courses WHERE title = 'Python: Functions & Modules (Beginner)'), 'Defining Functions', 'Parameters, return values, and scope.', 'Function examples and best practices.', 0),
((SELECT id FROM courses WHERE title = 'Python: Functions & Modules (Beginner)'), 'Modules and Imports', 'Organizing code with modules and packages.', 'Create and import modules.', 1),

((SELECT id FROM courses WHERE title = 'Python: Data Structures (Intermediate)'), 'Lists & Tuples Deep Dive', 'Advanced list operations and tuple usage.', 'Comprehensions and slicing.', 0),
((SELECT id FROM courses WHERE title = 'Python: Data Structures (Intermediate)'), 'Dictionaries & Sets', 'Mapping and unique collections.', 'Common patterns with dicts and sets.', 1),

((SELECT id FROM courses WHERE title = 'Python: File I/O & Error Handling (Intermediate)'), 'File Reading/Writing', 'Open/read/write files and context managers.', 'Practical file handling tasks.', 0),
((SELECT id FROM courses WHERE title = 'Python: File I/O & Error Handling (Intermediate)'), 'Exceptions & Logging', 'Try/except and logging basics.', 'Error handling exercises.', 1),

((SELECT id FROM courses WHERE title = 'Python: Object-Oriented Programming (Intermediate)'), 'Classes and Instances', 'Define classes, init, and instance methods.', 'OOP basics and examples.', 0),
((SELECT id FROM courses WHERE title = 'Python: Object-Oriented Programming (Intermediate)'), 'Inheritance & Polymorphism', 'Extend classes and override methods.', 'OOP patterns and exercises.', 1),

((SELECT id FROM courses WHERE title = 'Python: Web & APIs (Advanced)'), 'HTTP & Requests', 'Using requests to fetch data from APIs.', 'Call public APIs and parse JSON.', 0),
((SELECT id FROM courses WHERE title = 'Python: Web & APIs (Advanced)'), 'Building a Simple Client', 'Combine requests and data processing.', 'Hands-on API client exercise.', 1),

((SELECT id FROM courses WHERE title = 'Python: Testing & Debugging (Advanced)'), 'Unit Testing Basics', 'Write unit tests using unittest or pytest.', 'Assertions and test structure.', 0),
((SELECT id FROM courses WHERE title = 'Python: Testing & Debugging (Advanced)'), 'Debugging Techniques', 'Use pdb and logging to debug programs.', 'Debugging walkthroughs.', 1),

((SELECT id FROM courses WHERE title = 'Python: Projects & Deployment (Advanced)'), 'Packaging & Virtualenv', 'Create virtual environments and package apps.', 'Deployment prep and packaging.', 0),
((SELECT id FROM courses WHERE title = 'Python: Projects & Deployment (Advanced)'), 'Deploy a Simple App', 'Deploy a tiny Flask app locally or to a platform.', 'Deployment demo and exercises.', 1);

-- Exercises that link into the interactive IDE (lab) for each first lesson
INSERT INTO exercises (lesson_id, title, description, starter_code, solution_code, test_cases, difficulty, points) VALUES
((SELECT id FROM lessons WHERE course_id = (SELECT id FROM courses WHERE title = 'Python: Foundations (Beginner)') AND order_index = 0), 'First Script', 'Write a script that prints "Hello AIT".', 'print("")', 'print("Hello AIT")', '["Hello AIT"]', 'beginner', 10),
((SELECT id FROM lessons WHERE course_id = (SELECT id FROM courses WHERE title = 'Python: Data Types & Operations (Beginner)') AND order_index = 0), 'Sum Numbers', 'Read a list and print the sum.', 'numbers = [1,2,3]\n# your code', 'numbers = [1,2,3]\nprint(sum(numbers))', '["6"]', 'beginner', 10),
((SELECT id FROM lessons WHERE course_id = (SELECT id FROM courses WHERE title = 'Python: Control Flow (Beginner)') AND order_index = 0), 'Even Check', 'Print "even" or "odd" for a number.', 'n = 2\n# your code', 'n = 3\nif n%2==0:\n    print("even")\nelse:\n    print("odd")', '["odd"]', 'beginner', 10),
((SELECT id FROM lessons WHERE course_id = (SELECT id FROM courses WHERE title = 'Python: Functions & Modules (Beginner)') AND order_index = 0), 'Make a Function', 'Create greet() that returns "hi".', 'def greet():\n    pass', 'def greet():\n    return "hi"\nprint(greet())', '["hi"]', 'beginner', 10),
((SELECT id FROM lessons WHERE course_id = (SELECT id FROM courses WHERE title = 'Python: Data Structures (Intermediate)') AND order_index = 0), 'List Comprehension', 'Use a comprehension to square numbers.', 'nums = [1,2,3]\n# your code', 'nums = [1,2,3]\nprint([n*n for n in nums])', '["[1, 4, 9]"]', 'intermediate', 15),
((SELECT id FROM lessons WHERE course_id = (SELECT id FROM courses WHERE title = 'Python: File I/O & Error Handling (Intermediate)') AND order_index = 0), 'Read File', 'Read contents of a file and print them.', '# assume file exists', 'with open("input.txt") as f:\n    print(f.read())', '["<file-contents>"]', 'intermediate', 15),
((SELECT id FROM lessons WHERE course_id = (SELECT id FROM courses WHERE title = 'Python: Object-Oriented Programming (Intermediate)') AND order_index = 0), 'Create a Class', 'Define class Person with name attribute.', 'class Person:\n    pass', 'class Person:\n    def __init__(self, name):\n        self.name = name\nprint(Person("Alex").name)', '["Alex"]', 'intermediate', 15),
((SELECT id FROM lessons WHERE course_id = (SELECT id FROM courses WHERE title = 'Python: Web & APIs (Advanced)') AND order_index = 0), 'Fetch JSON', 'Call a public API and print a field.', 'import requests\n# your code', 'import requests\nprint(requests.__name__)', '[]', 'advanced', 20),
((SELECT id FROM lessons WHERE course_id = (SELECT id FROM courses WHERE title = 'Python: Testing & Debugging (Advanced)') AND order_index = 0), 'Write a Test', 'Write a simple unit test for add(a,b).', 'def add(a,b):\n    return a+b\n# add tests', 'def add(a,b):\n    return a+b\nprint(add(1,2))', '[]', 'advanced', 20),
((SELECT id FROM lessons WHERE course_id = (SELECT id FROM courses WHERE title = 'Python: Projects & Deployment (Advanced)') AND order_index = 0), 'Hello App', 'Create a tiny Flask app that returns Hello.', 'from flask import Flask\napp = Flask(__name__)\n# your code', 'from flask import Flask\napp = Flask(__name__)\n@app.route("/")\ndef home():\n    return "Hello"\nprint("app ready")', '[]', 'advanced', 20);

-- Example event
INSERT INTO events (title, description, event_date, location, status, created_by) VALUES
('Founders Office Hours', 'Live mentorship and Q&A for startup teams.', '2026-06-15', 'Online', 'published', 1);

-- Example event
INSERT INTO events (title, description, event_date, location, status, created_by) VALUES
('Founders Office Hours', 'Live mentorship and Q&A for startup teams.', '2026-06-15', 'Online', 'published', 1);
