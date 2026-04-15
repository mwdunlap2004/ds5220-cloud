#!/bin/bash

aws lambda invoke --function-name my-lambda-fn output.json
cat output.json
