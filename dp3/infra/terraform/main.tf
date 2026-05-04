provider "aws" {
  region = var.aws_region
}

locals {
  tags = merge(
    {
      Project = var.name
      Managed = "terraform"
    },
    var.tags,
  )
}

data "aws_caller_identity" "current" {}

resource "aws_dynamodb_table" "wildfire" {
  name         = "${var.name}-firms"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = local.tags
}

resource "aws_s3_bucket" "plot" {
  bucket = var.plot_bucket_name != "" ? var.plot_bucket_name : "${var.name}-plot-${data.aws_caller_identity.current.account_id}-${var.aws_region}"
  tags   = local.tags
}

resource "aws_s3_bucket_public_access_block" "plot" {
  bucket = aws_s3_bucket.plot.id

  block_public_acls       = false
  ignore_public_acls      = false
  block_public_policy     = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "plot_public_read" {
  bucket = aws_s3_bucket.plot.id
  depends_on = [aws_s3_bucket_public_access_block.plot]
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid       = "AllowPublicReadLatestPlotPrefix",
        Effect    = "Allow",
        Principal = "*",
        Action    = ["s3:GetObject"],
        Resource = [
          "${aws_s3_bucket.plot.arn}/latest/*"
        ]
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "ingest" {
  name              = "/aws/lambda/${var.name}-ingest"
  retention_in_days = 30
  tags              = local.tags
}

resource "aws_iam_role" "ingest_lambda" {
  name = "${var.name}-ingest-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "ingest_basic" {
  role       = aws_iam_role.ingest_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "ingest_data_access" {
  name = "${var.name}-ingest-data"
  role = aws_iam_role.ingest_lambda.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "dynamodb:PutItem",
          "dynamodb:BatchWriteItem",
          "dynamodb:Query"
        ],
        Resource = aws_dynamodb_table.wildfire.arn
      },
      {
        Effect = "Allow",
        Action = [
          "s3:PutObject"
        ],
        Resource = "${aws_s3_bucket.plot.arn}/*"
      }
    ]
  })
}

resource "aws_lambda_function" "ingest" {
  function_name = "${var.name}-ingest"
  role          = aws_iam_role.ingest_lambda.arn
  handler       = "ingestion.handler.lambda_handler"
  runtime       = "python3.12"
  architectures = ["arm64"]
  timeout       = 300
  memory_size   = 1024

  filename         = var.lambda_zip_path
  source_code_hash = filebase64sha256(var.lambda_zip_path)

  environment {
    variables = {
      FIRMS_MAP_KEY  = var.firms_map_key
      DDB_TABLE_NAME = aws_dynamodb_table.wildfire.name
      PLOT_BUCKET    = aws_s3_bucket.plot.bucket
      PLOT_KEY       = var.plot_key
      MAP_PLOT_KEY   = "latest/wildfire_map_latest.png"
      TTL_DAYS       = tostring(var.ttl_days)
      DAY_RANGE      = tostring(var.day_range)
      MIN_CONFIDENCE = tostring(var.min_confidence)
      DAYTIME_ONLY   = tostring(var.daytime_only)
      FIRMS_AREA     = var.firms_area
    }
  }

  tags = local.tags
}

resource "aws_cloudwatch_event_rule" "ingest_schedule" {
  name                = "${var.name}-ingest-schedule"
  schedule_expression = var.schedule_expression
  tags                = local.tags
}

resource "aws_cloudwatch_event_target" "ingest_target" {
  rule      = aws_cloudwatch_event_rule.ingest_schedule.name
  target_id = "IngestLambda"
  arn       = aws_lambda_function.ingest.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingest.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ingest_schedule.arn
}
