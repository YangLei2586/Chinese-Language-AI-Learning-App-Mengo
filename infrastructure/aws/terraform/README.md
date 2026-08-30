# Terraform skeleton contract

This is intentionally a non-provisioning skeleton. Add reviewed Terraform modules following the layout in `../README.md`; do not place provider credentials, `.tfvars` secrets, Terraform state, account IDs, or resource imports here.

Each module must expose least-privilege IAM, encryption, tags, monitoring, and deletion/retention controls as explicit inputs. Environments must consume immutable image digests and Secrets Manager ARNs, never raw secret values.
