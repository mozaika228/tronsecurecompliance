import argparse
import asyncio

import httpx


async def run(base_url: str) -> None:
    headers = {"X-Actor-Id": "1", "X-Actor-Role": "admin"}
    async with httpx.AsyncClient(base_url=base_url, timeout=20) as client:
        health = await client.get("/health")
        health.raise_for_status()

        aml = await client.post(
            "/api/v1/aml/check",
            json={"address": "TVjsMockAddress001", "network": "TRON"},
            headers=headers,
        )
        aml.raise_for_status()
        aml_payload = aml.json()

        create = await client.post(
            "/api/v1/requests",
            json={
                "address": "TVjsMockAddress001",
                "network": "TRON",
                "asset": "USDT",
                "amount": "150.00",
                "comment": "smoke test",
                "aml_check_id": aml_payload["check_id"],
            },
            headers=headers,
        )
        create.raise_for_status()
        req = create.json()

        submit = await client.post(f"/api/v1/requests/{req['id']}/submit", headers=headers)
        submit.raise_for_status()

        approve = await client.post(
            f"/api/v1/requests/{req['id']}/approve",
            json={"reason": "smoke approve"},
            headers=headers,
        )
        approve.raise_for_status()

        paid = await client.post(
            f"/api/v1/requests/{req['id']}/mark-paid",
            json={"tx_hash": f"smoke-{req['id'][:8]}"},
            headers=headers,
        )
        paid.raise_for_status()

        final_payload = paid.json()
        if final_payload["status"] != "paid":
            raise RuntimeError("Smoke failed: final status is not paid")

        print("Smoke OK")
        print(f"request_no={final_payload['request_no']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()
    asyncio.run(run(args.base_url))
