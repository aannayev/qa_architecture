#!/usr/bin/env bash
# Creates one logical database + dedicated role per service.
# Runs once at first Postgres startup (Docker entrypoint contract).
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<'SQL'
-- history
CREATE ROLE history LOGIN PASSWORD 'history';
CREATE DATABASE history OWNER history;

-- physics
CREATE ROLE physics LOGIN PASSWORD 'physics';
CREATE DATABASE physics OWNER physics;

-- math
CREATE ROLE math LOGIN PASSWORD 'math';
CREATE DATABASE math OWNER math;

-- geography
CREATE ROLE geography LOGIN PASSWORD 'geography';
CREATE DATABASE geography OWNER geography;

-- exam orchestrator
CREATE ROLE orchestrator LOGIN PASSWORD 'orchestrator';
CREATE DATABASE orchestrator OWNER orchestrator;

-- ai assistant (audit + eval runs)
CREATE ROLE ai_assistant LOGIN PASSWORD 'ai_assistant';
CREATE DATABASE ai_assistant OWNER ai_assistant;

-- unleash feature flag store
CREATE ROLE unleash LOGIN PASSWORD 'unleash';
CREATE DATABASE unleash OWNER unleash;
SQL

echo "Per-service databases created."
