-- This table stores some information about users' subscription invoice.

CREATE TABLE invoice(
    -- A unique identifier of a user in telegram.
    telegram_user_id BIGINT PRIMARY KEY,
    -- Amount due.
    amount_due NUMERIC(12, 6) NOT NULL UNIQUE,
    -- Subscription period.
    days_valid INT NOT NULL,
    -- Payment expiration timestamp.
    payment_expiration_timestamp TIMESTAMP WITH TIME ZONE NOT NULL
); -- end create table users