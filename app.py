from flask import Flask, render_template, redirect, session
import funcs

app = Flask(__name__)
app.secret_key = "wlfuiqhwelfiuwehfliwuehfwhevfjkhvgrlidzuf"

@app.route("/")
def startpoint():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=7000)