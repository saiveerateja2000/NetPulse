#!/usr/bin/env bash
set -e
BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS:-kafka:29092}"
for i in {1..30}; do
  if kafka-topics --bootstrap-server "${BOOTSTRAP_SERVERS}" --list >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

kafka-topics --bootstrap-server "${BOOTSTRAP_SERVERS}" \
  --create --if-not-exists \
  --topic netpulse.telemetry \
  --replication-factor 1 \
  --partitions 1
