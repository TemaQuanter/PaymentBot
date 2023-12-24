-- This table stores some information about subscription plans.

CREATE TABLE subscription_plans(
    -- A unique identifier of a user in telegram.
    id SERIAL PRIMARY KEY,
    -- The subscription expiration date and time.
    days_valid INT NOT NULL,
    -- Amount due.
    amount_due NUMERIC(12, 6) NOT NULL
); -- end create table users


-- Insert some basic plans.
INSERT INTO subscription_plans VALUES
    (1, 90, 1350),
    (2, 30, 490);