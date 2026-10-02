from flask import Flask


app = Flask(__name__)


@app.get("/checkout")
def checkout() -> dict[str, int]:
    return {"total": 42000}


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8086, debug=False)
