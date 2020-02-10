CREATE TABLE tasks (
    task_id INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    state INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    started_at INTEGER,
    finished_at INTEGER,
    parent_task_id INTEGER,
    FOREIGN KEY(parent_task_id) REFERENCES tasks(task_id)
);

PRAGMA foreign_keys = ON;

INSERT INTO tasks(description, state, created_at) VALUES ('This is an easy task', 1, 42);
INSERT INTO tasks(description, state, created_at) VALUES ('This is a hard task', 1, 1);
INSERT INTO tasks(description, state, created_at, parent_task_id) VALUES ('This is subtask', 1, 1, 2);
INSERT INTO tasks(description, state, created_at, parent_task_id) VALUES ('This is another subtask', 1, 1, 2);
INSERT INTO tasks(description, state, created_at, parent_task_id) VALUES ('This is a subsubtask', 1, 1, 4);