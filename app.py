from flask import Flask, render_template, redirect, session, request
import funcs

app = Flask(__name__)
app.secret_key = "wlfuiqhwelfiuwehfliwuehfwhevfjkhvgrlidzuf"

def check_login_status():
    if session.get("logged_in"):
        if session["logged_in"]:
            return redirect("/")

@app.route("/")
def startpoint():
    return render_template("index.html", session=session)

@app.route("/login")
def login():
    check_login_status()
    
    return render_template("logreg.html", action="login", msg=None)

@app.route("/login/process", methods=["POST"])
def process_login():
    check_login_status()
    
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
    check_login_status()
    
    return render_template("logreg.html", action="register", msg=None)

@app.route("/register/process", methods=["POST"])
def process_register():
    check_login_status()
    
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
    check_login_status()

    return render_template("get_location.html")

@app.route("/rate/process", methods=["POST"])
def process_rating():
    check_login_status()

    query = request.form["location_query"]
    lat, lng = funcs.get_coordinates(query)

    session["rating_coords"] = (lat, lng)

    return render_template("rate.html", lat=lat, lng=lng, msg=None)

@app.route("/rate/finish", methods=["POST"])
def finish_rating():
    check_login_status()
    
    cleanliness = request.form["cleanliness"]
    supplies = request.form["supplies"]
    privacy = request.form["privacy"]
    comment = request.form["comment"]

    response = funcs.create_rating(cleanliness, supplies, privacy, comment, session["rating_coords"])
    
    if response[0] == True:
        return redirect("/")
    else:
        return render_template("rate.html", msg=response[1])
    
@app.route("/explore")
def explore():
    toilets = funcs.get_all_toilets()
    return render_template("explore.html", toilets=toilets)

@app.route("/api/toilets")
def toilets_api():
    toilets = funcs.get_all_toilets()
    return toilets

if __name__ == "__main__":
    app.run(debug=True, port=7000)