#!/bin/bash

apt-get update && apt-get install -y docker.io
sleep 10
docker run -d -p 80:80 nginx
