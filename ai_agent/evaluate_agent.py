import json
from pathlib import Path

try:
    from ai_agent.analyze_run import analyze_run
except ModuleNotFoundError:  # Support running from inside the ai_agent directory.
    from analyze_run import analyze_run


EVAL_DIR = Path(__file__).parent / "eval_cases"


def load_cases():
    cases = []

    for file in sorted(EVAL_DIR.glob("*.json")):
        with file.open(encoding="utf-8") as f:
            data = json.load(f)

        cases.append({
            "name": file.stem,
            "input": data["input"],
            "expected": data["expected"]
        })

    return cases


def evaluate_case(case):
    actual = analyze_run(case["input"])

    expected_status = case["expected"]["status"]
    expected_next = case["expected"]["recommended_next_test"]

    actual_status = actual.get("status")
    actual_next = actual.get("recommended_next_test")

    status_match = actual_status == expected_status
    next_match = actual_next == expected_next

    return {
        "name": case["name"],
        "expected_status": expected_status,
        "actual_status": actual_status,
        "status_match": status_match,
        "expected_next_test": expected_next,
        "actual_next_test": actual_next,
        "next_test_match": next_match,
        "passed": status_match and next_match
    }


def main():
    cases = load_cases()

    results = []

    for case in cases:
        print(f"\nEvaluating: {case['name']}")

        result = evaluate_case(case)
        results.append(result)

        print(
            f"Status: expected={result['expected_status']} "
            f"actual={result['actual_status']}"
        )

        print(
            f"Next test: expected={result['expected_next_test']} "
            f"actual={result['actual_next_test']}"
        )

        print(
            "Result:",
            "PASS" if result["passed"] else "FAIL"
        )

    passed = sum(1 for r in results if r["passed"])
    total = len(results)

    accuracy = (
        round((passed / total) * 100, 2)
        if total
        else 0.0
    )

    summary = {
        "total_cases": total,
        "passed_cases": passed,
        "accuracy_percent": accuracy,
        "results": results
    }

    output_file = (
        Path(__file__).parent
        / "evaluation_results.json"
    )

    with output_file.open(
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            summary,
            f,
            indent=2
        )

    print("\n====================")
    print(f"Accuracy: {accuracy}%")
    print(f"Passed: {passed}/{total}")
    print(f"Saved: {output_file}")


if __name__ == "__main__":
    main()
