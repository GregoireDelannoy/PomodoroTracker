CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT NOT NULL UNIQUE
);

INSERT INTO users (name, email) VALUES ('John', 'john@doe.com');

CREATE TABLE tasks (
    task_id INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    owner_user_id INTEGER NOT NULL REFERENCES users(user_id)
);

INSERT INTO tasks(description, owner_user_id) VALUES ('This is an easy task', 0);
INSERT INTO tasks(description, owner_user_id) VALUES ('This is a hard task', 0);

-- CREATE TABLE event_types (
--     event_type_id INTEGER PRIMARY KEY,
--     code TEXT NOT NULL
-- );

-- INSERT INTO event_types (code) VALUES ('CREATED');
-- INSERT INTO event_types (code) VALUES ('STARTED');
-- INSERT INTO event_types (code) VALUES ('DONE');
-- INSERT INTO event_types (code) VALUES ('CANCELLED');
-- INSERT INTO event_types (code) VALUES ('FAILED');

CREATE TABLE events (
    event_id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    type TEXT NOT NULL,
    task_id INTEGER NOT NULL REFERENCES tasks(task_id)
);
