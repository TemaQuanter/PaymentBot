#!bin/bash

# This script assembles and then runs a PostgreSQL database.
# WARNING: This script should be used for development purposes ONLY!!!

# Import environmental variables necessary to create PostgreSQL database.
source ./scripts/helpers/load_env.sh

# Load environmental variables.
load_env '.env'

# Stop and remove the existing docker containser.
docker stop payment_bot_db
docker rm payment_bot_db

# Remove image.
docker rmi payment_bot_db

# Create a new image.
docker build -t payment_bot_db -f docker/postgresql.dockerfile .

# echo "POSTGRES_USER=$POSTGRES_USER"
# echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD"
# echo "POSTGRES_DB=$POSTGRES_DB"

# Run the database.
docker run -e POSTGRES_USER=$POSTGRES_USER -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD -e POSTGRES_DB=$POSTGRES_DB -e TG_SUPERUSER_ID=$TG_SUPERUSER_ID -e TG_SUPERUSER_USERNAME=$TG_SUPERUSER_USERNAME -e TG_SUPERUSER_STATUS_ID=$TG_SUPERUSER_STATUS_ID -e TG_SUPERUSER_ROLE_ID=$TG_SUPERUSER_ROLE_ID -d -p 5432:5432 --name payment_bot_db payment_bot_db