variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "name_prefix" {
  type    = string
  default = "aws-secrets-lab"
}

variable "tags" {
  type    = map(string)
  default = {
    Project = "AWS-Secrets-Lambda-Lab"
    Owner   = "NotesByNisha"
  }
}

variable "demo_secret_json" {
  description = "Demo JSON secret value stored in Secrets Manager."
  type        = map(string)
  default = {
    app_user     = "demo-user"
    app_password = "demo-password-change-me"
  }
}
