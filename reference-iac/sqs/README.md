# Simple Queue Service

## CloudFormation

See the template.yaml in this directory. To deploy, reference the local file,
give the stack a name, and provide any required parameters:

```
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name my-sqs-stack \
  --parameter-overrides MyQueueName=MyUserDefinedQueueName
```
