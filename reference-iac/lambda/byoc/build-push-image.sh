#!/bin/bash

# docker build --platform linux/amd64 --provenance=false -t my-lambda-fn .

docker build --platform linux/amd64 --provenance=false -t 440848399208.dkr.ecr.us-east-1.amazonaws.com/my-lambda-fn:latest .
docker push 440848399208.dkr.ecr.us-east-1.amazonaws.com/my-lambda-fn:latest
