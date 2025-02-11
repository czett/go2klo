from flask import Flask, render_template, redirect, session, request, url_for, jsonify
import funcs, re, random, json
from werkzeug.exceptions import HTTPException
from better_profanity import profanity

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
        session["lang"] = "english"
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

def get_texts(lang:str, template:str) -> dict:
    with open("static/langs/langs.json", "r", encoding="utf-8") as file:
        content = json.load(file)["langs"]
    
    req_content = content[lang][template]
    base = content[lang]["base"]
    req_content.update(base)

    return req_content

@app.route("/")
def startpoint():
    check_cookie_status()
    
    rated = (False, "") # normie case :3
    if session.get("rated"):
        rated = session["rated"]

    ts = get_texts(session["lang"], "index")

    session["rated"] = (False, "")
    return render_template("index.html", session=session, rated=rated, ts=ts)

@app.route("/login")
def login():
    check_cookie_status()
    ts = get_texts(session["lang"], "logreg")
    return render_template("logreg.html", action="login", msg=None, ts=ts, session=session)

@app.route("/login/process", methods=["POST"])
def process_login():    
    check_cookie_status()
    ts = get_texts(session["lang"], "logreg")

    try:
        username = request.form["username"]
        password = request.form["password"]

        if username and password:
            username = username.lower()
            response = funcs.login(username, password)
            if response[0] == True:
                session["user"] = username
                session["logged_in"] = True
                return redirect("/")
            else:
                return render_template("logreg.html", action="login", msg=response[1], session=session, ts=ts)
    except:
        return redirect("/")

    return "Congrats, you worked around my code :)"

@app.route("/accept-cookies")
def accept_cookies(): 
    session["cookies"] = True
    session.modified = True   
    return redirect("/")

@app.route("/switchlang")
def switchlang():
    langs = ["english", "german", "italian", "bulgarian", "french", "spanish", "norwegian", "albanian", "austrian"]
    clang = session["lang"]

    if clang != langs[-1]:
        session["lang"] = langs[1 + langs.index(clang)] 
    else:
        session["lang"] = langs[0]

    session.modified = True   
    return redirect("/")

@app.route("/switchlang/<lang>")
def switchlang_picked(lang):
    langs = ["english", "german", "italian", "bulgarian", "french", "spanish", "norwegian", "albanian", "austrian"]
    # clang = session["lang"]

    if lang in langs:
        session["lang"] = lang
    else:
        return redirect("/error/404")

    session.modified = True   
    return redirect("/")

@app.route("/register")
def register():
    check_cookie_status()
    ts = get_texts(session["lang"], "logreg")
    return render_template("logreg.html", action="register", ts=ts, msg=None, session=session)

@app.route("/register/process", methods=["POST"])
def process_register():
    check_cookie_status()
    ts = get_texts(session["lang"], "logreg")
    
    try:
        username = request.form["username"]
        password = request.form["password"]

        if not re.match("^[A-Za-z0-9_]*$", username): # only letters, digits, and underscores
            return render_template("logreg.html", action="register", msg="Only letters, digits and underscores allowed!", session=session, ts=ts)
        elif not re.match("^[A-Za-z0-9_]*$", password):
            return render_template("logreg.html", action="register", msg="Only letters, digits and underscores allowed!", session=session, ts=ts)
        elif len(username) < 3 or len(username) > 20:
            return render_template("logreg.html", action="register", msg="Username too short or too long! (min. 3, max. 20 characters)", session=session, ts=ts)
        elif len(password) < 6:
            return render_template("logreg.html", action="register", msg="Password too short! (min. 6 characters)", session=session, ts=ts)
            
        username = username.lower()
        
        if profanity.contains_profanity(username):
            return render_template("logreg.html", action="register", msg="Bad words detected! Try a proper username", session=session, ts=ts)

        if len(username) > 20:
            return render_template("logreg.html", action="register", msg="Username too long! (max. 20 characters)", session=session, ts=ts)

        if username and password:
            response = funcs.register(username, password)
            if response[0] == True:
                session["user"] = username
                session["logged_in"] = True
                return redirect("/")
            else:
                return render_template("logreg.html", action="register", msg=response[1], session=session, ts=ts)
    except:
        return redirect("/explore")
    
    return "Congrats, you worked around my code :)"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/rate")
def rate():
    check_cookie_status()
    if not check_login_status():
        return redirect("/login")
    
    ts = get_texts(session["lang"], "get_location")

    return render_template("get_location.html", session=session, ts=ts)

@app.route("/rate/process", methods=["POST"])
def process_rating():
    if not check_login_status():
        return redirect("/")

    query = request.form["location_query"]
    lat, lng = funcs.get_coordinates(query)

    session["rating_coords"] = (lat, lng)
    ts = get_texts(session["lang"], "rate")

    return render_template("rate.html", lat=lat, lng=lng, ts=ts, msg=None, session=session)

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
        msgs = ["Every rating counts! Your feedback helps us build a cleaner, better-connected world.", "You've just made the world a bit more bearable—one restroom at a time!", "Your input is noted!", "Got it! Other toilets nearby could use your expertise as well..."]
        session["rated"] = (True, random.choice(msgs))
        return redirect("/")
    else:
        return render_template("rate.html", msg=response[1], session=session)
    
@app.route("/explore")
def explore():
    check_cookie_status()
    ts = get_texts(session["lang"], "explore")
    toilets = funcs.get_all_toilets()
    return render_template("explore.html", toilets=toilets, ts=ts, session=session)

@app.route("/api/toilets")
def toilets_api(): # thanks GPT here :o
    start_id = request.args.get("start_id", default=0, type=int)
    limit = request.args.get("limit", default=50, type=int)
    toilets = funcs.get_toilets_chunk(start_id, limit)
    return jsonify(toilets)

@app.route("/toilet/<tid>")
def toilet(tid):
    check_cookie_status()
    info = funcs.get_toilet_details(tid)
    info["address"] = str(funcs.coords_to_address(info["latitude"], info["longitude"]))
    # {'toilet_id': 2, 'latitude': 51.5149633, 'longitude': 7.4548106, 'ratings': [{'rating_id': 1, 'cleanliness': 3, 'supplies': 3, 'privacy': 3, 'comment': '', 'user': 'czett'}]}

    ts = get_texts(session["lang"], "toilet")

    return render_template("toilet.html", toilet=info, ts=ts, session=session)

@app.route("/profile/<int:pid>")
def profile(pid):
    check_cookie_status()
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

    nots = []
    own = False
    if session.get("user"):
        if session["user"] == uname:
            own = True
            if session.get("notifications"):
                nots = session["notifications"]
            else:
                nots = []
        else:
            own = False

    ts = get_texts(session["lang"], "profile")

    return render_template("profile.html", ratings=ratings, ts=ts, session=session, name=uname, avg_lat=avg_lat, avg_lon=avg_lon, own=own, achievements=user_achievements, nots=nots)

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
    ts = get_texts(session["lang"], "leaderboard")
    return render_template("leaderboard.html", ts=ts, leaderboard=leaderboard, session=session)

@app.route("/trending")
def trending():    
    leaderboard = funcs.get_top_10_toilets()
    ts = get_texts(session["lang"], "trending")
    return render_template("trends.html", ts=ts, leaderboard=leaderboard, session=session)

@app.route("/clear-notifications")
def clear_notifications():
    if not check_login_status():
        return redirect("/")
    
    if session.get("notifications"):
        print(session["notifications"])
        session["notifications"] = []

    return redirect("/")

@app.errorhandler(Exception)
def handle_error(e):
    code = 500
    if isinstance(e, HTTPException):
        code = e.code
    return redirect(f"/error/{code}")

@app.route("/error/<code>")
def error(code):
    ts = get_texts(session["lang"], "error")
    return render_template("error.html", ts=ts, code=f"error {code} :(")
    
if __name__ == "__main__":
    app.run(debug=False, port=7000)