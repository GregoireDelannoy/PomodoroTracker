import bottle
import sqlite3
from jinja2 import Template
from enum import Enum
from time import time
from datetime import datetime

app = bottle.Bottle()
ROOT_PATH = '/pomodoro/'

def seconds_to_hms(seconds):
    h = str(int(seconds / 3600))
    m = str(int(seconds % 3600 / 60))
    s = str(int(seconds % 3600 % 60))
    return h + ':' + m + ':' + s

class TaskStates(Enum):
    CREATED = 1
    ONGOING = 2
    FAILED = 3
    DONE = 4

class Task():
    def __init__(self):
        self.id = None
        self.description = ''
        self.state = TaskStates.CREATED
        self.created_at = time()
        self.started_at = 0
        self.finished_at = 0
        self.total_children_time = 0

    def from_storage(self, res):
        self.id = res[0]
        self.description = res[1]
        self.state = TaskStates(res[2])
        self.created_at = res[3]
        self.started_at = res[4]
        self.finished_at = res[5]

    def __str__(self):
        return 'Task: ' + str(self.id) + str(self.description) + ' with state ' + str(self.state) + ' created at ' + str(self.created_at)

    def total_time(self):
        time = self.total_children_time
        if self.state in (TaskStates.DONE, TaskStates.FAILED):
            time += self.finished_at - self.started_at
        return seconds_to_hms(time)

    def finished_at_human(self):
        local_time = datetime.fromtimestamp(self.finished_at)
        return local_time.strftime("%Y-%m-%d %H:%M")

    def start(self):
        if self.state == TaskStates.CREATED:
            self.state = TaskStates.ONGOING
            self.started_at = time()
        else:
            raise Exception('Cannot start task: ' + str(self))

    def failed(self):
        if self.state == TaskStates.ONGOING:
            self.state = TaskStates.FAILED
            self.finished_at = time()
        else:
            raise Exception('Cannot fail task: ' + str(self))

    def done(self):
        if self.state == TaskStates.ONGOING:
            self.state = TaskStates.DONE
            self.finished_at = time()
        else:
            raise Exception('Cannot terminate task: ' + str(self))

class Storage():
    def __init__(self):
        self.DB_NAME = ':memory:'
        self.conn = sqlite3.connect(self.DB_NAME)
        cursor = self.conn.cursor()
        cursor.execute('''
CREATE TABLE tasks (
task_id INTEGER PRIMARY KEY,
description TEXT NOT NULL,
state INTEGER NOT NULL,
created_at INTEGER NOT NULL,
started_at INTEGER,
finished_at INTEGER,
parent_task_id INTEGER);''')
        self.conn.commit()

    def __fetch_all(self, statement, data):
        cursor = self.conn.cursor()
        cursor.execute(statement, data)
        result = cursor.fetchall()
        cursor.close()
        return result

    def __execute(self, statement, data):
        cursor = self.conn.cursor()
        cursor.execute(statement, data)
        cursor.close()
        self.conn.commit()

    def get_task(self, id):
        return self.__fetch_all("SELECT task_id, description, state, created_at, started_at, finished_at, parent_task_id FROM tasks WHERE task_id = ?", (id,))[0]
        # comma after id, see https://stackoverflow.com/a/7305758

    def get_tasks(self):
        return self.__fetch_all("SELECT task_id, description, state, created_at, started_at, finished_at, parent_task_id FROM tasks", ())

    def new_task(self, task, parent_id):
        if parent_id == None:
            self.__execute("INSERT INTO tasks(description, state, created_at) VALUES (?, ?, ?);", (task.description, task.state.value, task.created_at))
        else:
            self.__execute("INSERT INTO tasks(description, state, created_at, parent_task_id) VALUES (?, ?, ?, ?);", (task.description, task.state.value, task.created_at, parent_id))

    def update_task(self, task):
        self.__execute("UPDATE tasks SET description = ?, state = ?, started_at = ?, finished_at = ? WHERE task_id = ?", (task.description, task.state.value, task.started_at, task.finished_at, task.id))

class Node():
    def __init__(self, id, data):
        self.id = id
        self.data = data
        self.children = []
        self.parent_node = None

    def __str__(self):
        return str(self.data)

    def __iter__(self):
        return iter(self.children)

    def add_child(self, child):
        self.children.append(child)

class Tree():
    def __add_to_ancestors(self, node, seconds):
        if node.data != None:
            node.data.total_children_time += seconds
            self.__add_to_ancestors(node.parent_node, seconds)

    def __fill_elapsed_time(self, node):
        if node.data.state in (TaskStates.DONE, TaskStates.FAILED):
            elapsed_time = node.data.finished_at - node.data.started_at
            self.__add_to_ancestors(node.parent_node, elapsed_time)

    def __append(self, current_node, node, parent_id):
        if parent_id == None or current_node.id == parent_id:
            current_node.add_child(node)
            node.parent_node = current_node
            self.__fill_elapsed_time(node)
        else:
            for child in current_node.children:
                self.__append(child, node, parent_id)

    def __init__(self, storage):
        self.root = Node(-1, None)
        raw_tasks = storage.get_tasks()
        self.current_task = None
        for raw_task in raw_tasks:
            id = raw_task[0]
            parent_id = raw_task[6]

            task = Task()
            task.from_storage(raw_task)

            if task.state == TaskStates.ONGOING:
                self.current_task = task

            self.__append(self.root, Node(id, task), parent_id)

storage = Storage()
index_template = Template(open('index.html.j2').read())

# ROUTES
@app.get('/')
def home():
    tree = Tree(storage)
    return index_template.render(tree = tree.root, current_task = tree.current_task)

@app.post('/new')
def new():
    task = Task()
    task.description = bottle.request.POST.description
    storage.new_task(task, bottle.request.POST.get('parent_task_id'))
    bottle.redirect(ROOT_PATH)

@app.post('/start/<task_id>')
def start(task_id):
    task = Task()
    task.from_storage(storage.get_task(task_id))
    task.start()
    storage.update_task(task)
    bottle.redirect(ROOT_PATH)

@app.post('/done/<task_id>')
def done(task_id):
    task = Task()
    task.from_storage(storage.get_task(task_id))
    task.done()
    storage.update_task(task)
    bottle.redirect(ROOT_PATH)

@app.post('/failed/<task_id>')
def failed(task_id):
    task = Task()
    task.from_storage(storage.get_task(task_id))
    task.failed()
    storage.update_task(task)
    bottle.redirect(ROOT_PATH)

app.run(host='0.0.0.0', port=8002)