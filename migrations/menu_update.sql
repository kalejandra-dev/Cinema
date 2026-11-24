-- Cinema Paradiso: update an EXISTING MariaDB database to the new model.py
-- (menu categories and images, package images, movie release dates).
-- It only ADDS columns: movies, showtimes, food, bookings and users are kept.
-- Run it ONCE, e.g. from the lab computer:
--     mysql -h mysql.lab.it.uc3m.es -u 27_webapp_XX -p 27_webapp_XXa < migrations/menu_update.sql
-- A new database does not need this: init-db / reset-db already create these columns.

ALTER TABLE food_item
  ADD COLUMN category ENUM('drinks','popcorn','nachos','hot_dogs','sweets','other') NOT NULL DEFAULT 'other',
  ADD COLUMN detail VARCHAR(100) NOT NULL DEFAULT '',
  ADD COLUMN image_mime_type VARCHAR(128) NULL,
  ADD COLUMN image_data BLOB(2097152) NULL;

ALTER TABLE package
  ADD COLUMN image_mime_type VARCHAR(128) NULL,
  ADD COLUMN image_data BLOB(2097152) NULL;

ALTER TABLE movie
  ADD COLUMN release_date DATE NULL;
