import sys
import httpx
import asyncio

API_URL = "http://localhost:8000"

async def run_audit():
    print("\n--- MedSight AI Security Audit ---\n")
    passed = 0
    total = 0

    def check(name, condition, error_msg):
        nonlocal passed, total
        total += 1
        if condition:
            print(f"✅ PASS: {name}")
            passed += 1
        else:
            print(f"❌ FAIL: {name} - {error_msg}")

    try:
        async with httpx.AsyncClient() as client:
            # 1. Test Health / Headers
            res = await client.get(f"{API_URL}/api/v1/health")
            headers = res.headers
            check("X-Content-Type-Options", headers.get("x-content-type-options") == "nosniff", "Header missing or incorrect")
            check("X-Frame-Options", headers.get("x-frame-options") == "DENY", "Header missing or incorrect")
            check("Permissions-Policy", "microphone=(self)" in headers.get("permissions-policy", ""), "Microphone permission misconfigured")
            check("No Server Header", "server" not in headers, "Server header is leaking framework info")

            # 2. Test CORS Rejection
            cors_res = await client.options(
                f"{API_URL}/api/v1/health",
                headers={"Origin": "http://evil-domain.com", "Access-Control-Request-Method": "GET"}
            )
            # Depending on FastAPI config, it might strip CORS headers or return 400. 
            # The key is it shouldn't return Access-Control-Allow-Origin: http://evil-domain.com
            check("CORS Restrictions", cors_res.headers.get("access-control-allow-origin") != "http://evil-domain.com", "CORS allowed untrusted origin")

    except httpx.ConnectError:
        print("❌ Server not running. Start it with: make run-dev")
        sys.exit(1)

    print(f"\nAudit Complete: {passed}/{total} Passed\n")

if __name__ == "__main__":
    asyncio.run(run_audit())
