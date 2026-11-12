#!/usr/bin/env python3
"""Ensure the hospital db-init Lambda exists and run it.

- If <project>-db-init-service is missing (e.g. Terraform has not been
  applied yet), create it by cloning the VPC config, role, environment
  and layers of <project>-patient-service.
- Otherwise update its code and dependency layer.
- Then invoke it synchronously and fail if the initialisation fails.

Uses only the standard library and the `aws` CLI (already on the runner).
"""
import argparse
import json
import subprocess
import sys


def run_aws(*args, check=True):
    result = subprocess.run(["aws", *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(
            "aws %s failed: %s" % (" ".join(args[:4]), result.stderr.strip())
        )
    return result


def function_exists(name):
    return run_aws("lambda", "get-function", "--function-name", name, check=False).returncode == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, help="db-init deployment zip")
    parser.add_argument("--layer-arn", required=True, help="fresh dependency layer ARN")
    parser.add_argument("--project", default="hospital")
    args = parser.parse_args()

    fn = "%s-db-init-service" % args.project
    src = "%s-patient-service" % args.project

    if not function_exists(fn):
        cfg = json.loads(
            run_aws("lambda", "get-function-configuration", "--function-name", src).stdout
        )
        vpc = cfg.get("VpcConfig", {})
        env_vars = cfg.get("Environment", {}).get("Variables", {})
        create = [
            "lambda", "create-function",
            "--function-name", fn,
            "--runtime", "python3.11",
            "--handler", "lambda_function.lambda_handler",
            "--role", cfg["Role"],
            "--timeout", "300",
            "--memory-size", "256",
            "--zip-file", "fileb://%s" % args.zip,
            "--layers", args.layer_arn,
        ]
        if vpc.get("SubnetIds"):
            create += [
                "--vpc-config",
                "SubnetIds=%s,SecurityGroupIds=%s"
                % (",".join(vpc["SubnetIds"]), ",".join(vpc.get("SecurityGroupIds", []))),
            ]
        if env_vars:
            create += ["--environment", json.dumps({"Variables": env_vars})]
        run_aws(*create)
        run_aws("lambda", "wait", "function-active", "--function-name", fn)
        print("Created %s (cloned VPC/role/env from %s)" % (fn, src))
    else:
        run_aws("lambda", "update-function-code", "--function-name", fn,
                "--zip-file", "fileb://%s" % args.zip, "--publish")
        run_aws("lambda", "wait", "function-updated", "--function-name", fn)
        run_aws("lambda", "update-function-configuration", "--function-name", fn,
                "--layers", args.layer_arn)
        run_aws("lambda", "wait", "function-updated", "--function-name", fn)
        print("Updated code for %s" % fn)

    invoke = run_aws(
        "lambda", "invoke",
        "--function-name", fn,
        "--payload", "{}",
        "--cli-binary-format", "raw-in-base64-out",
        "/tmp/db-init-out.json",
    )
    meta = json.loads(invoke.stdout)
    with open("/tmp/db-init-out.json", encoding="utf-8") as f:
        raw = f.read()
    print("db-init result: %s" % raw[:2000])
    if meta.get("FunctionError") or meta.get("StatusCode") != 200:
        print("::error::db-init Lambda failed: %s" % raw[:500], file=sys.stderr)
        return 1
    try:
        result = json.loads(json.loads(raw).get("body", "{}"))
    except (ValueError, AttributeError):
        result = {}
    if not result.get("ok"):
        print("::error::db-init reported failure: %s" % raw[:500], file=sys.stderr)
        return 1
    print("Database initialisation succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
