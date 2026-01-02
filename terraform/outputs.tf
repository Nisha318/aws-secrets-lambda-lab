output "ddb_table_name" {
  value = aws_dynamodb_table.students.name
}

output "demo_secret_arn" {
  value = aws_secretsmanager_secret.demo.arn
}

output "seeder_lambda_name" {
  value = aws_lambda_function.seeder.function_name
}

output "reader_lambda_name" {
  value = aws_lambda_function.reader.function_name
}
