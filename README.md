---
title: FastAPI
description: A FastAPI server
tags:
  - fastapi
  - hypercorn
  - python
---

# FastAPI Example

This example starts up a [FastAPI](https://fastapi.tiangolo.com/) server.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/-NvLj4?referralCode=CRJ8FE)
## ✨ Features

- FastAPI
- [Uvicorn](https://www.uvicorn.org/)
- Python 3

## 💁‍♀️ How to use

- Clone locally and install packages with pip using `pip install -r requirements.txt`
- Run locally using `uvicorn main:app --reload`

## 📝 Notes

- To learn about how to use FastAPI with most of its features, you can visit the [FastAPI Documentation](https://fastapi.tiangolo.com/tutorial/)
- To learn about Hypercorn and how to configure it, read their [Documentation](https://hypercorn.readthedocs.io/)

## ☁️ AWS deployment (Lambda + S3)

The app runs on AWS Lambda behind a Lambda Function URL (HTTPS, no servers to
manage); generated workbooks are stored in a private S3 bucket and deleted
after 7 days. At low traffic this costs effectively nothing.

How it fits together: `Dockerfile` builds a normal FastAPI container that also
includes the [AWS Lambda Web Adapter](https://github.com/awslabs/aws-lambda-web-adapter),
and `template.yaml` (AWS SAM) creates the function, its URL, the bucket and
permissions. The same image still runs anywhere with `docker run`.

### Deploying (no local tools needed)

GitHub Actions builds and deploys on every push to `main`
(`.github/workflows/deploy-aws.yml`). It signs in to AWS with GitHub's OIDC
identity — no AWS keys are stored in GitHub — and can only do so from
workflows running on `main` of this repository.

**1. One-time AWS setup (AWS console, ~5 minutes)**

1. In the AWS console, pick the region you want (top-right), e.g. `us-east-1`.
2. Open **CloudFormation → Create stack → With new resources**.
3. Choose **Upload a template file** and upload **`deploy/aws-bootstrap.yaml`**
   (on GitHub open the `deploy` folder → `aws-bootstrap.yaml` → *Download raw
   file*). Not `template.yaml` at the repo root — that one is deployed by the
   workflow and fails in the console with "'ImageUri' must be set". On the next
   screen the parameters should be `GitHubRepo`, `GitHubBranch`,
   `AppStackName` and `CreateOidcProvider`.
4. Stack name: **`github-deploy-setup`** (the workflow looks for this name).
5. Parameters: keep the defaults. If **IAM → Identity providers** already lists
   `token.actions.githubusercontent.com`, set `CreateOidcProvider` to `false`.
6. Tick **"I acknowledge that AWS CloudFormation might create IAM resources
   with custom names"** and create the stack.
7. When it shows `CREATE_COMPLETE`, open the **Outputs** tab and copy
   `DeployRoleArn`.

**2. GitHub settings (Settings → Secrets and variables → Actions)**

| Kind | Name | Value |
| --- | --- | --- |
| Variable | `AWS_DEPLOY_ROLE_ARN` | the `DeployRoleArn` you copied |
| Variable | `AWS_REGION` | the region from step 1, e.g. `us-east-1` |
| Secret | `ACTION_API_KEY` | a random string of 40+ letters and digits (e.g. from a password manager); the GPT Action sends it as `X-API-Key` |
| Variable (optional) | `PUBLIC_BASE_URL` | only if you put a custom domain in front, e.g. `https://api.example.com` |

**3. Deploy**

Merge to `main`, or go to **Actions → Deploy to AWS → Run workflow**. The
run summary shows the API base URL; the workflow fails if `/health` on the
new deployment doesn't report `"storage": "s3"`. Until step 2 is done the
workflow is skipped rather than failing.

**4. Switch over**

Point the Custom GPT Action's server URL at the new base URL, run one real
PDF through it, then retire the Railway service and delete `railway.json`,
`railway.toml`, `nixpacks.toml` and `procfile`.

Deploying from your own machine instead also works if you have the AWS CLI,
SAM CLI and Docker: `sam build && sam deploy --guided`.

### Environment variables

| Variable | Purpose |
| --- | --- |
| `PUBLIC_BASE_URL` | Origin used in returned `download_url` links. Falls back to `RAILWAY_PUBLIC_URL`, then to the request's own URL |
| `ACTION_API_KEY` | If set, `/actions/generate_proposal_from_pdf` requires `X-API-Key` |
| `BOYD_S3_BUCKET` | If set, workbooks are stored in this bucket and `/download/...` redirects to a short-lived signed S3 link. If unset, they're kept on local disk (single-instance hosts only) |
| `BOYD_S3_PREFIX` | Key prefix in the bucket (default `proposals/`) |
| `BOYD_DOWNLOAD_URL_TTL_SECONDS` | Lifetime of each signed S3 link (default `300`) |
| `BOYD_OUTPUT_DIR` | Scratch / local storage directory (default `/tmp/output`) |
| `PORT` | Listen port (default `8000`) |

### Limits on Lambda

- Request bodies are capped at 6 MB, so PDFs uploaded through the web page
  (sent as base64) must be under ~4.5 MB. The GPT Action endpoint is not
  affected — it fetches the PDF from OpenAI's link.
- The first request after a quiet period takes a few extra seconds (cold start).

### Running locally

```sh
docker build -t boyd-api .
docker run -p 8000:8000 boyd-api
```
