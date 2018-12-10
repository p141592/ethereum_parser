#!/usr/bin/env bash

docker build -t eth_parser . && docker run -it --network="host" --name eth_parser --rm eth_parser