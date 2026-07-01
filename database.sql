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

-- Example event
INSERT INTO events (title, description, event_date, location, status, created_by) VALUES
('Founders Office Hours', 'Live mentorship and Q&A for startup teams.', '2026-06-15', 'Online', 'published', 1);
