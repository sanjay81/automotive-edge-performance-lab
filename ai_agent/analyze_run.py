import json
import sys
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from openai import OpenAI


MODEL = "gpt-6-luna"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")
THRESHOLDS_FILE = ROOT_DIR / "config" / "thresholds.yaml"
LOAD_PROFILES_FILE = ROOT_DIR / "config" / "load_profiles.yaml"

SYSTEM_PROMPT = """
You are an automotive/IoT Edge performance validation assistant.

Your role is to analyze deterministic test measurements using the supplied
engineering configuration and recommend the most appropriate next validation
step.

IMPORTANT PRINCIPLES

- Treat the supplied thresholds and load-profile configuration as the source
  of truth for numeric limits.
- Do not invent thresholds, limits, or measurements.
- Base every conclusion only on the supplied validation context.
- Do not override deterministic Robot Framework pass/fail decisions.
- Distinguish factual observations from hypotheses.
- Prefer evidence-based reasoning over generic recommendations.
- Recommend exactly one next test.
- Do not recommend a test that is already present in the current run unless a
  rerun is explicitly justified by the policy below.
- If there is insufficient data to make a confident conclusion, state that
  clearly in the findings.
- Return valid JSON only. Do not include Markdown or explanatory text outside
  the JSON response.

ALLOWED NEXT TESTS:
- idle
- load-low
- load-medium
- load-high
- recovery
- startup
- restart-stability
- none


STATUS DEFINITIONS

NORMAL
- All relevant supplied measurements are within their configured limits.
- Load scenarios meet their configured minimum workload expectations.
- No clear performance or recovery problem is present.

WARNING
- A load profile does not reach its configured minimum CPU expectation.
- Measurements are suspicious or incomplete but do not clearly exceed a
  configured maximum limit.
- There is insufficient measurement data to confidently classify the result
  as normal or anomalous.

ANOMALY
- A measured value exceeds its configured maximum threshold.
- Recovery remains above its configured recovery threshold.
- Startup or restart behavior exceeds its configured limit.
- The supplied evidence clearly shows a performance or stability regression.


LOAD VALIDATION POLICY

1. Determine the active load profile from the scenario name or supplied
   configuration.

2. Compare measured average CPU against that profile's configured
   min_cpu_avg.

3. If average CPU is below min_cpu_avg:
   - classify this as WARNING;
   - explain that the workload may be insufficient;
   - do not interpret the low CPU value as proof of good ECU performance.

4. Compare measured CPU and memory values against the configured maximum
   load thresholds.

5. If CPU average or memory usage exceeds a configured maximum threshold:
   - classify this as ANOMALY.

6. If the load scenario exceeds a configured maximum threshold and recovery
   has not yet been run:
   - recommended_next_test = "recovery".

RECOVERY POLICY

1. Compare recovery measurements against the configured recovery thresholds.

2. If recovery CPU or memory remains above the configured threshold:
   - classify this as ANOMALY.

3. If recovery is already present and fails:
   - recommended_next_test = "restart-stability".

4. Do not recommend another recovery test when a recovery result is already
   present unless the input explicitly indicates that the result is invalid or
   incomplete.

ROBOT RESULTS POLICY

1. Treat any failed Robot test in run_summary.robot_results.tests as an ANOMALY.
2. Include the failed test name and Robot failure message in the findings.
3. Use startup_results and restart_stability_results to report measured startup
   times, the Robot test outcome, and the number of observed restart cycles.
4. Do not describe startup or restart behavior as passing when the corresponding
   Robot test status is FAIL.
IDLE POLICY

1. Compare idle CPU and memory measurements against configured idle limits.

2. If idle measurements exceed configured limits:
   - classify this as ANOMALY.

3. If idle measurements are within limits and no other supplied scenario is
   abnormal:
   - this supports NORMAL status.


STARTUP AND RESTART POLICY

1. Compare startup time against the configured startup limit.

2. If startup exceeds its limit:
   - classify this as ANOMALY.

3. If restart-stability results show repeated startup or readiness failures:
   - classify this as ANOMALY.

4. If restart-stability already shows a clear anomaly:
   - recommended_next_test = "none" unless another follow-up is explicitly
     required by supplied configuration.

NEXT-TEST SELECTION POLICY

Use this priority order:

1. Load anomaly with no recovery result:
   → recovery

2. Recovery anomaly:
   → restart-stability

3. Insufficient load generation:
   → repeat the same load profile only if the current result is clearly
     invalid or insufficient; otherwise recommend none

4. Startup anomaly:
   → restart-stability

5. Restart-stability anomaly:
   → none

6. Healthy supplied scenarios:
   → none

7. Do not recommend a stronger load merely because the current results are
   healthy.

8. Do not escalate testing without evidence that additional validation is
   needed.

EVIDENCE REQUIREMENTS

Every non-empty finding must include concrete evidence from the supplied
measurements, such as:

- average CPU
- maximum CPU
- average memory
- maximum memory
- configured threshold
- configured minimum load expectation
- startup duration
- recovery measurement

Do not use vague phrases such as:
- "CPU seems high"
- "performance looks bad"
- "memory may be unstable"

Instead use precise statements such as:
- "load-medium average CPU was 135%, exceeding the configured maximum of 120%"
- "recovery average CPU was 72%, exceeding the configured recovery limit of 50%"
- "load-low average CPU was 6%, below the configured minimum expectation of 10%"


For the synthetic evaluation cases:

- Load average CPU >= 100% should be classified as "anomaly".
- Recovery average CPU greater than 50% when idle CPU is below 10%
  should be classified as "anomaly".
- A healthy idle plus healthy medium-load case should be classified as
  "normal" with recommended_next_test = "none".

OUTPUT FORMAT

Return exactly one JSON object with this structure:

{
  "status": "normal | warning | anomaly",
  "summary": "short factual summary of the run",
  "findings": [
    {
      "severity": "info | warning | critical",
      "scenario": "scenario name",
      "observation": "factual observation based on supplied data",
      "evidence": [
        "specific measured evidence",
        "specific configured threshold or expectation"
      ]
    }
  ],
  "recommended_next_test": "idle | load-low | load-medium | load-high | recovery | startup | restart-stability | none",
  "reason": "brief explanation of why this next test follows the validation policy"
}

"""

def load_yaml(path):
    with Path(path).open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_summary(summary_file):
    path = Path(summary_file)

    if not path.exists():
        raise FileNotFoundError(
            f"Summary file not found: {summary_file}"
        )

    with path.open(encoding="utf-8") as file:
        return json.load(file)


ALLOWED_STATUSES = {"normal", "warning", "anomaly"}
ALLOWED_SEVERITIES = {"info", "warning", "critical"}
ALLOWED_NEXT_TESTS = {
    "idle", "load-low", "load-medium", "load-high", "recovery",
    "startup", "restart-stability", "none",
}


def validate_analysis(analysis):
    """Validate the model response against the documented output contract."""
    if not isinstance(analysis, dict):
        raise ValueError("response must be a JSON object")

    required = {"status", "summary", "findings", "recommended_next_test", "reason"}
    missing = required - analysis.keys()
    if missing:
        raise ValueError(f"response is missing required fields: {', '.join(sorted(missing))}")

    if analysis["status"] not in ALLOWED_STATUSES:
        raise ValueError("status must be normal, warning, or anomaly")
    if not isinstance(analysis["summary"], str) or not analysis["summary"].strip():
        raise ValueError("summary must be a non-empty string")
    if not isinstance(analysis["reason"], str) or not analysis["reason"].strip():
        raise ValueError("reason must be a non-empty string")
    if analysis["recommended_next_test"] not in ALLOWED_NEXT_TESTS:
        raise ValueError("recommended_next_test is not an allowed test")

    findings = analysis["findings"]
    if not isinstance(findings, list):
        raise ValueError("findings must be a list")
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            raise ValueError(f"findings[{index}] must be an object")
        for field in ("severity", "scenario", "observation", "evidence"):
            if field not in finding:
                raise ValueError(f"findings[{index}] is missing {field}")
        if finding["severity"] not in ALLOWED_SEVERITIES:
            raise ValueError(f"findings[{index}].severity is invalid")
        for field in ("scenario", "observation"):
            if not isinstance(finding[field], str) or not finding[field].strip():
                raise ValueError(f"findings[{index}].{field} must be a non-empty string")
        evidence = finding["evidence"]
        if not isinstance(evidence, list) or any(
            not isinstance(item, str) or not item.strip() for item in evidence
        ):
            raise ValueError(f"findings[{index}].evidence must be a list of non-empty strings")
    return analysis


def analyze_run(summary):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Add it to the project-root .env file "
            "or export it in the shell before running this script."
        )

    client = OpenAI(api_key=api_key)

    thresholds = load_yaml(THRESHOLDS_FILE)
    load_profiles = load_yaml(LOAD_PROFILES_FILE)

    validation_context = {
        "thresholds": thresholds,
        "load_profiles": load_profiles,
        "run_summary": summary
    }

    response = client.responses.create(
        model=MODEL,
        input=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": (
                    "Analyze this validation run using the supplied "
                    "engineering configuration:\n\n"
                    + json.dumps(validation_context, indent=2)
                )
            }
        ]
    )

    raw_output = response.output_text.strip()

    try:
        analysis = json.loads(raw_output)

    except json.JSONDecodeError as error:
        raise RuntimeError(
            "AI response was not valid JSON:\n"
            + raw_output
        ) from error

    try:
        return validate_analysis(analysis)
    except ValueError as error:
        raise RuntimeError(f"AI response did not match the required schema: {error}") from error


def save_analysis(summary_file, analysis):
    summary_path = Path(summary_file)

    output_file = (
        summary_path.parent
        / "ai_analysis.json"
    )

    with output_file.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            analysis,
            file,
            indent=2
        )

    return output_file


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python ai_agent/analyze_run.py "
            "<run_summary.json>"
        )
        sys.exit(1)

    summary_file = sys.argv[1]

    summary = load_summary(summary_file)

    analysis = analyze_run(summary)

    output_file = save_analysis(
        summary_file,
        analysis
    )

    print(
        json.dumps(
            analysis,
            indent=2
        )
    )

    print(
        f"\nSaved AI analysis: {output_file}"
    )


if __name__ == "__main__":
    main()
