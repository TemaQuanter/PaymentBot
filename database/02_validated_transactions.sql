-- This table stores validated transactions that were used for payments.

CREATE TABLE validated_transactions(
    -- Transaction hash/id.
    transaction_id VARCHAR(64) PRIMARY KEY,
    -- Transaction timestamp.
    transaction_timestamp TIMESTAMP WITH TIME ZONE NOT NULL
); -- end create table validated_transactions