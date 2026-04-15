#!/bin/bash

aws iam create-policy-version \
  --policy-arn arn:aws:iam::440848399208:policy/lambda-s3-linecount-policy \
  --policy-document file://lambda-s3-policy.json \
  --set-as-default
