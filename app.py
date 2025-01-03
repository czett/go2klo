from flask import Flask, render_template, redirect, session, request, url_for
import funcs, re

app = Flask(__name__)
app.secret_key = "wlfuiqhwelfiuwehfliwuehfwhevfjkhvgrlidzuf"

def check_login_status():
    if session.get("logged_in"):
        if session["logged_in"]:
            return True
    else:
        session["logged_in"] = False
        return False
    
    return True

def check_cookie_status():
    if session.get("cookies"):
        if session["cookies"]:
            return True
    else:
        session["cookies"] = False
        return False
    
    return True

def add_notification(notficiation: dict) -> None:
    # dict with keys title and text!!!!!

    if not session.get("notifications"):
        session["notifications"] = []

    current_notifications = session["notifications"]
    current_notifications.append(notficiation)

    session["notifications"] = current_notifications
    session.update()

@app.route("/")
def startpoint():
    check_cookie_status()
    return render_template("index.html", session=session)

@app.route("/login")
def login():
    return render_template("logreg.html", action="login", msg=None, session=session)

@app.route("/login/process", methods=["POST"])
def process_login():    
    try:
        username = request.form["username"]
        password = request.form["password"]

        if username and password:
            response = funcs.login(username, password)
            if response[0] == True:
                session["user"] = username
                session["logged_in"] = True
                return redirect("/")
            else:
                return render_template("logreg.html", action="login", msg=response[1], session=session)
    except:
        return redirect("/")

    return "Congrats, you worked around my code :)"

@app.route("/accept-cookies")
def accept_cookies(): 
    session["cookies"] = True
    session.modified = True   
    return redirect("/")

@app.route("/register")
def register():    
    return render_template("logreg.html", action="register", msg=None, session=session)

@app.route("/register/process", methods=["POST"])
def process_register():    
    try:
        username = request.form["username"]
        password = request.form["password"]

        if not bool(re.match("^[a-zA-Z0-9_]+$", username)): # name limitation
            return render_template("logreg.html", action="register", msg="Only letters, digits and underscores allowed!", session=session)

        if username and password:
            response = funcs.register(username, password)
            if response[0] == True:
                session["user"] = username
                session["logged_in"] = True
                return redirect("/")
            else:
                return render_template("logreg.html", action="register", msg=response[1], session=session)
    except:
        return redirect("/")
    
    return "Congrats, you worked around my code :)"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/rate")
def rate():
    if not check_login_status():
        return redirect("/")

    return render_template("get_location.html", session=session)

@app.route("/rate/process", methods=["POST"])
def process_rating():
    if not check_login_status():
        return redirect("/")

    query = request.form["location_query"]
    lat, lng = funcs.get_coordinates(query)

    session["rating_coords"] = (lat, lng)

    return render_template("rate.html", lat=lat, lng=lng, msg=None, session=session)

@app.route("/rate/finish", methods=["POST"])
def finish_rating():
    if not check_login_status():
        return redirect("/")

    cleanliness = request.form["cleanliness"]
    supplies = request.form["supplies"]
    privacy = request.form["privacy"]
    comment = request.form["comment"]
    user = session["user"]

    response = funcs.create_rating(cleanliness, supplies, privacy, comment, session["rating_coords"], user)
    
    if response[0] == True:
        return redirect("/")
    else:
        return render_template("rate.html", msg=response[1], session=session)
    
@app.route("/explore")
def explore():
    toilets = funcs.get_all_toilets()
    return render_template("explore.html", toilets=toilets, session=session)

@app.route("/api/toilets")
def toilets_api():
    toilets = funcs.get_all_toilets()
    return toilets

@app.route("/toilet/<tid>")
def toilet(tid):
    info = funcs.get_toilet_details(tid)
    info["address"] = str(funcs.coords_to_address(info["latitude"], info["longitude"]))
    # {'toilet_id': 2, 'latitude': 51.5149633, 'longitude': 7.4548106, 'ratings': [{'rating_id': 1, 'cleanliness': 3, 'supplies': 3, 'privacy': 3, 'comment': '', 'user': 'czett'}]}
    return render_template("toilet.html", toilet=info, session=session)

@app.route("/profile/<int:pid>")
def profile(pid):
    # if not funcs.check_user_exists(pid):
    #     return redirect("/")

    pid = int(pid)
    
    ratings = funcs.get_user_ratings(pid)
    uname = funcs.get_username_by_user_id(pid)

    user_achievements = funcs.get_achievements_by_user_id(pid)[1]

    # return str(ratings)

    # Calculate the average latitude and longitude for all rated toilets
    if ratings != []:
        avg_lat = sum(rating['latitude'] for rating in ratings) / len(ratings)
        avg_lon = sum(rating['longitude'] for rating in ratings) / len(ratings)
    else:
        # Default center if no ratings
        avg_lat, avg_lon = 51.505, -0.09 # default is uk or so

    if session.get("user"):
        if session["user"] == uname:
            own = True
        else:
            own = False

    # return nots as list of notifications, as of now list of dicts
    if uname == session["user"]:
        if session.get("notifications"):
            nots = session["notifications"]
        else:
            nots = []
    else:
        nots = []

    return render_template("profile.html", ratings=ratings, session=session, name=uname, avg_lat=avg_lat, avg_lon=avg_lon, own=own, achievements=user_achievements, nots=nots)

@app.route("/profile/<username>")
def profile_by_username(username):
    # Fetch the user ID using the username
    user_id = funcs.get_user_id_by_username(username)
    
    if not user_id:
        return redirect("/")  # Redirect to homepage if username does not exist
    
    # Redirect to the original profile route with user ID
    return redirect(url_for('profile', pid=user_id))

@app.route("/myprofile")
def my_profile():
    if not check_login_status():
        return redirect("/")
    
    username = session["user"]
    return redirect(f"/profile/{username}")

@app.route("/leaderboard")
def leaderboard():    
    leaderboard = funcs.get_users_sorted_by_ratings()
    return render_template("leaderboard.html", leaderboard=leaderboard, session=session)

@app.route("/clear-notifications")
def clear_notifications():
    if not check_login_status():
        return redirect("/")
    
    if session.get("notifications"):
        print(session["notifications"])
        session["notifications"] = []

    return redirect("/")
    
if __name__ == "__main__":
    app.run(debug=True, port=7000)