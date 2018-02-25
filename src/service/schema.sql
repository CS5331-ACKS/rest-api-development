CREATE TABLE users(
  username TEXT PRIMARY KEY,
  password TEXT NOT NULL,
  fullname TEXT NOT NULL,
  age INTEGER NOT NULL
);

CREATE TABLE tokens(
  token TEXT PRIMARY KEY,
  expired BOOLEAN NOT NULL
)
