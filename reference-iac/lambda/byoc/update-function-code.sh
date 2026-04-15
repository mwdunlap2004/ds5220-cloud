#!/bin/bash

aws lambda update-function-code \
  --function-name my-lambda-fn \
  --image-uri 440848399208.dkr.ecr.us-east-1.amazonaws.com/my-lambda-fn:latest
