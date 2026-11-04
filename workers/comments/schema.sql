CREATE TABLE IF NOT EXISTS comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  page TEXT NOT NULL,
  name TEXT NOT NULL,
  body TEXT NOT NULL,
  created INTEGER NOT NULL,
  approved INTEGER NOT NULL DEFAULT 0,
  ip_hash TEXT
);
CREATE INDEX IF NOT EXISTS idx_comments_page ON comments(page, approved, created);
