from flask import Flask, render_template, redirect, session, request
import funcs

app = Flask(__name__)
app.secret_key = "wlfuiqhwelfiuwehfliwuehfwhevfjkhvgrlidzuf"

@app.route("/")
def startpoint():
    return render_template("index.html", session=session)

@app.route("/login")
def login():
    if session.get("logged_in"):
        if session["logged_in"]:
            return redirect("/")
    
    return render_template("logreg.html", action="login", msg=None)

@app.route("/login/process", methods=["POST"])
def process_login():
    if session.get("logged_in"):
        if session["logged_in"]:
            return redirect("/")
    
    username = request.form["username"]
    password = request.form["password"]

    if username and password:
        response = funcs.login(username, password)
        if response[0] == True:
            session["user"] = username
            session["logged_in"] = True
            return redirect("/")
        else:
            return render_template("logreg.html", action="login", msg=response[1])

    return "Congrats, you worked around my code :)"

@app.route("/register")
def register():
    if session.get("logged_in"):
        if session["logged_in"]:
            return redirect("/")
    
    return render_template("logreg.html", action="register", msg=None)

@app.route("/register/process", methods=["POST"])
def process_register():
    if session.get("logged_in"):
        if session["logged_in"]:
            return redirect("/")
    
    username = request.form["username"]
    password = request.form["password"]

    if username and password:
        response = funcs.register(username, password)
        if response[0] == True:
            session["user"] = username
            session["logged_in"] = True
            return redirect("/")
        else:
            return render_template("logreg.html", action="register", msg=response[1])

    return "Congrats, you worked around my code :)"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/rate")
def rate():
    # logged in checker missing!
    return render_template("get_location.html")

@app.route("/rate/process", methods=["POST"])
def process_rating():
    # logged in checker missing!
    query = request.form["location_query"]
    lat, lng = funcs.get_coordinates(query)

    return render_template("rate.html", lat=lat, lng=lng)

if __name__ == "__main__":
    app.run(debug=True, port=7000)