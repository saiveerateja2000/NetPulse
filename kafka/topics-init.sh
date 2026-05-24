#!/usr/bin/env bash
set -e
for i in {1..30}; do
  if kafka-topics --bootstrap-server kafka:9092 --list >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

kafka-topics --bootstrap-server kafka:9092 \
  --create --if-not-exists \
  --topic netpulse.telemetry \
  --replication-factor 1 \
  --partitions 1
