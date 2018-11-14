#!/usr/bin/env bash

docker build -t eth_explorer . && docker run -it eth_explorer