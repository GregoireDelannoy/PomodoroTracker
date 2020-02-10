import bottle
import sqlite3
import os.path
from jinja2 import Template
from enum import Enum
from time import time
from functools import reduce

app = bottle.Bottle()

DB_NAME = 'db.sqlite3'

class TaskStates(Enum):
    CREATED = 1
    ONGOING = 2
    FAILED = 3
    DONE = 4

class Task():
    def __init__(self, description):
        self.description = description
        self.state = TaskStates.CREATED
        self.created_at = time()
        self.started_at = None
        self.finished_at = None

    def __str__(self):
        return 'Task %s with state %d created at %d, started at %d, finished at %d' (self.description, self.state, self.created_at, self.started_at, self.finished_at)

    def start(self):
        if self.state == TaskStates.CREATED:
            self.state = TaskStates.ONGOING
            self.started_at = time()
        else:
            raise Exception('Cannot start task: ' + str(self))

    def fail(self):
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




index_template = Template('''
<!doctype html>
<html lang="en">
<body>
<h1>Tasks</h1>
<h2>New task</h2>
<form action="/new" method="POST">
  <input type="text" size="100" maxlength="1000" name="description">
  <input type="submit" name="save" value="save">
</form>
<h2>Current todo</h2>
<ul>
{% for item in tasks %}
  <li>
  {{item.description}} :
  {% if item.ongoing %}
  <form action="/done/{{item.task_id}}" method="POST"><input type="submit" name="save" value="done"></form>
  <form action="/failed/{{item.task_id}}" method="POST"><input type="submit" name="save" value="failed"></form>
  {% else %}
  <form action="/start/{{item.task_id}}" method="POST"><input type="submit" name="save" value="start"></form>
  {% endif %}
  :
  <form action="/delete/{{item.task_id}}" method="POST"><input type="submit" name="submit" value="delete"></form> </li>
{% endfor %}
</ul>
</body>
</html>
''')

def fetch_all(statement):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(statement)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def insert(statement, data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    print(statement)
    cursor.execute(statement, data)
    print(cursor.lastrowid)
    cursor.close()
    conn.commit()
    conn.close()

def ongoing_tasks(user_id):
    res = fetch_all("SELECT events.type, tasks.task_id FROM events JOIN tasks WHERE events.task_id=tasks.task_id AND tasks.owner_user_id = %d ORDER BY events.timestamp" % (user_id))
    ongoing = []
    for item in res:
        type = item[0]
        id = item[1]
        if type in ("STARTED"):
            ongoing.append(id)
            print('appending task id %d, because type: %s' % (id, type))
        elif type in ("DONE", "FAILED"):
            ongoing.remove(id)
    print(ongoing)
    return ongoing



# ROUTES
@app.get('/')
def home():
    # TODO: user mgmt
    user_id = 0

    res = fetch_all("SELECT tasks.task_id, tasks.description, users.email FROM tasks JOIN users;")
    ongoing = ongoing_tasks(user_id)
    tasks = list(map(lambda i: {'task_id': i[0], 'description': i[1], 'ongoing': i[0] in ongoing}, res))
    print(tasks)
    return index_template.render(tasks=tasks)

@app.post('/new')
def new():
    user_id = 0
    description = bottle.request.POST.description
    statement = "INSERT INTO tasks(description, owner_user_id) VALUES (?, ?);"
    insert(statement, (description, user_id))
    bottle.redirect('/')

@app.post('/start/<task_id>')
def start(task_id):
    statement = "INSERT INTO events(type, task_id) VALUES ('STARTED', ?);"
    insert(statement, (task_id))
    bottle.redirect('/')

@app.post('/done/<task_id>')
def done(task_id):
    statement = "INSERT INTO events(type, task_id) VALUES ('DONE', ?);"
    insert(statement, (task_id))
    bottle.redirect('/')

@app.post('/failed/<task_id>')
def failed(task_id):
    statement = "INSERT INTO events(type, task_id) VALUES ('FAILED', ?);"
    insert(statement, (task_id))
    bottle.redirect('/')

@app.post('/delete/<task_id>')
def delete(task_id):
    statement = "DELETE FROM events WHERE task_id = ?"
    insert(statement, (task_id))
    statement = "DELETE FROM tasks WHERE task_id = ?"
    insert(statement, (task_id))
    bottle.redirect('/')

app.run(host='localhost', port=8080, debug=True, reloader=True)