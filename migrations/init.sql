-- Создание таблиц для MVP
CREATE TABLE IF NOT EXISTS users (
                                     user_id INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS busy (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    user_id INTEGER NOT NULL,
                                    label TEXT NOT NULL,
                                    start_ts INTEGER NOT NULL,
                                    end_ts INTEGER NOT NULL,
                                    FOREIGN KEY(user_id) REFERENCES users(user_id)
    );

CREATE TABLE IF NOT EXISTS tasks (
                                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                                     user_id INTEGER NOT NULL,
                                     label TEXT NOT NULL,
                                     duration_hours REAL NOT NULL,
                                     preferred_days TEXT,
                                     FOREIGN KEY(user_id) REFERENCES users(user_id)
    );

CREATE TABLE IF NOT EXISTS settings (
                                        user_id INTEGER PRIMARY KEY,
                                        start_hour INTEGER NOT NULL,
                                        end_hour INTEGER NOT NULL,
                                        FOREIGN KEY(user_id) REFERENCES users(user_id)
    );