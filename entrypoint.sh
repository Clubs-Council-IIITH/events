#!/bin/bash

cp ./schema.graphql /subgraphs/events.graphql
uvicorn main:app --host 0.0.0.0 --port 80 --log-config ./uvicorn_config.json
