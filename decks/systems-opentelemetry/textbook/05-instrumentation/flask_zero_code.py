import argparse

from flask import Flask


app = Flask(__name__)


@app.get("/checkout")
def checkout() -> dict[str, int]:
    return {"total": 42000}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8086)
    args = parser.parse_args()
    app.run(host="127.0.0.1", port=args.port, debug=False, use_reloader=False)
