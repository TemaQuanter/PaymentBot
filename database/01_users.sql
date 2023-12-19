-- This table stores some information about users' subscription.

CREATE TABLE users(
    -- A unique identifier of a user in telegram.
    telegram_id BIGINT PRIMARY KEY,
    -- The subscription expiration date and time.
    subscription_expiration_timestamp TIMESTAMP WITH TIME ZONE,
    -- Amount due.
    amount_due NUMERIC(12, 6),
    -- Payment expiration timestamp.
    payment_expiration_timestamp TIMESTAMP WITH TIME ZONE
); -- end create table users