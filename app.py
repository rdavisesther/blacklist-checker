from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/check", methods=["POST"])
def check():
    data = request.get_json(force=True)

    ips = data.get("ips", [])
    domains = data.get("domains", [])

    # Demo logic for now
    css = 0
    xbl = 0
    pbl = 0
    sbl = 0
    barracuda = 0
    dbl = 0
    clean = 0

    # IP demo counting
    for i, _ in enumerate(ips):
        if i % 7 == 0:
            css += 1
        elif i % 11 == 0:
            xbl += 1
        elif i % 5 == 0:
            pbl += 1
        elif i % 3 == 0:
            sbl += 1
        elif i % 9 == 0:
            barracuda += 1
        else:
            clean += 1

    # Domain demo counting
    for i, _ in enumerate(domains):
        if i % 2 == 0:
            dbl += 1

    return jsonify({
        "css": css,
        "xbl": xbl,
        "pbl": pbl,
        "sbl": sbl,
        "barracuda": barracuda,
        "clean": clean,
        "dbl": dbl
    })


if __name__ == "__main__":
    app.run(debug=True)