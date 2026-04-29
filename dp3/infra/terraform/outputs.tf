output "dynamodb_table_name" {
  value       = aws_dynamodb_table.wildfire.name
  description = "DynamoDB table used by ingestion and API"
}

output "plot_bucket_name" {
  value       = aws_s3_bucket.plot.bucket
  description = "Public S3 plot bucket"
}

output "plot_url" {
  value       = "https://${aws_s3_bucket.plot.bucket}.s3.${var.aws_region}.amazonaws.com/${var.plot_key}"
  description = "Public URL returned by /plot"
}

output "ingest_lambda_name" {
  value       = aws_lambda_function.ingest.function_name
  description = "Scheduled ingest Lambda function"
}
