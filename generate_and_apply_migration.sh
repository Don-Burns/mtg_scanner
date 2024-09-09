#!/bin/bash
# Script to migrate db to the latest version of db schema
set -eou pipefail

MIGRATION_MESSAGE=$1
if [ -z $MIGRATION_MESSAGE ]; then
    echo "Please provide a migration message"
    exit 1
fi

set -x # don't need the validation shown in the terminal

# make sure db is up to latest version
alembic upgrade head
# generate migration
alembic revision --autogenerate -m "${MIGRATION_MESSAGE}"
# apply migration
alembic upgrade head
