import os

import pytest
from mcp.server.fastmcp import FastMCP

from tests.agentic.agent_runner import run_agent
from tests.agentic.invariants import check_purchase_invariants
from tests.agentic.judge import judge_run

INSTRUCTION = "Buy me a medium blue t-shirt under $30 and ship it to my saved address."

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="requires a real ANTHROPIC_API_KEY to drive the agent + judge",
)


async def test_agentic_purchase_flow_pass_rate(
    seeded_mcp_server: FastMCP, request: pytest.FixtureRequest
) -> None:
    runs = request.config.getoption("--runs")
    report = []

    for i in range(runs):
        result = await run_agent(INSTRUCTION, seeded_mcp_server)
        invariants = check_purchase_invariants(
            cart=result.last_cart,
            order=result.last_order,
            expected_sku="TSHIRT-BLUE-M",
            max_total_cents=3000,
        )
        invariants_passed = all(inv.passed for inv in invariants)
        judge_passed, judge_reason = await judge_run(result)
        report.append(
            {
                "run": i + 1,
                "invariants_passed": invariants_passed,
                "failed_invariants": [inv.description for inv in invariants if not inv.passed],
                "judge_passed": judge_passed,
                "judge_reason": judge_reason,
            }
        )

    pass_count = sum(1 for r in report if r["invariants_passed"] and r["judge_passed"])
    pass_rate = pass_count / runs

    print("\n--- Agentic eval pass-rate report ---")
    for r in report:
        print(
            f"run {r['run']}: invariants={r['invariants_passed']} "
            f"(failed={r['failed_invariants']}) judge={r['judge_passed']} ({r['judge_reason']})"
        )
    print(f"pass rate: {pass_rate:.0%} ({pass_count}/{runs})")

    assert pass_rate >= 0.8
