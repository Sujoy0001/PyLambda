import argparse
import json
import statistics
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def send_request(
    base_url: str, check_database: bool
) -> tuple[float, int | None, str | None]:
    started_at = time.perf_counter()
    try:
        if check_database:
            unique_id = uuid.uuid4().hex
            body = json.dumps(
                {
                    "username": f"loadtest-{unique_id}",
                    "useremail": f"loadtest-{unique_id}@example.com",
                    "password": "load-test-password",
                }
            ).encode("utf-8")
            request = Request(
                f"{base_url}/v1/auth/signup",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            expected_status = 201
        else:
            request = Request(f"{base_url}/health", method="GET")
            expected_status = 200

        with urlopen(request, timeout=30) as response:
            status_code = response.status
        error = (
            None if status_code == expected_status else "unexpected status"
        )
    except HTTPError as exception:
        status_code = exception.code
        error = "unexpected status"
    except (TimeoutError, URLError, OSError) as exception:
        status_code = None
        error = str(exception)

    return time.perf_counter() - started_at, status_code, error


def percentile(values: list[float], percentage: int) -> float:
    ordered = sorted(values)
    index = round((len(ordered) - 1) * percentage / 100)
    return ordered[index]


def run_check(
    label: str,
    base_url: str,
    requests: int,
    concurrency: int,
    check_database: bool,
) -> bool:
    started_at = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        results = list(
            executor.map(
                lambda _: send_request(
                    base_url, check_database
                ),
                range(requests),
            )
        )
    elapsed = time.perf_counter() - started_at

    latencies = [result[0] for result in results]
    successful = sum(result[2] is None for result in results)
    status_counts: dict[int, int] = {}
    errors: dict[str, int] = {}
    for _, status_code, error in results:
        if status_code is not None:
            status_counts[status_code] = status_counts.get(status_code, 0) + 1
        if error is not None:
            errors[error] = errors.get(error, 0) + 1

    print(f"\n{label}")
    print(f"  Requests:       {requests}")
    print(f"  Successful:     {successful}")
    print(f"  Failed:         {requests - successful}")
    print(f"  HTTP statuses:  {status_counts}")
    print(f"  Elapsed:        {elapsed:.2f} seconds")
    print(f"  Throughput:     {requests / elapsed:.2f} requests/second")
    print(f"  Latency avg:    {statistics.mean(latencies) * 1000:.2f} ms")
    print(f"  Latency p95:    {percentile(latencies, 95) * 1000:.2f} ms")
    print(f"  Latency max:    {max(latencies) * 1000:.2f} ms")
    if errors:
        print(f"  Errors:         {errors}")

    return successful == requests


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Measure app request and database-backed signup performance."
        )
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help=(
            "Base URL of the running app "
            "(default: http://127.0.0.1:8000)"
        ),
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=100,
        help="Number of requests per check (default: 100)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help=(
            "Maximum concurrent requests (default: 10)"
        ),
    )
    args = parser.parse_args()

    if args.requests < 1 or args.concurrency < 1:
        parser.error("--requests and --concurrency must both be positive")
    if args.concurrency > args.requests:
        parser.error("--concurrency cannot exceed --requests")

    base_url = args.base_url.rstrip("/")
    app_ok = run_check(
        "Application check (GET /health)",
        base_url,
        args.requests,
        args.concurrency,
        check_database=False,
    )
    db_ok = run_check(
        "Database check (POST /v1/auth/signup)",
        base_url,
        args.requests,
        args.concurrency,
        check_database=True,
    )

    print(
        "\nDatabase check creates test user records. "
        "Use this only with an app and database you control."
    )
    return 0 if app_ok and db_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
