-- Migration: add platform-admin test account (test_admin / 123456)
-- Safe to run multiple times — uses INSERT IGNORE (username has UNIQUE constraint).
-- After running this, execute `python database/init_users.py` to set the real password hash.

INSERT IGNORE INTO `user`
    (company_id, region_id, store_id, username, password, display_name, role, is_active)
VALUES
    (NULL, NULL, NULL, 'test_admin',
     'PLACEHOLDER_RUN_INIT_USERS',
     'Platform Admin', 'admin', 1);
