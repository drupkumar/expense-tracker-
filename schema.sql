CREATE DATABASE IF NOT EXISTS expense_tracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE expense_tracker;

CREATE TABLE IF NOT EXISTS user (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(180) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  phone VARCHAR(20) DEFAULT '',
  monthly_income FLOAT DEFAULT 0,
  currency VARCHAR(8) DEFAULT 'INR',
  theme VARCHAR(10) DEFAULT 'dark',
  reset_token VARCHAR(100) DEFAULT '',
  reset_token_expires DATETIME NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS category (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NULL,
  name VARCHAR(80) NOT NULL,
  kind VARCHAR(20) DEFAULT 'expense',
  icon VARCHAR(40) DEFAULT 'bi-tag',
  color VARCHAR(20) DEFAULT '#3ee0b0',
  UNIQUE (user_id, name),
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS transaction (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  category_id INT NOT NULL,
  amount FLOAT NOT NULL,
  kind VARCHAR(20) NOT NULL,
  note VARCHAR(255) DEFAULT '',
  merchant VARCHAR(120) DEFAULT '',
  payment_method VARCHAR(40) DEFAULT 'UPI',
  txn_date DATE,
  source VARCHAR(20) DEFAULT 'manual',
  receipt_path VARCHAR(255) DEFAULT '',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
  FOREIGN KEY (category_id) REFERENCES category(id)
);

CREATE TABLE IF NOT EXISTS budget (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  category_id INT NOT NULL,
  month INT NOT NULL,
  year INT NOT NULL,
  amount FLOAT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
  FOREIGN KEY (category_id) REFERENCES category(id)
);

CREATE TABLE IF NOT EXISTS goal (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  name VARCHAR(120) NOT NULL,
  target_amount FLOAT NOT NULL,
  saved_amount FLOAT DEFAULT 0,
  deadline DATE NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS recurring_transaction (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  category_id INT NOT NULL,
  amount FLOAT NOT NULL,
  kind VARCHAR(20) NOT NULL,
  note VARCHAR(255) DEFAULT '',
  merchant VARCHAR(120) DEFAULT '',
  payment_method VARCHAR(40) DEFAULT 'UPI',
  frequency VARCHAR(20) NOT NULL,
  next_due_date DATE NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
  FOREIGN KEY (category_id) REFERENCES category(id)
);

CREATE TABLE IF NOT EXISTS transfer (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  from_method VARCHAR(40) NOT NULL,
  to_method VARCHAR(40) NOT NULL,
  amount FLOAT NOT NULL,
  txn_date DATE,
  note VARCHAR(255) DEFAULT '',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS import_batch (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  fingerprint VARCHAR(64) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_id, fingerprint),
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- For an existing MySQL installation, apply these additive changes once:
-- ALTER TABLE user ADD COLUMN theme VARCHAR(10) DEFAULT 'dark';
-- CREATE TABLE import_batch (id INT PRIMARY KEY AUTO_INCREMENT, user_id INT NOT NULL,
--   fingerprint VARCHAR(64) NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
--   UNIQUE (user_id, fingerprint), FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE);
