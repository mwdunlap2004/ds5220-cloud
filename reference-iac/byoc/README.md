# BYOC Lambda

```
docker build -t my-lambda-fn .
```

```
# Authenticate
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789.dkr.ecr.us-east-1.amazonaws.com

# Tag
docker tag my-lambda-fn:latest \
  123456789.dkr.ecr.us-east-1.amazonaws.com/my-lambda-fn:latest

# Push
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/my-lambda-fn:latest
```

```
aws lambda create-function \
  --function-name my-lambda-fn \
  --package-type Image \
  --code ImageUri=123456789.dkr.ecr.us-east-1.amazonaws.com/my-lambda-fn:latest \
  --role arn:aws:iam::123456789:role/lambda-execution-role
```

```
aws lambda invoke --function-name my-lambda-fn output.json
cat output.json
```
