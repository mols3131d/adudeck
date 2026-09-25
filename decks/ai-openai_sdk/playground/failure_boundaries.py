import openai
from openai import OpenAI

from _support.retry_server import synthetic_error_server

STATUS = 429
MAX_RETRIES = 2

print("sdk version:", openai.__version__)

with synthetic_error_server(STATUS) as server:
    client = OpenAI(
        api_key="local-test-key",
        base_url=server.base_url,
        max_retries=MAX_RETRIES,
        timeout=5.0,
    )

    try:
        client.responses.create(
            model="gpt-5.5",
            input="retry experiment",
        )
    except openai.APIStatusError as exc:
        print("exception:", type(exc).__name__)
        print("status:", exc.status_code)
        print("request id:", exc.request_id)
        print("HTTP attempts:", server.request_count)
