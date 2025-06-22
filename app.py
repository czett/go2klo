from flask import Flask, render_template, redirect, session, request, url_for, jsonify
import funcs, re, random, json, os
from werkzeug.exceptions import HTTPException
from datetime import datetime
from better_profanity import profanity
from dotenv import load_dotenv

try:
    load_dotenv()
except:
    pass # :) great code, right?

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

rank_icon_map = {"dev": "data_object", "mod": "gavel",  "supporter": "favorite", "og": "workspace_premium", "basic": "handshake", "creator": "campaign", "recruiter": "military_tech", "gambler": "playing_cards"}

def check_login_status():
    if session.get("logged_in"):
        if session["logged_in"]:
            return True
    else:
        session["logged_in"] = False
        return False
    
    return True

def check_cookie_status():
    # cookie banner removal for now because only essential cookies are used
    session["cookies"] = True
    
    if not session.get("lang"):
        session["lang"] = "english"
    
    return True

    # old banner validation code
    if session.get("cookies"):
        if session["cookies"]:
            return True
    else:
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

@app.route("/session")
def session_out():
    return str(dict(session))

@app.route("/")
def startpoint():
    check_cookie_status()
    
    rated = (False, "") # normie case :3
    report = None # normie case :3
    if session.get("rated"):
        rated = session["rated"]
    if session.get("report"):
        report = session["report"]
        session.pop("report")

    ts = get_texts(session["lang"], "index")

    session["rated"] = (False, "")
    return render_template("index.html", session=session, rated=rated, ts=ts, report=report)

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
        username.strip()
        password = request.form["password"]
        password.strip()

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
        username = request.form["username"].lower()

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

    # print(code, session["pwreset_code"])

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

        if not re.match(r"^(?!.*--)[\x20-\x7E]+$", password):
            return render_template("logreg.html", action="newpw", msg="Password contains invalid characters or '--' sequence is not allowed", ts=ts, session=session)
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
    mail_return = funcs.send_verification_email(email, session["auth_code"])

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

            # check for referral here :3
            referral_tuple = (False, None)
            if session.get("referral"):
                referral_uid = session["referral_uid"]
                referral_tuple = (True, referral_uid)
                session.pop("referral")
                session.pop("referral_name")
                session.pop("referral_uid")
                session.modified = True

            response = funcs.register(username.lower(), password, email, referral_tuple)
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
        username = request.form["username"].lower()
        username.strip()
        password = request.form["password"]
        password.strip()
        email = request.form["email"].lower()
        email.strip()

        session["creds"] = (username, password, email)

        if not re.match("^[A-Za-z0-9_]*$", username): # only letters, digits, and underscores
            return render_template("logreg.html", action="register", msg="Only letters, digits and underscores allowed in username!", session=session, ts=ts)
        if not re.match(r"^(?!.*--)[\x20-\x7E]+$", password):
            return render_template("logreg.html", action="register", msg="Password contains invalid characters or '--' sequence is not allowed", ts=ts, session=session)
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
    
    if session.get("rating_coords") != None:
        rating_coords = session.get("rating_coords")
    else:
        rating_coords = None

    session["rating_coords"] = None

    ts = get_texts(session["lang"], "get_location")

    if not session.get("cooldown"):
        session["cooldown"] = 0
    else:
        cooldown_time = 180
        if datetime.now().timestamp() - session["cooldown"] < cooldown_time:
            cooldown_msg = "You have to wait " + str(int(cooldown_time/60)) + " minutes between ratings! Currently you have to wait for " + str(cooldown_time - int(datetime.now().timestamp() - session["cooldown"])) + " seconds."
            return render_template("get_location.html", session=session, ts=ts, msg=cooldown_msg)

    return render_template("get_location.html", session=session, ts=ts, msg=None, rating_coords=rating_coords)

@app.route("/rate/t/<tid>")
def rate_tid(tid):
    check_cookie_status()
    if not check_login_status():
        return redirect("/login")
    
    if not tid:
        return redirect("/explore")

    # check if toilet exists

    uid = funcs.get_user_id_by_username(session["user"])

    toilet = funcs.get_toilet_details(tid, uid)
    if toilet == None:
        return redirect("/explore")

    lat, lng = toilet["latitude"], toilet["longitude"]
    
    session["rating_coords"] = f"{lat}, {lng}"
    
    return redirect("/rate")

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

    # rank fetching for img upload
    uid = funcs.get_user_id_by_username(session["user"])
    rank = funcs.get_user_rank(uid) # either none or rank, no other case possible (at least i hope so)

    return render_template("rate.html", lat=lat, lng=lng, ts=ts, msg=None, session=session, rank=rank)

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

    if uid == None:
        return redirect("/logout")
    
    profanity.load_censor_words()

    if not re.match(r"^[\w!?,.;:\-()=$€£/%\s\u00C0-\u017F]*$", comment, re.UNICODE):
        return render_template("rate.html", msg="Invalid chars in comment", ts=ts, session=session)

    comment = profanity.censor(comment)

    response = funcs.create_rating(cleanliness, supplies, privacy, comment, session["rating_coords"], uid)

    if response[0] == True:
        img_file = request.files.get("img-input")
        if img_file and img_file.filename:
            funcs.upload_rating_image(response[1], img_file)  # response[1] = rating_id
    

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

    toilets = funcs.get_toilets(20)
    
    return render_template("explore.html", ts=ts, session=session, toilets=toilets)

@app.route("/explore/search", methods=["POST"])
def search_toilets():
    check_cookie_status()
    ts = get_texts(session["lang"], "explore")

    try:
        query = request.form["search-query"]
        query = query.strip()
        query = query.lower()

        if profanity.contains_profanity(query) or "gustav" in query.lower():
            return redirect("/explore")
        if not re.match(r"^[\w!?,.;:\-()=$€£/%\s\u00C0-\u017F]*$", query, re.UNICODE):
            return redirect("/explore")
        if not query:
            return redirect("/explore")
        if len(query) > 100:
            return redirect("/explore")
    except:
        return redirect("/explore")

    toilets = funcs.search_toilets(query)

    # Default to center of Europe if no toilets found :(((
    t1_coords = [50.1109, 8.6821]
    zoom = 6
    
    if len(toilets) != 0:
        t1 = toilets[0]
        t1_coords = (t1["latitude"], t1["longitude"])
        zoom = 3

    if len(toilets) > 1:
        t2 = toilets[-1]
        t2_coords = (t2["latitude"], t2["longitude"])

        distance = funcs.distance(t1_coords, t2_coords)
        zoom = funcs.get_zoom_level(distance)

        # print(round(distance, 0))

    if zoom == None:
        zoom = 6

    return render_template("explore.html", ts=ts, session=session, toilets=toilets, zoom=zoom, query=query, focus_coords=list(t1_coords))

@app.route("/api/toilets")
def toilets_api(): # thanks GPT here :o
    start_id = request.args.get("start_id", default=0, type=int)
    limit = request.args.get("limit", default=50, type=int)
    toilets = funcs.get_toilets_chunk(start_id, limit)
    return jsonify(toilets)

@app.route("/toilet/<tid>")
def toilet_num(tid):
    # update june 2025 - migrated back to this url as toilet sharing is maybe something we'll want to have for the future
    check_cookie_status()

    uid = None
    if session.get("logged_in"):
        username = session["user"]
        uid = funcs.get_user_id_by_username(username)

    info = funcs.get_toilet_details(tid, uid)

    # in case someone shares a faulty url >:(
    if info == None:
        return redirect("/explore")
    
    ts = get_texts(session["lang"], "toilet")

    return render_template("toilet.html", toilet=info, ts=ts, session=session, icon_map=rank_icon_map)

# @app.route("/toilet") # all because of adsense bro
# def toilet():
#     check_cookie_status()

#     uid = None
#     if session.get("user"):
#         user = session["user"]
#         uid = funcs.get_user_id_by_username(user)
#     else:
#         uid = None

#     info = funcs.get_toilet_details(tid, uid)

#     if info == None:
#         return redirect("/explore") # redirect to explore if toilet does not exist

#     # im sorry for this geopy, i left it in for too long without even using the address :(
#     # info["address"] = str(funcs.coords_to_address(info["latitude"], info["longitude"]))
#     # {'toilet_id': 2, 'latitude': 51.5149633, 'longitude': 7.4548106, 'ratings': [{'rating_id': 1, 'cleanliness': 3, 'supplies': 3, 'privacy': 3, 'comment': '', 'user': 'czett'}]}

#     ts = get_texts(session["lang"], "toilet")

#     return render_template("toilet.html", toilet=info, ts=ts, session=session, icon_map=rank_icon_map)

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
                # print("Deleted cached ratings of user", key)
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

    user_rank = funcs.get_user_rank(pid)

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

    if own == True:
        if user_rank == "dev" or user_rank == "mod":
            reports = []
            reports = funcs.get_all_reports()
            return render_template("profile.html", ts=ts, pid=str(pid), icon_map=rank_icon_map, rank=user_rank, session=session, own=own, nots=nots, reports=reports, user_achievements=user_achievements, uname=uname, ratings=ratings)

    # return render_template("profile.html", ts=ts, pid=str(pid), session=session, avg_lat=avg_lat, avg_lon=avg_lon, own=own, nots=nots)
    return render_template("profile.html", ts=ts, pid=str(pid), icon_map=rank_icon_map, rank=user_rank, session=session, own=own, nots=nots)

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

    ts = get_texts(session["lang"], "leaderboard")
    return render_template("leaderboard.html", ts=ts, session=session, icon_map=rank_icon_map)

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
        #   (session["notifications"])
        session["notifications"] = []

    return redirect("/")

@app.route("/claim/limited-edition-rank")
def claim_limited_edition_rank():
    if not check_login_status():
        return redirect("/")
    
    if session.get("user"):
        user = session["user"]
        uid = funcs.get_user_id_by_username(user)

        has_rank = funcs.has_user_rank(uid, "og")

        if has_rank[0] == False and has_rank[1] == "":
            rank_assign_response = funcs.assign_user_rank(uid, "og")

    return redirect("/")

@app.route("/report", methods=["POST"])
def report_process():
    if not check_login_status():
        return redirect("/")
    
    try:
        toilet_id = request.form["toilet_id"]
        report_text = request.form["report_text"]
        if not re.match(r"^[\w!?,.;:\-()=$€£/%\s\u00C0-\u017F]*$", report_text, re.UNICODE):
            return redirect("/error/400")

        session["report"] = toilet_id

        user_id = funcs.get_user_id_by_username(session["user"])
        report_response = funcs.add_report(toilet_id, report_text, user_id)

        return redirect("/")
    except:
        return redirect("/")
    
@app.route("/report/decline/<rid>")
def decline_report(rid):
    if not check_login_status():
        return redirect("/")
    
    if session.get("user"):
        user = session["user"]
        uid = funcs.get_user_id_by_username(user)

        has_rank = funcs.has_user_rank(uid, "dev")

        if has_rank[0] == True and has_rank[1] == "":
            funcs.delete_report_by_id(rid)

        has_rank = funcs.has_user_rank(uid, "mod")

        if has_rank[0] == True and has_rank[1] == "":
            funcs.delete_report_by_id(rid)

    return redirect("/myprofile")

@app.route("/report/accept/<tid>")
def accept_report(tid):
    if not check_login_status():
        return redirect("/")
    
    if session.get("user"):
        user = session["user"]
        uid = funcs.get_user_id_by_username(user)

        has_rank = funcs.has_user_rank(uid, "dev")

        if has_rank[0] == True:
            funcs.delete_toilet_by_id(int(tid))

        has_rank = funcs.has_user_rank(uid, "mod")

        if has_rank[0] == True:
            funcs.delete_toilet_by_id(int(tid))
        
    return redirect("/myprofile")

@app.route("/rl/<username>")
def referral(username):
    check_cookie_status()

    if session.get("logged_in") == True:
        return redirect("/")
    
    if not re.match("^[A-Za-z0-9_]*$", username):
        return redirect("/")
    
    uid = funcs.get_user_id_by_username(username)

    if uid:
        session["referral"] = True
        session["referral_name"] = username
        session["referral_uid"] = uid
        return redirect("/register")
        
    return redirect("/")

@app.route("/blog")
def blog():
    check_cookie_status()
    ts = get_texts(session["lang"], "blog")
    
    # search if done
    search_query = request.args.get("search_query")
    search_results = None
    if search_query:
        # print(f"Search query: {search_query}")
        articles = funcs.search_articles(search_query)
        search_results = articles

    #check for msg
    msg = request.args.get("msg")

    if session.get("newest_articles"):
        newest_articles = session["newest_articles"]
    else:
        newest_articles = funcs.get_newest_articles(12)
        session["newest_articles"] = newest_articles
    
    if session.get("hot_articles"):
        hot_articles = session["hot_articles"]
    else:
        hot_articles = funcs.get_hot_articles(3)
        session["hot_articles"] = hot_articles

    unreviewed_articles = None

    # give unreviewed articles to mods and devs
    if session.get("user"):
        user = session["user"]
        uid = funcs.get_user_id_by_username(user)

        if uid:
            rank = funcs.get_user_rank(uid)
            if funcs.compare_ranks(rank, "mod") == True:
                unreviewed_articles = funcs.get_unreviewed_articles(30)

    return render_template("blog.html", ts=ts, msg=msg, session=session, newest_articles=newest_articles, hot_articles=hot_articles, search_results=search_results, unreviewed_articles=unreviewed_articles)

@app.route("/blog/write")
def write_blog():
    check_cookie_status()

    if not check_login_status():
        return redirect("/login")
    
    ts = get_texts(session["lang"], "blog")
    return render_template("blog_write.html", ts=ts, session=session)

@app.route("/blog/submit", methods=["POST"])
def submit_blog():
    check_cookie_status()

    title = request.form["title"]
    content = request.form["content"]
    slug = request.form["slug"]
    img = request.form["img"]

    user = session["user"]
    uid = funcs.get_user_id_by_username(user)
    if uid == None:
        return redirect("/logout")
    
    response = funcs.submit_article(title, content, slug, img, uid)

    if response[0] == True:
        msg = "Article submitted successfully! It will be reviewed by our team."
    else:
        msg = "An error occurred while submitting your article: " + response[1]

    return redirect(url_for("blog", msg=msg))


@app.route("/blog/p/<slug>")
def blog_post(slug):
    check_cookie_status()

    article = funcs.get_article_by_slug(slug)

    if article == None:
        return redirect("/blog")
    if article[0] == "unpublished":
        if session.get("user"):
            user = session["user"]
            uid = funcs.get_user_id_by_username(user)

            if uid:
                rank = funcs.get_user_rank(uid)
                if funcs.compare_ranks(rank, "mod") == True:
                    pass
                else:
                    return redirect("/blog")
            else:
                return redirect("/blog")
        else:
            return redirect("/blog")

    funcs.add_article_view(slug)
    ts = get_texts(session["lang"], "blog")

    # format date
    article = article[1]
    article["created_at"] = article["created_at"].strftime("%d.%m.%Y")

    return render_template("blog_article.html", article=article, session=session, ts=ts)

@app.route("/blog/mod/<action>/<slug>")
def blog_mod_action(action, slug):
    check_cookie_status()

    if not session.get("user"):
        return redirect("/blog")
    
    user = session["user"]
    uid = funcs.get_user_id_by_username(user)
    if uid == None:
        return redirect("/logout")
    rank = funcs.get_user_rank(uid)
    if not funcs.compare_ranks(rank, "mod"):
        return redirect("/blog")
    
    if action == "approve":
        funcs.approve_article(slug)

        if session.get("newest_articles"):
            session.pop("newest_articles")
    elif action == "reject":
        funcs.reject_article(slug)

    return redirect("/blog")

@app.route("/blog/search", methods=["POST"])
def blog_search():
    check_cookie_status()

    query = request.form["query"]

    # articles = funcs.search_articles(query)
    # session["blog_search_results"] = articles
    # return redirect("/blog")

    return redirect(url_for("blog", search_query=query))

# quick redirection urls

@app.route("/p/<identifier>")
def profile_referrer(identifier):
    check_cookie_status()

    if not re.match("^[A-Za-z0-9_]*$", identifier):
        return redirect("/")

    return redirect(f"/profile/{identifier}")

@app.route("/t/<tid>")
def toilet_referrer(tid):
    check_cookie_status()

    if not re.match("^[0-9]*$", tid):
        return redirect("/explore")

    return redirect(f"/toilet/{tid}")

@app.route("/l/<page>")
def logout_and_redirect(page):
    check_cookie_status()
    session.pop()

    return redirect(f"/{page}")

@app.route("/legal")
def legal():
    check_cookie_status()
    ts = get_texts(session["lang"], "index")

    return render_template("legal.html", ts=ts, session=session)

@app.route("/api/like-rating/<tid>", methods=["POST"])
def toggle_like_rating(tid):
    if not check_login_status():
        return jsonify({"error": "You must be logged in to like a rating."}), 401
    
    user = session["user"]
    uid = funcs.get_user_id_by_username(user)
    
    if uid is None:
        return jsonify({"error": "User not found."}), 404

    response = funcs.toggle_like_rating(uid, tid)

    if response[0]:
        return jsonify({"success": True, "message": response[1]})
    else:
        return jsonify({"error": response[1]}), 400

@app.route("/rfr")
def rfr():
    check_cookie_status()
    ts = get_texts(session["lang"], "rfr")

    return render_template("rfr.html", ts=ts, session=session)

@app.route("/gambling")
def gambling():
    check_cookie_status()
    ts = get_texts(session["lang"], "index")

    msg = None
    if not check_login_status():
        msg = "You have to be logged in to gamble"
        return render_template("gambling.html", ts=ts, msg=msg, session=session)

    if session.get("msg"):
        msg = session["msg"]
        session.pop("msg")

    uid = funcs.get_user_id_by_username(session["user"])
    rank = funcs.get_user_rank(uid)

    if rank == "gambler" and msg == None:
        msg = "You are already a gambling master. You can't win more :("

    return render_template("gambling.html", ts=ts, msg=msg, session=session)

@app.route("/gambling/<result>")
def gambling_result(result):
    check_cookie_status()
    ts = get_texts(session["lang"], "index")

    if not check_login_status():
        return redirect("/error/404")
    if result != "w" and result != "l":
        return redirect("/error/404")

    msg = "You lost! Too bad."
    
    if result == "w":
        uid = funcs.get_user_id_by_username(session["user"])
        rank = funcs.get_user_rank(uid)

        if funcs.compare_ranks(rank, "gambler") == True:
            msg = f"Gambler rank was not assigned because you rank '{rank}' is worth more. If you want to overwrite anyways, DM me on Instagram @go2klo :)"
            session["msg"] = msg
            return redirect("/gambling")

        msg = "You won! Check out your new rank (you might need to log out and in again for the changes to take effect)"
        funcs.assign_user_rank(uid, "gambler")
    
    session["msg"] = msg

    return redirect("/gambling")

# @app.errorhandler(Exception)
# def handle_error(e):
#     code = 500
#     if isinstance(e, HTTPException):
#         code = e.code
#     return redirect(f"/error/{code}")

# @app.route("/error/<code>")
# def error(code):
#     ts = get_texts(session["lang"], "error")
#     return render_template("error.html", ts=ts, code=f"error {code} :(")

if __name__ == "__main__":
    app.run(debug=True, port=7000)