# API Gateway Routes

A single REST API Gateway (`HospitalAPI`) uses a **proxy** resource `{proxy+}`
so every path is forwarded to the matching Lambda via an
`AWS_PROXY` (Lambda Proxy) integration.

## Resource tree & integration targets

| Method | Path                          | Lambda             | Purpose                          |
|--------|-------------------------------|--------------------|----------------------------------|
| ANY    | /patients                     | patient-lambda     | List / create patients           |
| ANY    | /patients/{patient_id}        | patient-lambda     | Get / update / delete patient    |
| ANY    | /bills                        | billing-lambda     | List / create bills              |
| ANY    | /bills/{bill_id}              | billing-lambda     | Get / update / delete bill       |
| ANY    | /bills/patient/{patient_id}   | billing-lambda     | Bills for a patient               |
| ANY    | /payments                     | billing-lambda     | List / record payments            |
| ANY    | /payments/patient/{patient_id}| billing-lambda     | Payment history for a patient     |
| ANY    | /dues                         | billing-lambda     | All pending dues (synced)         |
| ANY    | /diseases                     | disease-lambda     | List / create diseases            |
| ANY    | /diseases/{disease_id}        | disease-lambda     | Get / update / delete disease     |
| ANY    | /diseases/patient/{patient_id}| disease-lambda     | Diseases for a patient            |
| ANY    | /diseases/active              | disease-lambda     | All active diseases               |
| ANY    | /doctors                      | doctor-lambda      | List / create doctors             |
| ANY    | /doctors/{doctor_id}          | doctor-lambda      | Get / update / delete doctor      |
| ANY    | /assignments                  | doctor-lambda      | List / create assignments         |
| ANY    | /assignments/{assignment_id}  | doctor-lambda      | Get / update / delete assignment |
| ANY    | /assignments/doctor/{doctor_id}  | doctor-lambda   | Assignments for a doctor          |
| ANY    | /assignments/patient/{patient_id}| doctor-lambda   | Assignments for a patient         |
| OPTIONS| /{proxy+}                     | (CORS mock)        | Preflight handling                |

## CORS
Enabled on every method with:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS`
- `Access-Control-Allow-Headers: Content-Type,Authorization`

Each Lambda also returns these headers directly (belt-and-suspenders).

## Deploy stages
- `prod` — production stage, URL pattern:
  `https://<api-id>.execute-api.<region>.amazonaws.com/prod`
- Set this URL as `API_GATEWAY_URL` env var on the Lambdas and as
  `window.HMS_CONFIG.apiBase` in the frontend `api.js`.

## Terraform
The API Gateway, resources, methods, integrations, and stage are all
provisioned in `terraform/main.tf`.
