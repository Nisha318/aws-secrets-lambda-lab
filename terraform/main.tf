terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = ">= 2.4"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  name_prefix = var.name_prefix
}

# -------------------------
# DynamoDB
# -------------------------
resource "aws_dynamodb_table" "students" {
  name         = "${local.name_prefix}-students"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "StudId"

  attribute {
    name = "StudId"
    type = "N"
  }

  tags = var.tags
}

# -------------------------
# Secrets Manager (demo JSON secret)
# -------------------------
resource "aws_secretsmanager_secret" "demo" {
  name        = "${local.name_prefix}-demo-secret"
  description = "Demo JSON secret for the lab (not required for DynamoDB access)."
  tags        = var.tags
}

resource "aws_secretsmanager_secret_version" "demo" {
  secret_id     = aws_secretsmanager_secret.demo.id
  secret_string = jsonencode(var.demo_secret_json)
}

# -------------------------
# IAM role for Lambda
# -------------------------
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = "${local.name_prefix}-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = var.tags
}

# Least privilege policy for this lab
data "aws_iam_policy_document" "lambda_policy" {
  statement {
    sid     = "Logs"
    effect  = "Allow"
    actions = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }

  statement {
    sid    = "DynamoDBAccess"
    effect = "Allow"
    actions = [
      "dynamodb:PutItem",
      "dynamodb:BatchWriteItem",
      "dynamodb:Scan",
      "dynamodb:GetItem",
      "dynamodb:DescribeTable"
    ]
    resources = [aws_dynamodb_table.students.arn]
  }

  # Optional: allow demo secret retrieval (kept separate and scoped to one secret)
  statement {
    sid     = "SecretsRead"
    effect  = "Allow"
    actions = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    resources = [aws_secretsmanager_secret.demo.arn]
  }
}

resource "aws_iam_policy" "lambda_policy" {
  name   = "${local.name_prefix}-lambda-policy"
  policy = data.aws_iam_policy_document.lambda_policy.json
  tags   = var.tags
}

resource "aws_iam_role_policy_attachment" "lambda_attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

# -------------------------
# Package Lambda code
# -------------------------
data "archive_file" "reader_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/reader.py"
  output_path = "${path.module}/build/reader.zip"
}

data "archive_file" "seeder_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/seeder.py"
  output_path = "${path.module}/build/seeder.zip"
}

resource "aws_lambda_function" "seeder" {
  function_name = "${local.name_prefix}-seeder"
  role          = aws_iam_role.lambda_role.arn
  handler       = "seeder.lambda_handler"
  runtime       = "python3.12"

  filename         = data.archive_file.seeder_zip.output_path
  source_code_hash = data.archive_file.seeder_zip.output_base64sha256
  timeout          = 10

  environment {
    variables = {
      DDB_TABLE  = aws_dynamodb_table.students.name
      SECRET_ARN = aws_secretsmanager_secret.demo.arn
    }
  }

  tags = var.tags
}

resource "aws_lambda_function" "reader" {
  function_name = "${local.name_prefix}-reader"
  role          = aws_iam_role.lambda_role.arn
  handler       = "reader.lambda_handler"
  runtime       = "python3.12"

  filename         = data.archive_file.reader_zip.output_path
  source_code_hash = data.archive_file.reader_zip.output_base64sha256
  timeout          = 10

  environment {
    variables = {
      DDB_TABLE = aws_dynamodb_table.students.name
    }
  }

  tags = var.tags
}

resource "null_resource" "build_dir" {
  provisioner "local-exec" {
    command = "powershell -Command \"New-Item -ItemType Directory -Force ${path.module}\\build | Out-Null\""
  }
}

