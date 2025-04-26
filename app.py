from flask import Flask, render_template, redirect, session, request, url_for, jsonify
import funcs, re, random, json
from werkzeug.exceptions import HTTPException
from datetime import datetime
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

        if not re.fullmatch(r"^[A-Za-z0-9_]{3,20}$", username) and not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", username):  # Prevents SQL injection and allows email login
            return render_template("logreg.html", action="login", msg="Invalid username or email!", session=session, ts=ts)

        if username and password:
            username = username.lower()
            response = funcs.login(username, password)
            if response[0] == True:
                if "@" in username:
                    username = funcs.get_username_by_email(username)
                    
                session["user"] = username
                session["logged_in"] = True
                session.permanent = True
                return redirect("/")
            else:
                return render_template("logreg.html", action="login", msg=response[1], session=session, ts=ts)
    except:
        return redirect("/")

    return "Congrats, you worked around my code :)"

@app.route("/pwreset")
def pwreset():
    check_cookie_status()
    ts = get_texts(session["lang"], "logreg")
    return render_template("logreg.html", action="pwreset", msg=None, ts=ts, session=session)

@app.route("/pwreset/process", methods=["POST"])
def process_pwreset():
    check_cookie_status()
    ts = get_texts(session["lang"], "logreg")

    try:
        email = request.form["email"]
        username = request.form["username"]

        if not re.fullmatch(r"^[A-Za-z0-9_]{3,20}$", username) and not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
            return render_template("logreg.html", action="pwreset", msg="Invalid username or email!", session=session, ts=ts)

        if not username == funcs.get_username_by_email(email):
            return render_template("logreg.html", action="pwreset", msg="Username and email don't belong to same account!", session=session, ts=ts)

        if email:
            session["username"] = username
            session["pwreset_code"] = funcs.generate_password_reset_code()
            funcs.send_password_reset_email(email, session["pwreset_code"])
            return render_template("logreg.html", action="pwreset", msg="Reset link sent via email. Make sure to quickly open in this browser.", session=session, ts=ts)
    except Exception as e:
        return redirect("/")

    return "Congrats, you worked around my code :)"

@app.route("/r/<code>")
def reset_password(code):
    check_cookie_status()
    ts = get_texts(session["lang"], "logreg")

    if not session.get("pwreset_code"):
        return render_template("logreg.html", action="pwreset", msg="Invalid reset link!", ts=ts, session=session)

    print(code, session["pwreset_code"])

    if code == session["pwreset_code"]:
        return render_template("logreg.html", action="newpw", msg=None, ts=ts, session=session)
    else:
        return render_template("logreg.html", action="pwreset", msg="Invalid reset link!", ts=ts, session=session)

@app.route("/r/process", methods=["POST"])
def process_new_password():
    check_cookie_status()
    ts = get_texts(session["lang"], "logreg")

    try:
        password = request.form["password"]
        username = session["username"]

        if not re.match("^[A-Za-z0-9_]*$", password):
            return render_template("logreg.html", action="newpw", msg="Only letters, digits and underscores allowed!", ts=ts, session=session)
        elif len(password) < 6:
            return render_template("logreg.html", action="newpw", msg="Password too short! (min. 6 characters)", ts=ts, session=session)

        response = funcs.reset_password(username, password)
        if response[0] == True:
            return render_template("logreg.html", action="login", msg="Password reset successfully! You can now login.", ts=ts, session=session)
        else:
            return render_template("logreg.html", action="newpw", msg=response[1], ts=ts, session=session)
    except Exception as e:
        return render_template("logreg.html", action="newpw", msg="An error occured. Whoopsie!", ts=ts, session=session)

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

@app.route("/register/auth")
def register_auth():
    check_cookie_status()
    ts = get_texts(session["lang"], "logreg")
    auth_code = funcs.generate_auth_code()

    if not session.get("auth_code"):
        session["auth_code"] = auth_code

    username, password, email = session["creds"]
    funcs.send_verification_email(email, auth_code)

    return render_template("auth.html", ts=ts, session=session, msg=None)

@app.route("/register/auth/check", methods=["POST"])
def process_register_auth():
    check_cookie_status()
    ts = get_texts(session["lang"], "logreg")
    auth_code = session["auth_code"]

    try:
        code = request.form["authcode"]
        if int(code) == int(auth_code):
            username, password, email = session["creds"]
            response = funcs.register(username.lower(), password, email)
            if response[0] == True:
                session["user"] = username
                session["logged_in"] = True
                session.permanent = True
                return redirect("/")
            else:
                return render_template("logreg.html", action="register", ts=ts, msg=response[1], session=session)
        else:
            return render_template("auth.html", ts=ts, session=session, msg=f"Invalid code! Try again.")
    except:
        return redirect("/explore")

    return "Congrats, you worked around my code :)"

@app.route("/register/process", methods=["POST"])
def process_register():
    check_cookie_status()
    ts = get_texts(session["lang"], "logreg")
    
    try:
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        session["creds"] = (username, password, email)

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
            if funcs.check_username_or_email_exists(username, email)[0]:
                return render_template("logreg.html", action="register", msg="Username or email already taken!", session=session, ts=ts)
            return redirect("/register/auth")
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

    if not session.get("cooldown"):
        session["cooldown"] = 0
    else:
        cooldown_time = 180
        if datetime.now().timestamp() - session["cooldown"] < cooldown_time:
            cooldown_msg = "You have to wait " + str(int(cooldown_time/60)) + " minutes between ratings! Currently you have to wait for " + str(cooldown_time - int(datetime.now().timestamp() - session["cooldown"])) + " seconds."
            return render_template("get_location.html", session=session, ts=ts, msg=cooldown_msg)

    return render_template("get_location.html", session=session, ts=ts, msg=None)

@app.route("/rate/process", methods=["POST"])
def process_rating():
    if not check_login_status():
        return redirect("/")

    query = request.form["location_query"]
    
    if profanity.contains_profanity(query) or "gustav" in query.lower():
        return redirect("/rate")
    
    lat, lng = funcs.get_coordinates(query)

    session["rating_coords"] = (lat, lng)
    ts = get_texts(session["lang"], "rate")

    return render_template("rate.html", lat=lat, lng=lng, ts=ts, msg=None, session=session)

@app.route("/rate/finish", methods=["POST"])
def finish_rating():
    if not check_login_status():
        return redirect("/")
    
    ts = get_texts(session["lang"], "rate")

    cleanliness = request.form["cleanliness"]
    supplies = request.form["supplies"]
    privacy = request.form["privacy"]
    comment = request.form["comment"]
    user = session["user"]
    uid = funcs.get_user_id_by_username(user)
    
    profanity.load_censor_words()

    if not re.match(r"^[\w!?,.;:\-()=$€£/%\s\u00C0-\u017F]*$", comment, re.UNICODE):
        return render_template("rate.html", msg="Invalid chars in comment", ts=ts, session=session)

    comment = profanity.censor(comment)
    response = funcs.create_rating(cleanliness, supplies, privacy, comment, session["rating_coords"], uid)
    
    if response[0] == True:
        msgs = ["Every rating counts! Your feedback helps us build a cleaner, better-connected world.", "You've just made the world a bit more bearable—one restroom at a time!", "Your input is noted!", "Got it! Other toilets nearby could use your expertise as well..."]
        session["rated"] = (True, random.choice(msgs))

        # clear trends and leaderboard
        if session.get("trends"): 
            session.pop("trends")
        if session.get("leaderboard"):
            session.pop("leaderboard")

        session["cooldown"] = datetime.now().timestamp()

        return redirect("/")
    else:
        ts = get_texts(session["lang"], "rate")
        return render_template("rate.html", msg=response[1], session=session, ts=ts)
    
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
def toilet_num(tid):
    # check_cookie_status()
    # info = funcs.get_toilet_details(tid)
    # info["address"] = str(funcs.coords_to_address(info["latitude"], info["longitude"]))
    # # {'toilet_id': 2, 'latitude': 51.5149633, 'longitude': 7.4548106, 'ratings': [{'rating_id': 1, 'cleanliness': 3, 'supplies': 3, 'privacy': 3, 'comment': '', 'user': 'czett'}]}

    # ts = get_texts(session["lang"], "toilet")

    # return render_template("toilet.html", toilet=info, ts=ts, session=session)

    check_cookie_status()

    if session.get("tid"):
        session.pop("tid")

    session["tid"] = tid
    return redirect("/toilet")

@app.route("/toilet") # all because of adsense bro
def toilet():
    check_cookie_status()

    if not session.get("tid"):
        return redirect("/explore")

    tid = session["tid"]
    info = funcs.get_toilet_details(tid)
    rank_icon_map = {"dev": "data_object", "supporter": "favorite", "og": "workspace_premium", "basic": "handshake"}

    if info == None:
        return redirect("/explore") # redirect to explore if toilet does not exist

    # im sorry for this geopy, i left it in for too long without even using the address :(
    # info["address"] = str(funcs.coords_to_address(info["latitude"], info["longitude"]))
    # {'toilet_id': 2, 'latitude': 51.5149633, 'longitude': 7.4548106, 'ratings': [{'rating_id': 1, 'cleanliness': 3, 'supplies': 3, 'privacy': 3, 'comment': '', 'user': 'czett'}]}

    ts = get_texts(session["lang"], "toilet")

    return render_template("toilet.html", toilet=info, ts=ts, session=session, icon_map=rank_icon_map)

@app.route("/profile/<int:pid>")
def profile(pid):
    check_cookie_status()
    pid = int(pid)

    if not session.get(f"username_{pid}"):
        uname = funcs.get_username_by_user_id(pid)
        session[f"username_{pid}"] = uname
    else:
        uname = session[f"username_{pid}"]

    if not session.get(f"user_achievements_{pid}"):
        user_achievements = funcs.get_achievements_by_user_id(pid)[1]
        session[f"user_achievements_{pid}"] = user_achievements
    else:
        user_achievements = session[f"user_achievements_{pid}"]
    
    cached_ratings_keys = [key for key in session.keys() if key.startswith("user_ratings_")]
    if len(cached_ratings_keys) >= 2:
        # Delete one user's ratings (the first one in the list) as too many ratings are cached
        for key in cached_ratings_keys:
            if key != f"user_ratings_{pid}":
                session.pop(key)
                print("Deleted cached ratings of user", key)
                break
    if not session.get(f"user_ratings_{pid}"):
        ratings = funcs.get_user_ratings(pid)
        session[f"user_ratings_{pid}"] = ratings
    else:
        ratings = session[f"user_ratings_{pid}"]

    # POSTPONED TO SAVE VERCEL RESOURCES Calculate the average latitude and longitude for all rated toilets
    # if ratings != []:
    #     avg_lat = sum(rating['latitude'] for rating in ratings) / len(ratings)
    #     avg_lon = sum(rating['longitude'] for rating in ratings) / len(ratings)
    # else:
    #     
    
    # AS OF NOW, APRIL 4TH 25, I AM REMOVING THE USER MAP DUE TO IT BEING UNNECESSARY AND CHEWING UP MY VERCEL PLAN


    #avg_lat, avg_lon = 51.1657, 10.4515 # default is Germany

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

    # return render_template("profile.html", ts=ts, pid=str(pid), session=session, avg_lat=avg_lat, avg_lon=avg_lon, own=own, nots=nots)
    return render_template("profile.html", ts=ts, pid=str(pid), session=session, own=own, nots=nots)

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
    check_cookie_status()
    if not session.get("leaderboard"):
        leaderboard = funcs.get_users_sorted_by_ratings()
        session["leaderboard"] = leaderboard

    # test

    ts = get_texts(session["lang"], "leaderboard")
    return render_template("leaderboard.html", ts=ts, session=session)

@app.route("/trending")
def trending():
    check_cookie_status()
    if not session.get("trends"):
        leaderboard = funcs.get_top_10_toilets()
        session["trends"] = leaderboard

    ts = get_texts(session["lang"], "trending")
    return render_template("trends.html", ts=ts, session=session)

@app.route("/totd")
def totd():
    check_cookie_status()
    
    result = funcs.get_toilet_of_the_day()

    return redirect(f"/toilet/{result}") if result != None else redirect("/explore")

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
    app.run(debug=True, port=7000)