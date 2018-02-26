CREATE TABLE users(
  username TEXT PRIMARY KEY,
  password TEXT NOT NULL,
  fullname TEXT NOT NULL,
  age INTEGER NOT NULL
);

CREATE TABLE tokens(
  username TEXT REFERENCES users(username),
  token TEXT PRIMARY KEY,
  expired BOOLEAN NOT NULL
);

CREATE TABLE diary_entries(
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  "text" TEXT NOT NULL,
  public BOOLEAN NOT NULL,
  username TEXT REFERENCES users(username)
)
