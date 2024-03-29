from flask import Flask, render_template,redirect,request,current_app,session
from fun import get_code_sets,code_lang,answer_fix,mode_b_keys,ans_feeback,password_hash,get_folders,get_settings,get_streak,get_sets,hash_value,gen_user_token,add_streak,streak,login,check_image,gen_id,make_dict_group,user_data_group,username,recommend,rule_id,gen_code,leaderboard_dict,similarity,userinfo,make_dict,mod,play_dict,smart,last_7,week_add,stats_dict,update,make_dict_folder,subject,make_dict_rules
from better_profanity import profanity
import emoji
import os,random,re
from datetime import timedelta
from datetime import datetime
from flask_compress import Compress
from dotenv import load_dotenv
from pymongo import MongoClient
from flask import Flask, redirect, request,jsonify
from flask.templating import render_template
import stripe
from stripe.error import StripeError

load_dotenv(override=True, interpolate=False)
client = MongoClient(os.getenv('mongo_url'))

db = client["Booogle_Revise"]
global_data_db = db["Global_Data"]
user_data_db = db["User_Data"]
stripe.api_key = os.environ['PAY_API']
endpoint_secret = os.environ['WEB_HOOK']

app = Flask(__name__)
app.secret_key = os.getenv('secret_key')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365)
compress = Compress(app)

@app.route("/")
def home():
    if login() == False:
        return render_template("login/login.html")
    users_groups = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["groups"]
    added_groups = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["added_groups"]
    code_sets = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["code"]
    print(added_groups)
    for i in added_groups:
        owners_username = i[0]
        group = i[1]
        group_data = user_data_db.find_one({"username":owners_username,"type":"user_data"})["data"]["groups"][group]
        users_groups[group] = group_data
    streak()
    if session.get("feedback"):
        feedback = session.get("feedback")
        session["notifications"] = [{"title":"Feedback","body":f"You Have {feedback} possible improvements to this set","type":"warning","icon":"ph-warning-circle"}]
        session.pop("feedback")
    if session.get("notifications"):
        notifications = session.get("notifications")
        session.pop("notifications")
    else:
        notifications = []
    return render_template("/home/home.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),sets=get_sets(),is_new=new,notifications=notifications,folders=get_folders(),groups=users_groups,code_sets=code_sets)

@app.route("/signup",methods=["POST","GET"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = password_hash(request.form["password"],os.getenv("salt"))
        pattern = re.compile('^[a-zA-Z0-9]+$')
        usernames = global_data_db.find_one({"name":"usernames"})
        if username not in usernames["data"] and len(username) < 16 and len(username) > 4 and bool(pattern.match(username)) and request.form["password"] == request.form["repeat_password"] and len(request.form["password"]) >= 6 and len(request.form["password"]) <= 30:
            user_data = {"username":username,"type":"user_data","data":{
                "streak":{"streak":0,"time":str(datetime.now())},
                "sets":{},
                "level":"",
                "groups":{},
                "rules":{},
                "code":{},
                "added_groups":[],
                "folders":{},
                "settings":{"interface":{"theme":"green","cards":"straight"},"accessibility":{"fontSize":"normal","font":"roboto"}},
                "password":password,
                "profile_image":"blue"
            }}
            user_data_db.insert_one(user_data)
            user_token = gen_user_token()
            session["token"] = user_token
            query = {"name":"B-KEYS"}
            update = {"$set":{f"data.{hash_value(user_token)}":username}}
            global_data_db.update_one(query, update)
            query = {"name":"usernames"}
            update = {"$push":{"data":username}}
            global_data_db.update_one(query, update)
            return redirect("/")
        else:
            if username in usernames["data"]:
                error = "Username Already Exists"
            elif len(username) > 16 or len(username) < 4:
                error = "Username Too Long Or Too Short"
            elif bool(pattern.match(username)) == False:
                error = "Username Contains Special Characters"
            elif request.form["password"] != request.form["repeat_password"]:
                error = "Passwords Do Not Match"
            elif len(request.form["password"]) < 6 or len(request.form["password"]) > 30:
                error = "Password Too Long Or Too Short"
            else:
                error = "Unknown Error"
        role = request.form["role"]
    else:
        error = False
    return render_template("login/signup.html",error=error)

@app.route("/login",methods=["POST","GET"])
def user_login():
    if request.method == "POST":
        username = request.form["username"]
        password = password_hash(request.form["password"],os.getenv("salt"))
        usernames = global_data_db.find_one({"name":"usernames"})
        if username in usernames["data"]:
            user_data = user_data_db.find_one({"username":username,"type":"user_data"})
            if password == user_data["data"]["password"]:
                user_token = gen_user_token()
                session["token"] = user_token
                query = {"name":"B-KEYS"}
                update = {"$set":{f"data.{hash_value(user_token)}":username}}
                global_data_db.update_one(query, update)
                return redirect("/")
            else:
                error = "Incorrect Password"
        else:
            error = "Username Does Not Exist"
    else:
        error = False
    return render_template("login/login_account.html",error=error)

@app.route("/mobile")
def mobile():
    if login() == False:
        return render_template("login_mobile.html")
    else:
        if session.get("notifications"):
            notifications = session.get("notifications")
            session.pop("notifications")
        else:
            notifications = []
        users_groups = make_dict(db[username()]["groups"])
        for i in db[username()]["added_groups"]:
            owners_username = i[0]
            group = i[1]
            group_data = make_dict(db[owners_username]["groups"])[group]
            users_groups[group] = group_data
        return render_template("home.html",groups=users_groups,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),sets=get_sets(),is_new=False,notifications=notifications,folders=make_dict_folder(db[username()]["folders"]))

@app.route("/share/@<username>/<set>")
def share(username,set):
    settings = user_data_db.find_one({"username":username,"type":"user_data"})["data"]["sets"][set]["settings"]
    title = set
    desc = settings["desc"]
    user = username
    notifications = []
    flash_link = f"/flashcards/@{user}/{set}"
    quest_link = f"/questions/@{user}/{set}"
    fill_link = f"/fill/@{user}/{set}"
    user_settings = {"interface":{"theme":"green","cards":"straight"},"accessibility":{"fontSize":"normal","font":"roboto"}}
    return render_template("share.html",fill_link=fill_link,quest_link=quest_link,flash_link=flash_link,settings=user_settings,title=title,desc=desc,user=user,notifications=notifications,name="Guest",boosting=False,profile_pic="https://booogle-revise-2.goodvessel92551.repl.co/static/logo.png")

@app.route("/community")
def community():
    if login() == False:
        notifications = []
        users_name = "Guest"
        settings = {"interface":{"theme":"green","cards":"straight"},"accessibility":{"fontSize":"normal","font":"roboto"}}
        boosting = [False,"/static/logo.png"]
        streak = 0
        
    else:
        if session.get("notifications"):
            notifications = session.get("notifications")
            session.pop("notifications")
        else:
            notifications = []
        users_name = username()
        settings = get_settings()
        boosting = userinfo(username())
        streak = get_streak()
    sets = global_data_db.find_one({"name":"sets"})["data"]
    code_sets = global_data_db.find_one({"name":"code_sets"})["data"]
    view_sets = {}
    code_sets_view = {}
    share_links = []
    for i, (name_key, set_name) in enumerate(sets):
        name = user_data_db.find_one({"username":name_key,"type":"user_data"})
        share_links.append("/share/@"+name_key+"/"+set_name)
        set_data = name["data"]["sets"][set_name]
        view_sets[i] = set_data
    
    for i, (name_key, set_name) in enumerate(code_sets):
        name = user_data_db.find_one({"username":name_key,"type":"user_data"})
        set_data = name["data"]["code"][set_name]
        code_sets_view[i] = set_data
    return render_template("home/community.html",code_sets=code_sets_view,streak=streak,share_links=share_links,name=users_name,settings=settings,boosting=boosting,sets=make_dict(view_sets),notifications=notifications)

@app.route("/recommended")
def recommended():
    if login() == False:
        return render_template("login/login.html")
    recommended = recommend(user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["sets"])
    recommended_sets = {}
    notifications = []
    for i in range(len(recommended)):
        recommended_sets[i] = db[recommended[i][0]]["sets"][recommended[i][1]]
        recommended_sets[i]["settings"]["name"] = recommended[i][1]
        recommended_sets[i]["settings"]["subject"] = db[recommended[i][0]]["sets"][recommended[i][1]]["settings"]["subject"]
    return render_template("recommended.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications,recommended_sets=make_dict(recommended_sets))

@app.route("/community/update")
def community_update():
    if login() == False:
        return render_template("login/login.html")
    sets = list(db["sets"])
    for i in range(len(sets)):
        db[sets[i][0]]["sets"][sets[i][1]]["settings"]["subject"] = subject(sets[i][1])
    return redirect("/community")

@app.route("/publish/<name>")
def publish(name):
    if login() == False:
        return render_template("login/login.html")
    level = userinfo(username())[0]
    amount = 0
    sets_list = global_data_db.find_one({"name":"sets"})["data"]
    for i in sets_list:
        if username() in i:
            amount += 1
    if ((level == False) and (amount >= 2)) or ((level == "premium") and (amount >= 5)) or ((level == "pro") and (amount >= 10)) or ((level == "elite") and (amount >= 30)):
        session["notifications"] = [{"title":"Failed","body":"You Have Reached The Max Amount Of Sets You Can Publish","type":"warning","icon":"ph-warning-circle"}]
        return redirect("/")
    set = get_sets()[name]
    for i in range(1,len(set)):
        quest = set[f"Q{i}"]["question"]
        if mod(quest) == "1" or profanity.contains_profanity(quest):
            session["notifications"] = [{"title":"Failed","body":"You Can't Publish This Set, Due To It Contains Profanity Or Rude Text. (Question:"+str(i)+")","type":"wanning","icon":"ph-warning-circle"}]
            return redirect("/")
        for j in set[f"Q{i}"]["answers"]:
            ans = set[f"Q{i}"]["answers"][j]
            if mod(ans) == "1" or profanity.contains_profanity(ans):
                session["notifications"] = [{"title":"Failed","body":"You Can't Publish This Set, Due To It Contains Profanity Or Rude Text. (Question:"+str(i)+")","type":"wanning","icon":"ph-warning-circle"}]
                return redirect("/")
    query = {"name":"sets"}
    update = {"$push": {"data": [username(),name]}}
    global_data_db.update_one(query, update)
    session["notifications"] = [{"title":"Success","body":f"You Have Published: {set['settings']['name']}","type":"success","icon":"ph-check-circle"}]
    return redirect("/community")

@app.route("/download/@<user_name>/<name>")
def download(user_name,name):
    if login() == False:
        return render_template("login/login.html")
    user_data = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]
    user_sets = user_data["sets"]
    user_folders = user_data["folders"]
    set_id = gen_id()
    user_sets[set_id] = user_data_db.find_one({"username":user_name,"type":"user_data"})["data"]["sets"][name]
    user_sets[set_id]["settings"]["folder"] = False
    query = {"username":username(),"type":"user_data"}
    update = {"$set":{"data.folders":user_folders}}
    user_data_db.update_one(query, update)
    query = {"username":username(),"type":"user_data"}
    update = {"$set":{"data.sets":user_sets}}
    user_data_db.update_one(query, update)
    return redirect("/")

@app.route("/delete/@<user_name>/<name>")
def delete2(user_name,name):
    if login() == False:
        return render_template("login/login.html")
    sets = global_data_db.find_one({"name":"sets"})["data"]
    if username() == user_name or userinfo(username())[0] == "admin":
        for i in sets:
            if user_name in i and name in i:
                sets.remove(i)
        query = {"name":"sets"}
        update = {"$set": {"data": sets}}
        global_data_db.update_one(query, update)
    else:
        session["notifications"] = [{"title":"Failed","body":"You Can Not Delete This Set.","type":"warning","icon":"ph-warning-circle"}]
        return redirect("/community")
    session["notifications"] = [{"title":"Success","body":f"You Deleted This From The Community","type":"success","icon":"ph-check-circle"}]
    return redirect("/")

@app.route("/flashcards/@<username>/<name>")
def flashcards2(username,name):
    notifications = []
    settings = {"interface":{"theme":"green","cards":"straight"},"accessibility":{"fontSize":"normal","font":"roboto"}}
    return render_template("tools/cards.html",streak=0,title=name,settings=settings,name="Guest",boosting=False,profile_pic="https://booogle-revise-2.goodvessel92551.repl.co/static/logo.png",sets=user_data_db.find_one({"username":username,"type":"user_data"})["data"]["sets"][name],notifications=notifications)

@app.route("/fill/@<username>/<name>")
def fills(username,name):
    notifications = []
    settings = {"interface":{"theme":"green","cards":"straight"},"accessibility":{"fontSize":"normal","font":"roboto"}}
    return render_template("tools/fill.html",streak=0,title=name,name="Guest",settings=settings,boosting=False,profile_pic="https://booogle-revise-2.goodvessel92551.repl.co/static/logo.png",set=user_data_db.find_one({"username":username,"type":"user_data"})["data"]["sets"][name],notifications=notifications)

@app.route("/questions/@<username>/<name>",methods=["POST","GET"])
def questions(username,name):
    notifications = []
    settings = {"interface":{"theme":"green","cards":"straight"},"accessibility":{"fontSize":"normal","font":"roboto"}}
    set = user_data_db.find_one({"username":username,"type":"user_data"})["data"]["sets"][name]
    order = []
    for i in range(1,len(set)):
        order.append("Q"+str(i))
    random.shuffle(order)
    session["next"] = "False"
    session["current"] = {"current":0,"order":order}
    ans = []
    if session.get("current")["current"] == len(session.get("current")["order"]):
        return render_template("tools/finish.html",settings=settings,name="Guest",boosting=False,profile_pic="https://booogle-revise-2.goodvessel92551.repl.co/static/logo.png",notifications=notifications)
    current = session.get("current")
    question = set[current["order"][current["current"]]]["question"]
    amount_needed = 3-len(set[current["order"][session["current"]["current"]]]["answers"])
    ans.append(set[current["order"][session["current"]["current"]]]["answers"]["ans1"])
    temp = list(current["order"])
    temp.remove(current["order"][current["current"]])
    try:
        type = set[current["order"][current["current"]]]["type"]
    except:
        for i in range(amount_needed):
            quest = random.choice(temp)
            temp.remove(quest)
            ans.append(set[quest]["answers"][random.choice(list(set[quest]["answers"].keys()))])
        random.shuffle(ans)
    else:
        ans = []
        for i in temp:
            if set[i]["type"] == type:
                temp.remove(i)
                ans.append(set[i]["answers"]["ans1"])
        if len(ans) >= 3:
            random.shuffle(ans)
            ans = ans[:2]
            ans.append(set[current["order"][session["current"]["current"]]]["answers"]["ans1"])
        else:
            ans.append(set[current["order"][session["current"]["current"]]]["answers"]["ans1"])
        while len(ans) < 3:
            quest = random.choice(temp)
            temp.remove(quest)
            ans.append(set[quest]["answers"][random.choice(list(set[quest]["answers"].keys()))])
        random.shuffle(ans)
    if session.get("stats"):
        session.pop("stats")
    session["stats"] = {}
    return render_template("tools/question.html",mode="community",streak=0,title=name,settings=settings,name="Guest",boosting=False,profile_pic="https://booogle-revise-2.goodvessel92551.repl.co/static/logo.png",sets=user_data_db.find_one({"username":username,"type":"user_data"})["data"]["sets"][name],ans=ans,question=question,notifications=notifications,owner=username,total_quests=len(current["order"]),set=name,quest_num = current["order"][current["current"]])

@app.route("/new/folder",methods=["POST","GET"])
def new_folder():
    if login() == False:
        return render_template("login/login.html")
    notifications = []
    if request.method == "POST":
        title = emoji.demojize(request.form["title"]).strip()
        desc = request.form["desc"]
        cover = request.form["cover"]
        if title in list(user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["folders"]):
            session["notifications"] = [{"title":"Failed","body":"You already have a folder with that name","type":"warning","icon":"ph-warning-circle"}]
            return redirect("/")
        else:
            new_folder = {
                "name":title,
                "desc":desc,
                "background":cover,
                "sets":[],
                "code":[]
            }
            query = {"username":username(),"type":"user_data"}
            update = {"$set":{"data.folders."+title:new_folder}}
            user_data_db.update_one(query, update)
        return redirect("/")
    return render_template("folders/new_folder.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/folder/<folder>",methods=["POST","GET"])
def folder(folder):
    if login() == False:
        return render_template("login/login.html")
    notifications = []
    sets = {}
    code_sets_folder = {}
    user_sets = get_sets()
    code_sets = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["code"]
    names = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["folders"][folder]["sets"]
    code_names = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["folders"][folder]["code"]
    for i in names:
        sets[i] = user_sets[i]
    for i in code_names:
        code_sets_folder[i] = code_sets[i]
    return render_template("folders/folder.html",code=code_sets_folder,sets=sets,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications,title=user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["folders"][folder]["name"])

@app.route("/edit/folder/<folder>",methods=["POST","GET"])
def edit_folder(folder):
    if login() == False:
        return render_template("login/login.html")
    notifications = []
    sets = {}
    if request.method == "POST":
        old_folder = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["folders"][folder]
        query = {"username":username(),"type":"user_data"}
        update = {"$unset":{"data.folders."+folder:""}}
        user_data_db.update_one(query, update)
        title = emoji.demojize(request.form["title"]).strip()
        desc = request.form["desc"]
        cover = request.form["cover"]
        new_folder = {
            "name":title,
            "desc":desc,
            "background":cover,
            "sets":old_folder["sets"]
        }
        query = {"username":username(),"type":"user_data"}
        update = {"$set":{"data.folders."+title:new_folder}}
        user_data_db.update_one(query, update)
        return redirect("/folder/"+title)
    return render_template("folders/edit_folder.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications,folder=user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["folders"][folder])

@app.route("/remove/folder/<folder>")
def remove_folder(folder):
    if login() == False:
        return render_template("login/login.html")
    for i in user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["folders"][folder]["sets"]:
        query = {"username":username(),"type":"user_data"}
        update = {"$set":{"data.sets."+i+".settings.folder":False}}
        user_data_db.update_one(query, update)
    query = {"username":username(),"type":"user_data"}
    update = {"$unset":{"data.folders."+folder:""}}
    user_data_db.update_one(query, update)
    return redirect("/")

@app.route("/remove/folder/<folder>/<name>")
def remove_folder_sey(folder,name):
    if login() == False:
        return render_template("login/login.html")
    if name in list(user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["folders"][folder]["code"]):
        query = {"username":username(),"type":"user_data"}
        sets = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["folders"][folder]["code"]
        print(sets)
        sets.remove(name)
        update = {"$set":{"data.folders."+folder+".code":sets}}
        user_data_db.update_one(query, update)
        update = {"$set":{"data.code."+name+".folder":False}}
        user_data_db.update_one(query, update)
        return redirect("/folder/"+folder)
    else:
        query = {"username":username(),"type":"user_data"}
        sets = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["folders"][folder]["sets"]
        sets.remove(name)
        update = {"$set":{"data.folders."+folder+".sets":sets}}
        user_data_db.update_one(query, update)
        update = {"$set":{"data.sets."+name+".settings.folder":False}}
        user_data_db.update_one(query, update)
    return redirect("/folder/"+folder)
    
@app.route("/add/folder/<folder>/<name>")
def add_folder_set(folder,name):
    if login() == False:
        return render_template("login/login.html")
    folders = get_folders()
    if name in list(folders[folder]["sets"]) and name in list(folders[folder]["code"]):
        return "Error"
    elif name in list(user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["code"].keys()):
        query = {"username":username(),"type":"user_data"}
        update = {"$push":{"data.folders."+folder+".code":name}}
        user_data_db.update_one(query, update)
        update = {"$set":{"data.code."+name+".folder":True}}
        user_data_db.update_one(query, update)
        return redirect("/folder/"+folder)
    else:
        query = {"username":username(),"type":"user_data"}
        update = {"$push":{"data.folders."+folder+".sets":name}}
        user_data_db.update_one(query, update)
        update = {"$set":{"data.sets."+name+".settings.folder":True}}
        user_data_db.update_one(query, update)
        return redirect("/folder/"+folder)

@app.route("/new",methods=["POST","GET"])
def new():
    if login() == False:
        return render_template("login/login.html")
    notifications = []
    level = userinfo(username())[0]
    len_sets = len(get_sets())
    if ((level == False) and (len_sets > 10)) or ((level == "premium") and (len_sets > 20)) or ((level == "pro") and (len_sets > 35)) or ((level == "elite") and (len_sets > 100)):
        session["notifications"] = [{"title":"Failed","body":"You Have Reached The Max Amount Of Sets","type":"warning","icon":"ph-warning-circle"}]
        return redirect("/")
    if request.method == "POST":
        premium = ["pro","art","bike","elite","car","castle","code","hill","map","flask"]
        pro = ["elite","car","castle","code","hill","map","flask"]
        elite = ["boost","premium","pro","art","bike","elite","car","castle","code","hill","map","flask"]
        title = emoji.demojize(request.form["title"]).strip()
        desc = request.form["desc"]
        cover = request.form["cover"]
        set_id = gen_id()
        if level == "boost" or level == False:
            if cover in elite:
                cover = "maths"
        elif level == "premium":
            if cover in premium:
                cover = "maths"
        elif level == "pro":
            if cover in pro:
                cover = "maths"
        if len(title) > 80 or len(title) == 0 or len(desc) > 150 or len(desc) == 0:
            session["new_set"] = {"title":title,"desc":desc,"background":cover}
            return redirect("/new")
        if title in get_sets().keys():
            session["notifications"] = [{"title":"Failed","body":"This Set With This Name Already Exists","type":"warning","icon":"ph-warning-circle"}]
            return redirect("/")
        else:
            new_set = {
                "settings":{
                    "name":title,
                    "desc":desc,
                    "public":False,
                    "background":cover,
                    "user":username(),
                    "level":userinfo(username())[0],
                    "subject":subject(emoji.demojize(request.form["title"])),
                    "folder":False,
                    "id":set_id
                }
            }
            session["feedback"]  = 0
            user_data_db.update_one({"username":username(),"type":"user_data"},{"$set":{"data.sets."+set_id:new_set}})
            session["current_set"] = set_id
            button_type = request.form["button"]
            if button_type == "photo":
                return redirect("/photo/new/question")
            return redirect("/new/question")
    else:
        if session.get("new_set"):
            title = session.get("new_set")["title"]
            desc = session.get("new_set")["desc"]
            background = session.get("new_set")["background"]
            session.pop("new_set")
        else:
            title = ""
            desc = ""
            background = "animals"
        return render_template("sets/new.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),title=title,desc=desc,background=background,notifications=notifications)

@app.route("/new/<title>/<desc>")
def new_title(title,desc):
    if login() == False:
        return render_template("login/login.html")
    session["new_set"] = {"title":title,"desc":desc,"background":""}
    return redirect("/new")

@app.route("/new/question",methods=["POST","GET"])
def new_question():
    if login() == False:
        return render_template("login/login.html")
    notifications = []
    if request.method == "POST":
        level = userinfo(username())[0]
        quest = request.form["quest"]
        ans = request.form["ans1"]
        image_url = request.form["image_url"]
        pattern = re.compile(r'\.(jpg|jpeg|png|gif|bmp|svg|tiff)$', re.IGNORECASE)
        type = smart(ans)
        quest_mod = mod(quest)
        quest_feedback = ans_feeback(quest)
        quest_num =str(len(get_sets()[session.get("current_set")]))
        new_quest = {"status":mod(quest),"question":quest,"answers":{"ans1":ans},"type":type,"answer_feedback":ans_feeback(ans)}
        if quest_mod == "1" or quest_feedback == "Bad":
            session["feedback"] += 1
        if bool(pattern.search(image_url)):
            image_data = check_image(image_url)
            if "rating_label" in image_data:
                if image_data["rating_label"] != "adult":
                    new_quest["image"] = {"url":image_url,"rating":image_data["rating_label"]}
        user_data_db.update_one({"username":username(),"type":"user_data"},{"$set":{"data.sets."+session.get("current_set")+".Q"+quest_num:new_quest}})
        len_quests = len(get_sets()[session.get("current_set")])
        if ((level == False) and (len_quests >= 15)) or ((level == "premium") and (len_quests >= 20)) or ((level == "pro") and (len_quests >= 25)) or ((level == "elite") and (len_quests >= 50)):
            session["notifications"] = [{"title":"Failed","body":"You Have Reached The Max Amount Of Questions","type":"warning","icon":"ph-warning-circle"}]
            return redirect("/")
        if request.form["button"] == "finish":
            session.pop("current_set")
            return redirect("/")
        elif request.form["button"] == "next_photo":
            return redirect("/photo/new/question")
    rude = False
    length = False
    quest = ""
    ans = ""
    if session.get("quest"):
        quests = session.get("quest")
        quest = quests["quest"]
        ans = quests["ans"]
        session.pop("quest")
    elif session.get("quest_rude"):
        rude = True
        quest = session.get("quest_rude")
        session.pop("quest_rude")
    elif session.get("quest_len"):
        length = True
        quest = session.get("quest_len")
        session.pop("quest_len")
    return render_template("sets/new_question.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),quest=quest,ans=ans,rude=rude,len=length,notifications=notifications)

@app.route("/edit/<name>",methods=["POST","GET"])
def edit(name):
    if login() == False:
        return render_template("login/login.html")
    notifications = []
    if request.method == "POST":
        title = emoji.demojize(request.form["title"]).strip()
        desc = request.form["desc"]
        cover = request.form["cover"]
        old_set = get_sets()[name]
        query = {"username":username(),"type":"user_data"}
        update = {"$unset":{"data.sets."+name:""}}
        user_data_db.update_one(query, update)
        if len(title) > 80 or len(title) == 0 or len(desc) > 150 or len(desc) == 0:
            session["new_set"] = {"title":title,"desc":desc,"background":cover}
            return redirect("/new")
        if title in get_sets().keys():
            session["notifications"] = [{"title":"Failed","body":"This Set With This Name Already Exists","type":"warning","icon":"ph-warning-circle"}]
            return redirect("/")
        else:
            if old_set["settings"]["user"] != username():
                level = old_set["settings"]["level"]
            else:
                level = userinfo(username())[0]
            new_set = {
                "settings":{
                    "name":title,
                    "desc":desc,
                    "public":False,
                    "background":cover,
                    "user":old_set["settings"]["user"],
                    "level":level,
                    "subject":subject(emoji.demojize(request.form["title"])),
                    "folder":old_set["settings"]["folder"]
                }
            }
            user_data_db.update_one({"username":username(),"type":"user_data"},{"$set":{"data.sets."+name:new_set}})
        for i in range(1,len(list(request.form)[3:])):
            if (i >= 15 and (level == False or level == "boost")) or (i >= 20 and level == "premium") or (i >= 25 and level == "pro") or (i >= 50 and level == "elite"):
                session["notifications"] = [{"title":"Failed","body":"Your Have Reached The Max Amount Of Questions","type":"warning","icon":"ph-warning-circle"}]
                return redirect("/")
            else:
                try:
                    quest = request.form[f"Q{i}"]
                except:
                    break
                else:
                    query = {"username":username(),"type":"user_data"}
                    question = {}
                    quest_profanity = profanity.contains_profanity(quest)
                    question = {"status":mod(quest),"question":quest,"answers":{"ans1":request.form[f"A{i}"]},"type":smart(request.form[f"A{i}"]),"answer_feedback":ans_feeback(request.form[f"A{i}"])}
                    image_url = request.form[f"img{i}"]
                    pattern = re.compile(r'\.(jpg|jpeg|png|gif|bmp|svg|tiff)$', re.IGNORECASE)
                    if bool(pattern.search(image_url)):
                        image_data = check_image(image_url)
                        if "rating_label" in image_data:
                            if image_data["rating_label"] != "adult":
                                question["image"] = {"url":image_url,"rating":image_data["rating_label"]}   
                    if mod(quest) == "1" or quest_profanity: 
                        pass
                    else:
                        user_data_db.update_one(query, {"$set":{"data.sets."+name+".Q"+str(i):question}})
        session["notifications"] = [{"title":"Success","body":f"You Have Edited: {title}","type":"success","icon":"ph-check-circle"}]
        return redirect("/")
    return render_template("sets/edit.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),sets=get_sets()[name],notifications=notifications)


@app.route("/robots.txt", methods=["GET"])
def robots():
    return current_app.send_static_file("robots.txt")

@app.route("/community/robots.txt", methods=["GET"])
def community_robots():
    return current_app.send_static_file("robots.txt")

@app.route("/offline")
def offline():
    return render_template("offline.html")

@app.route("/offline/flashcards")
def offline_cards():
    return "Offline"

@app.route("/flashcards/<name>")
def flashcards(name):
    if login() == False:
        return render_template("login/login.html")
    notifications = []
    add_streak()
    return render_template("tools/cards.html",title=name,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),sets=get_sets()[name],notifications=notifications)

@app.route("/questions/<name>",methods=["POST","GET"])
def question(name):
    if login() == False:
        return render_template("login/login.html")
    notifications = []
    set = get_sets()[name]
    if len(set) < 4:
        session["notifications"] = [{"title":"Failed","body":"You Need More Questions","type":"warning","icon":"ph-warning-circle"}]
        return redirect("/")
    if session.get("stats"):
        session.pop("stats")
    session["stats"] = {}
    order = []
    for i in range(1,len(set)):
        order.append("Q"+str(i))
    random.shuffle(order)
    session["next"] = "False"
    session["current"] = {"current":0,"order":order}
    ans = []
    if session.get("current")["current"] == len(session.get("current")["order"]):
        return render_template("tools/finish.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications,stats=session["stats"])
    current = session.get("current")
    question = set[current["order"][current["current"]]]["question"]
    amount_needed = 3-len(set[current["order"][session["current"]["current"]]]["answers"])
    ans.append(set[current["order"][session["current"]["current"]]]["answers"]["ans1"])
    temp = list(current["order"])
    temp.remove(current["order"][current["current"]])
    try:
        type = set[current["order"][current["current"]]]["type"]
    except:
        for i in range(amount_needed):
            quest = random.choice(temp)
            temp.remove(quest)
            ans.append(set[quest]["answers"][random.choice(list(set[quest]["answers"].keys()))])
        random.shuffle(ans)
    else:
        ans = []
        for i in temp:
            if set[i]["type"] == type:
                temp.remove(i)
                ans.append(set[i]["answers"]["ans1"])
        if len(ans) >= 3:
            random.shuffle(ans)
            ans = ans[:2]
            ans.append(set[current["order"][session["current"]["current"]]]["answers"]["ans1"])
        else:
            ans.append(set[current["order"][session["current"]["current"]]]["answers"]["ans1"])
        while len(ans) < 3:
            quest = random.choice(temp)
            temp.remove(quest)
            ans.append(set[quest]["answers"][random.choice(list(set[quest]["answers"].keys()))])
        random.shuffle(ans)
    return render_template("tools/question.html",mode="question",title=name,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),sets=get_sets()[name],ans=ans,question=question,notifications=notifications,quest_num = current["order"][current["current"]],set=name,total_quests=len(current["order"]),owner=username())

@app.route("/api/questions",methods=["POST","GET"])
def api_quest_ans():
    correct = False
    data = request.get_json()
    owner = data["user"]
    current = session.get("current")
    set = user_data_db.find_one({"username":owner,"type":"user_data"})["data"]["sets"][data["set"]]
    current_ans = set[data["question"]]["answers"]["ans1"]
    current["current"] += 1
    session["current"] = current
    if data["answer"] == current_ans:
        session["stats"][str(current["current"])] = {"quest":set[data["question"]]["question"],"correct":True}
        correct = True
    else:
        session["stats"][str(current["current"])] = {"quest":set[data["question"]]["question"],"correct":False}
    if session.get("current")["current"] == len(session.get("current")["order"]):
        add_streak()
        return {"done":True,"answer":current_ans,"correct":correct}
    quest_num = current["order"][current["current"]]
    next_quest = set[quest_num]

    ans = []
    temp = list(current["order"])
    temp.remove(current["order"][current["current"]])
    ans.append(set[current["order"][session["current"]["current"]]]["answers"]["ans1"])
    try:
        type = set[current["order"][current["current"]]]["type"]
    except:
        pass
    else:
        ans = []
        for i in temp:
            if set[i]["type"] == type:
                temp.remove(i)
                ans.append(set[i]["answers"]["ans1"])
        if len(ans) >= 3:
            random.shuffle(ans)
            ans = ans[:2]
            ans.append(set[current["order"][session["current"]["current"]]]["answers"]["ans1"])
        else:
            ans.append(set[current["order"][session["current"]["current"]]]["answers"]["ans1"])
    while len(ans) < 3:
        quest = random.choice(temp)
        temp.remove(quest)
        ans.append([set[quest]["answers"]["ans1"]])
    random.shuffle(ans)

    send_data = {
        "done":False,
        "correct":correct,
        "answer":current_ans,
        "question":next_quest["question"],
        "answers":{
            "ans1":ans[0],
            "ans2":ans[1],
            "ans3":ans[2]
        },
        "quest_num":quest_num
    }
    return send_data

@app.route("/finish/questions")
def finish_questions():
    if session.get("task"):
        data = session.get("task")
        query = {"username":data["owner"]}
        update = {"$set":{"data.groups."+data["group"]+".assignments."+data["task"]+".data."+username():session["stats"]}}
        user_data_db.update_one(query, update)
        session.pop("task")
    return render_template("tools/finish.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=[],stats=session["stats"])

@app.route("/delete/<name>")
def delete(name):
    if login() == False:
        return render_template("login/login.html")
    sets = get_sets()
    query = {"username":username()}
    update = {"$unset":{"data.sets."+name:{}}}
    user_data_db.update_one(query,update)
    session["notifications"] = {"title":"Success","body":f"You Have Deleted: {name}","type":"success","icon":"ph-check-circle"}
    if name in list(global_data_db.find_one({"name":"sets"})["data"]):
        sets = global_data_db.find_one({"name":"sets"})["data"]
        sets.remove(name)
        query = {"name":"sets"}
        update = {"$set":{"data":sets}}
        global_data_db.update_one(query, update)
    return redirect("/")



@app.route("/upgrade")
def upgrade():
    if login() == False:
        notifications = []
        users_name = "Guest"
        settings = {"interface":{"theme":"green","cards":"straight"},"accessibility":{"fontSize":"normal","font":"roboto"}}
        boosting = [False,"/static/logo.png"]
        streak = 0

    else:
        if session.get("notifications"):
            notifications = session.get("notifications")
            session.pop("notifications")
        else:
            notifications = []
        users_name = username()
        settings = get_settings()
        boosting = userinfo(username())
        streak = get_streak()
    notifications = []
    return render_template("upgrade.html",streak=streak,name=users_name,settings=settings,boosting=boosting,notifications=notifications)

@app.route("/finish")
def finish():
    if login() == False:
        return render_template("login/login.html")
    notifications = []
    if session.get("task"):
        data = session.get("task")
        query = {"username":data["owner"]}
        update = {"$set":{"data.groups."+data["group"]+".assignments."+data["task"]+".data."+username():True}}
        user_data_db.update_one(query, update)
        session.pop("task")
    return render_template("tools/finish_flash.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/fill/<name>")
def fill(name):
    if login() == False:
        return render_template("login/login.html")
    notifications = []
    add_streak()
    return render_template("tools/fill.html",title=name,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),set=get_sets()[name],notifications=notifications)

@app.errorhandler(500)
def server_error(e):
    session["notifications"] = [{"title":"Error 500","body":"There Was An Error Try Again Later","type":"error","icon":"ph-x-circle"}]
    return redirect("/")

@app.errorhandler(404)
def page_not_found(e):
    session["notifications"] = [{"title":"Error 404","body":"We Were Unable To Find The Page That You Were Looking For","type":"error","icon":"ph-x-circle"}]
    return redirect("/")

@app.route("/test/<set>",methods=["POST","GET"])
def test_mode(set):
    if login() == False:
        return render_template("login/login.html")
    notifications = []
    questions = []
    quest_set = {}
    level = userinfo(username())[0] 
    if level != "elite" and level != "admin":
        session["notifications"] = [{"title":"Upgrade","body":"You Need To Upgrade To Access Test Mode","type":"warning","icon":"ph-warning-circle"}]
        return redirect("/")
    set_data = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["sets"][set]
    if request.method == "POST":
        for i in range(1,len(list(set_data))):
            ans = request.form[f"Q{i}"]
            quest = set_data[f"Q{i}"]["question"]
            similarity_num = similarity(ans.lower(),str(set_data[f"Q{i}"]["answers"]["ans1"]).lower())
            if similarity_num > 0.8:
                session["stats"][str(i)] = {"quest":quest,"correct":True}
            else:
                session["stats"][str(i)] = {"quest":quest,"correct":False}
        return render_template("tools/finish.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications,stats=session["stats"])
    else:
        for i in range(1,len(list(set_data))):
            questions = []
            for j in range(1,len(list(set_data))):
                questions.append(f"Q{j}")
            quest_set[f"Q{i}"] = {
                "question":set_data[f"Q{i}"]["question"],
                "type":None,
                "answer":None
            }
            quest = set_data[f"Q{i}"]
            if len(quest["answers"]["ans1"].split()) < 10 and random.randint(0,2) == 0:
                quest_set[f"Q{i}"]["type"] = "text"
                quest_set[f"Q{i}"]["answer"] = quest["answers"]["ans1"]
            else:
                answers = [quest["answers"]["ans1"]]
                temp = questions
                temp.remove(f"Q{i}")
                for j in range(1,len(list(set_data))):
                    ans = set_data[f"Q{j}"]
                    if ans["type"] == quest["type"] and ans["answers"]["ans1"] != quest["answers"]["ans1"]:
                        answers.append(ans["answers"]["ans1"])
                    if len(answers) == 3:
                        break
                
                if len(answers) != 3:
                    while len(answers) != 3:
                        random_ans = random.choice(temp)
                        answers.append(set_data[random_ans]["answers"]["ans1"])
                        temp.remove(random_ans)
                random.shuffle(answers)
                quest_set[f"Q{i}"]["type"] = "multi"
                quest_set[f"Q{i}"]["answer"] = answers
            if session.get("stats"):
                session.pop("stats")
            session["stats"] = {}
    return render_template("tools/test_mode.html",title=set,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),set=get_sets()[set],notifications=notifications,quest_set=quest_set)

@app.route("/play", methods=["POST","GET"])
def play():
    if login() == False:
        return render_template("login/login.html")
    if request.method == "POST":
        code = request.form["code"]
        codes = global_data_db.find_one({"name":"play"})["data"]
        if code not in codes:
            session["notifications"] = [{"title":"Failed","body":f"{code} Is Not A valid Key, Please Try Again","type":"warning","icon":"ph-warning-circle"}]
            return redirect("/play")
        else:
            return redirect(f"/play/{int(code)}")
    if session.get("notifications"):
        notifications = session.get("notifications")
        session.pop("notifications")
    else:
        notifications = []
    return render_template("play/play.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/play/stats/<code>")
def play_sets(code):
    if login() == False:
        return render_template("login/login.html")
    notifications = []
    return render_template("play/play_stats.html",code=code,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/play/<code>")
def play_code(code):
    if login() == False:
        return render_template("login/login.html")
    notifications = []
    codes = global_data_db.find_one({"name":"play"})["data"]
    play_info = codes[code]
    players = len(play_info["users"])
    level = userinfo(username())[0]
    if (players >= 3 and level == False) or (players >= 5 and level == "premium") or (players >= 10 and level == "pro") or (players >= 44 and level == "elite"):
        session["notifications"] = [{"title":"Failed","body":"There Are No Spaces Left For You","type":"warning","icon":"ph-warning-circle"}]
        return redirect("/")
    if code not in list(codes):
        session["notifications"] = [{"title":"Failed","body":f"{code} Is Not A valid Key, Please Try Again","type":"warning","icon":"ph-warning-circle"}]
        return redirect("/play")
    play_info = {
        "score":{},
        "user_image":userinfo(username())[1]
    }
    query = {"name":"play"}
    update = {"$set":{"data."+code+".users."+username():play_info}}
    global_data_db.update_one(query, update)
    return render_template("play/play_hub.html",code=code,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/play/leave/<code>")
def leave_code(code):
    if login() == False:
        return render_template("login/login.html")
    query = {"name":"play"}
    update = {"$unset":{"data."+code+".users."+username():""}}
    global_data_db.update_one(query, update)
    return redirect("/")

@app.route("/host")
def host():
    if login() == False:
        return render_template("login/login.html")
    notifications = []
    play = global_data_db.find_one({"name":"play"})["data"]
    for i in play:
        if play[i]["host"] == username():
            query = {"name":"play"}
            update = {"$unset":{"data."+i:""}}
            global_data_db.update_one(query, update)
    code = random.randint(100000,999999)
    return render_template("play/host.html",code=code,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications,sets=get_sets())


@app.route("/play/host/<code>/<set>")
def play_host(code,set):
    if login() == False:
        return render_template("login/login.html")
    notifications = []
    play_data = {
        "host":username(),
        "users":{},
        "started":False,
        "set":set
    }
    query = {"name":"play"}
    update = {"$set":{"data."+code:play_data}}
    global_data_db.update_one(query, update)
    return render_template("play/play_host.html",code=code,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/play/start/<code>")
def play_start(code):
    if login() == False:
        return render_template("login/login.html")
    notifications = []
    play = global_data_db.find_one({"name":"play"})["data"]
    set = user_data_db.find_one({"username":play[code]["host"],"type":"user_data"})["data"]["sets"][play[code]["set"]]
    if play[code]["host"] == username():
        query = {"name":"play"}
        update = {"$set":{"data."+code+".started":True}}
        global_data_db.update_one(query, update)
        return render_template("play/play_start.html",quests=len(set),users=play[code]["users"],code=code,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)
    else:
        return redirect(f"/play/{int(code)}")

@app.route("/play/started/<code>",methods=["POST","GET"])
def play_started(code):
    if login() == False:
        return render_template("login/login.html")
    play = global_data_db.find_one({"name":"play"})["data"]
    name = play[code]["set"]
    host = play[code]["host"]
    notifications = []
    set = user_data_db.find_one({"username":host,"type":"user_data"})["data"]["sets"][name]
    if request.method == "POST":
        current = session.get("current")
        if session.get("current")["current"] == len(session.get("current")["order"]):
            return render_template("play/play_finish.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications,stats=session["stats"])
        if session.get("next") == "False":
            answer = request.form["button"]
            answers = []
            for i in set[current["order"][current["current"]]]["answers"]:
                answers.append(set[current["order"][current["current"]]]["answers"][i])
            answer1 = answers[0]
            for i in range(1,len(answers)):
                answer1 += ", "+i
            session["next"] = "True"
            session["current"] = {"current":current["current"]+1,"order":current["order"]}
            quest = set[current["order"][current["current"]]]["question"]
            if answer in answers:
                query = {"name":"play"}
                update = {"$set":{"data."+code+".users."+username()+".score."+str(current["current"]+1):{"quest":quest,"correct":True}}}
                global_data_db.update_one(query, update)
                return render_template("correct.html",title=name,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),answer=answer1,notifications=notifications)
            else:
                db["play"][code]["users"][username()]["score"][str(current["current"]+1)] = {"quest":quest,"correct":False}
                return render_template("wrong.html",title=name,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),answer=answer1,notifications=notifications)
        else:
            session["next"] = "False"
    else:
        if len(set) < 4:
            session["notifications"] = [{"title":"Failed","body":"You Need More Questions","type":"warning","icon":"ph-warning-circle"}]
            return redirect("/")
        if session.get("stats"):
            session.pop("stats")
        session["stats"] = {}
        order = []
        for i in range(1,len(set)):
            order.append("Q"+str(i))
        random.shuffle(order)
        session["next"] = "False"
        session["current"] = {"current":0,"order":order}
    ans = []
    if session.get("current")["current"] == len(session.get("current")["order"]):
        return render_template("play/play_finish.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications,stats=session["stats"])
    current = session.get("current")
    question = set[current["order"][current["current"]]]["question"]
    amount_needed = 3-len(set[current["order"][session["current"]["current"]]]["answers"])
    ans.append(set[current["order"][session["current"]["current"]]]["answers"]["ans1"])
    temp = list(current["order"])
    temp.remove(current["order"][current["current"]])
    try:
        type = set[current["order"][current["current"]]]["type"]
    except:
        for i in range(amount_needed):
            quest = random.choice(temp)
            temp.remove(quest)
            ans.append(set[quest]["answers"][random.choice(list(set[quest]["answers"].keys()))])
        random.shuffle(ans)
    else:
        ans = []
        for i in temp:
            if set[i]["type"] == type:
                temp.remove(i)
                ans.append(set[i]["answers"]["ans1"])
        if len(ans) >= 3:
            random.shuffle(ans)
            ans = ans[:2]
            ans.append(set[current["order"][session["current"]["current"]]]["answers"]["ans1"])
        else:
            ans.append(set[current["order"][session["current"]["current"]]]["answers"]["ans1"])
        while len(ans) < 3:
            quest = random.choice(temp)
            temp.remove(quest)
            ans.append(set[quest]["answers"][random.choice(list(set[quest]["answers"].keys()))])
        random.shuffle(ans)
        quest_num = current["order"][session["current"]["current"]]
        session["current_play_code"] = code
    return render_template("tools/question.html",owner=host,total_quests=quest_num,quest_num=quest_num,title=name,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),set=name,ans=ans,question=question,notifications=notifications,mode="play")

@app.route("/api/play/quest",methods=["POST","GET"])
def api_quest_ans_play():
    code = session.get("current_play_code")
    correct = False
    data = request.get_json()
    owner = data["user"]
    current = session.get("current")
    set = user_data_db.find_one({"username":owner,"type":"user_data"})["data"]["sets"][data["set"]]
    quest = set[current["order"][current["current"]]]["question"]
    current_ans = set[data["question"]]["answers"]["ans1"]
    current["current"] += 1
    session["current"] = current
    if data["answer"] == current_ans:
        session["stats"][str(current["current"])] = {"quest":set[data["question"]]["question"],"correct":True}
        correct = True
        query = {"name":"play"}
        update = {"$set":{"data."+code+".users."+username()+".score."+str(current["current"]+1):{"quest":quest,"correct":True}}}
        global_data_db.update_one(query, update)
    else:
        session["stats"][str(current["current"])] = {"quest":set[data["question"]]["question"],"correct":False}
        query = {"name":"play"}
        update = {"$set":{"data."+code+".users."+username()+".score."+str(current["current"]+1):{"quest":quest,"correct":False}}}
        global_data_db.update_one(query, update)
    if session.get("current")["current"] == len(session.get("current")["order"]):
        add_streak()
        return {"done":True,"answer":current_ans,"correct":correct}
    quest_num = current["order"][current["current"]]
    next_quest = set[quest_num]

    ans = []
    temp = list(current["order"])
    temp.remove(current["order"][current["current"]])
    ans.append(set[current["order"][session["current"]["current"]]]["answers"]["ans1"])
    try:
        type = set[current["order"][current["current"]]]["type"]
    except:
        pass
    else:
        ans = []
        for i in temp:
            if set[i]["type"] == type:
                temp.remove(i)
                ans.append(set[i]["answers"]["ans1"])
        if len(ans) >= 3:
            random.shuffle(ans)
            ans = ans[:2]
            ans.append(set[current["order"][session["current"]["current"]]]["answers"]["ans1"])
        else:
            ans.append(set[current["order"][session["current"]["current"]]]["answers"]["ans1"])
    while len(ans) < 3:
        quest = random.choice(temp)
        temp.remove(quest)
        ans.append([set[quest]["answers"]["ans1"]])
    random.shuffle(ans)

    send_data = {
        "done":False,
        "correct":correct,
        "answer":current_ans,
        "question":next_quest["question"],
        "answers":{
            "ans1":ans[0],
            "ans2":ans[1],
            "ans3":ans[2]
        },
        "quest_num":quest_num
    }
    return send_data


@app.route("/play/end/<code>")
def play_end(code):
    if login() == False:
        return render_template("login/login.html")
    if username() == db["play"][code]["host"]:
        del db["play"][code]
    else:
        session["notifications"] = [{"title":"Failed","body":"You Are Not The Host","type":"warning","icon":"ph-warning-circle"}]
        return redirect("/")
    return redirect("/")

@app.route("/api/play/started/<code>")
def play_started_api(code):
    if login() == False:
        return render_template("login/login.html")
    play = global_data_db.find_one({"name":"play"})["data"]
    started = {"started":play[code]["started"]}
    return started

@app.route("/api/play/leaderboard/<code>")
def play_leaderboard_api(code):
    if login() == False:
        return render_template("login/login.html")
    play = global_data_db.find_one({"name":"play"})["data"]
    leaderboard = play[code]["users"]
    return leaderboard

@app.route("/automations",methods=["GET","POST"])
def automations():
    if login() == False:
        return render_template("login/login.html")
    if request.method == "POST":
        db[username()]["rules"] = {}
        i = 0
        while True:
            try:
                subject = request.form[f"subject{i}"]
                folder = request.form[f"folder{i}"]
            except:
                break
            else:
                for j in db[username()]["rules"]:
                    if subject in db[username()]["rules"][j]["subject"]:
                        session["notifications"] = [{"title":"Failed","body":"You Already Have A Rule For This Subject","type":"warning","icon":"ph-warning-circle"}]
                        return redirect("/")
                db[username()]["rules"][rule_id()] = {
                    "subject":subject,
                    "folder":folder,
                    "type":"move"
                }
            i += 1
        return redirect("/")
    notifications = []
    return render_template("rules.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications,folders=make_dict_folder(db[username()]["folders"]),rules=make_dict_rules(db[username()]["rules"]))



    
@app.route("/code")
def user_code():
    if login() == False:
        return render_template("login/login.html")
    try:
        db[username()]["code"]
    except:
        user_code = gen_code()
        db[username()]["code"] = user_code
        db["codes"][username()] = user_code
    else:
        user_code = db[username()]["code"]
    return user_code

@app.route("/ping")
def ping():
    return "Pong"

@app.route("/schedule")
def schedule():
    if login() == False:
        return render_template("login/login.html")
    notifications = []
    return render_template("schedule.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/new/group",methods=["GET","POST"])
def new_group():
    if login() == False:
        return render_template("login/login.html")
    amount_groups = len(user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["groups"])
    level = userinfo(username())[0]
    if (amount_groups >= 1 and level == "") or (amount_groups >= 2 and level == "premium") or (amount_groups >= 5 and level == "pro") or (amount_groups >= 20 and level == "elite"):
        session["notifications"] = [{"title":"Failed","body":"You Have Reached The Max Amount Of Groups","type":"warning","icon":"ph-warning-circle"}]
        return redirect("/")
    if request.method == "POST":
        title = request.form["title"]
        desc = request.form["desc"]
        cover = request.form["cover"]
        type = request.form["type"]
        group_id = gen_id()
        group = {
            "sets":[],
            "users":[username()],
            "folders":{},
            "settings":{
                "Title":title,
                "Desc":desc,
                "Cover":cover,
                "Owner":username(),
                "upload_own":False,
                "type":type
            }
        }
        if type == "class":
            group["assignments"] = {}
        query = {"username":username()}
        update = {"$set":{"data.groups."+group_id:group}}
        user_data_db.update_one(query, update)
        return redirect("/")
    notifications = []
    return render_template("groups/new_group.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/edit/group/<group>")
def edit_group(group):
    if login() == False:
        return render_template("login/login.html")
    group_info = make_dict_group(db[username()]["groups"][group])
    notifications = []
    return render_template("groups/edit_group.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),group_info=group_info,notifications=notifications)

@app.route("/group/<group>",methods=["POST","GET"])
def group(group):
    if login() == False:
        return render_template("login/login.html")
    if session.get("notifications"):
        notifications = session.get("notifications")
        session.pop("notifications")
    else:
        notifications = []
    if request.method == "POST":
        add_username = request.form["username"]
        users = global_data_db.find_one({"name":"usernames"})["data"]
        group_users = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["groups"][group]["users"]
        if add_username not in users:
            session["notifications"] = [{"title":"Failed","body":"User Does Not Exist","type":"warning","icon":"ph-warning-circle"}]
        elif add_username in group_users:
            session["notifications"] = [{"title":"Failed","body":"User Is Already In The Group","type":"warning","icon":"ph-warning-circle"}]
        else:
            query = {"username":add_username}
            update = {"$push":{"data.added_groups":[username(),group]}}
            user_data_db.update_one(query, update)
            query = {"username":username()}
            update = {"$push":{"data.groups."+group+".users":add_username}}
            user_data_db.update_one(query, update)
            session["notifications"] = [{"title":"Success","body":"User Has Been Added To The Group","type":"success","icon":"ph-check-circle"}]
        return redirect("/group/"+group)
    else:
        sets = {}
        groups = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["groups"]
        user_sets = get_sets()

        if group in list(groups):
            group_name = groups[group]["settings"]["Title"]
            names = groups[group]["sets"]
            owner = groups[group]["settings"]["Owner"]
            for i in range(len(names)):
                sets[i] = user_sets[groups[group]["sets"][i]]
            user_data = user_data_group(groups[group]["users"])
            folders = groups[group]["folders"]
            type = groups[group]["settings"]["type"]
            if type == "class":
                assignments = groups[group]["assignments"]
                title = groups[group]["settings"]["Title"]
                tasks = groups[group]["assignments"]
        else:
            added_groups = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["added_groups"]
            for i in added_groups:
                if i[1] == group:
                    this_group = user_data_db.find_one({"username":i[0],"type":"user_data"})["data"]["groups"][group]
                    owner_sets = user_data_db.find_one({"username":i[0],"type":"user_data"})["data"]["sets"]
                    group_name = this_group["settings"]["Title"]
                    names = this_group["sets"]
                    owner = this_group["settings"]["Owner"]
                    for i in range(len(names)):
                        print(this_group["sets"][i])
                        sets[i] = owner_sets[this_group["sets"][i]]
                    user_data = user_data_group(this_group["users"])
                    folders = this_group["folders"]
                    type = this_group["settings"]["type"]
                    if type == "class":
                        assignments = this_group["assignments"]
                        title = this_group["settings"]["Title"]
                        tasks = this_group["assignments"]
        if type == "class":
            return render_template("groups/classes/classroom.html",tasks=tasks,assignments=assignments,group_name=group_name,folders=folders,user_data=user_data,sets=sets,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications,title=title,owner=owner,id=group)
        else:
            return render_template("groups/group.html",group_name=group_name,folders=folders,user_data=user_data,sets=sets,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications,title=group,owner=owner)
    
@app.route("/add/group/<group>/<name>")
def add_group_set(group,name):
    if login() == False:
        return render_template("login/login.html")
    groups = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["groups"]
    owner = groups[group]["settings"]["Owner"]
    if username() != owner:
        return "Error"
    else:
        if name in list(groups[group]["sets"]):
            return "Error"
        else:
            query = {"username":username()}
            update = {"$push":{"data.groups."+group+".sets":name}}
            user_data_db.update_one(query, update)
            return redirect("/group/"+group)
        

@app.route("/remove/group/<group>")
def remove_group(group):
    if login() == False:
        return render_template("login/login.html")
    users = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["groups"][group]["users"]
    for user in users:
        query = {"username":user}
        update = {"$pull":{"data.added_groups":[username(),group]}}
        user_data_db.update_one(query, update)
    query = {"username":username()}
    update = {"$unset":{"data.groups."+group:""}}
    user_data_db.update_one(query, update)
    return redirect("/")

@app.route("/group/<group>/folder/<folder>")
def group_folder(group,folder):
    if login() == False:
        return render_template("login/login.html")
    notifications = []
    groups = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["groups"]
    if group in list(groups):
        group_name = groups[group]["settings"]["Title"]
        folders = groups[group]["folders"]
        folder_info = folders[folder]
        sets = {}
        user_sets = get_sets()
        names = folder_info["sets"]
        folder_name = folder_info["settings"]["title"]
        for i in range(len(names)):
            sets[i] = user_sets[folder_info["sets"][i]]
        owner = groups[group]["settings"]["Owner"]
    else:
        sets = {}
        added_groups = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["added_groups"]
        for i in added_groups:
            if i[1] == group:
                this_group = user_data_db.find_one({"username":i[0],"type":"user_data"})["data"]["groups"][group]
                owner_sets = user_data_db.find_one({"username":i[0],"type":"user_data"})["data"]["sets"]
                names = this_group["sets"]
                group_name = this_group["settings"]["Title"]
                for i in range(len(names)):
                    sets[i] = owner_sets[this_group["sets"][i]]
        folder_name = this_group["folders"][folder]["settings"]["title"]
        owner = this_group["settings"]["Owner"]
    return render_template("groups/folder.html",owner=owner,group_name=group_name,folder_id=folder,sets=sets,group_id=group,folder_name=folder_name,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/group/folder/new/<group>",methods=["POST","GET"])
def new_group_folder(group):
    if login() == False:
        return render_template("login/login.html")
    notifications = []
    if request.method == "POST":
        title = request.form["title"]
        desc = request.form["desc"]
        cover = request.form["cover"]
        folder_id = gen_id()
        folder = {
            "sets":[],
            "settings":{
                "title":title,
                "desc":desc,
                "cover":cover,
            }
        }
        query = {"username":username(),"type":"user_data"}
        print(folder_id)
        update = {"$set":{"data.groups."+group+".folders."+folder_id:folder}}
        user_data_db.update_one(query, update)
        return redirect("/group/"+group)
    return render_template("folders/new_folder.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/group/<group>/folder/edit/<folder>",methods=["POST","GET"])
def edit_group_folder(group,folder):
    if login() == False:
        return render_template("login/login.html")
    old_folder = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["groups"][group]["folders"][folder]
    if request.method == "POST":
        title = request.form["title"]
        desc = request.form["desc"]
        cover = request.form["cover"]
        query = {"username":username()}
        update = {"$set":{"data.groups."+group+".folders."+folder+".settings.title":title,"data.groups."+group+".folders."+folder+".settings.desc":desc,"data.groups."+group+".folders."+folder+".settings.cover":cover}}
        user_data_db.update_one(query, update)
        return redirect("/group/"+group)
    notifications = []
    folder_info = {"name":old_folder["settings"]["title"],"desc":old_folder["settings"]["desc"],"cover":old_folder["settings"]["cover"]}
    return render_template("folders/edit_folder.html",folder=folder_info,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/group/<group>/folder/add/<folder>/<name>")
def add_group_folder_set(group,folder,name):
    if login() == False:
        return render_template("login/login.html")
    groups = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["groups"]
    group_info = groups[group]
    set_name = group_info["sets"][int(name)]
    query = {"username":username()}
    update = {"$push":{"data.groups."+group+".folders."+folder+".sets":set_name}}
    user_data_db.update_one(query, update)
    return {"success":True}

@app.route("/group/<group>/folder/remove/<folder>")
def remove_group_folder(group,folder):
    if login() == False:
        return render_template("login/login.html")
    query = {"username":username()}
    update = {"$unset":{"data.groups."+group+".folders."+folder:""}}
    user_data_db.update_one(query, update)
    return redirect("/group/"+group)

@app.route("/group/remove/<group_name>/<set_pos>")
def remove_group_set(group_name,set_pos):
    group = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["groups"][group_name]["sets"]
    print(group)
    set_name = group[int(set_pos)]
    group.remove(set_name)
    print(group)
    query = {"username":username()}
    update = {"$set":{"data.groups."+group_name+".sets":group}}
    user_data_db.update_one(query, update)
    return {"success":True}

@app.route("/remove/group/<group>/<name>")
def remove_group_user(group,name):
    if login() == False:
        return render_template("login/login.html")
    owner = username()
    query = {"username":name}
    update = {"$pull":{"data.added_groups":[owner,group]}}
    user_data_db.update_one(query, update)
    query = {"username":owner}
    update = {"$pull":{"data.groups."+group+".users":name}}
    user_data_db.update_one(query, update)
    return redirect("/group/"+group)

@app.route("/group/<group>/folder/remove/<folder>/<name>")
def remove_group_folder_set(group,folder,name):
    if login() == False:
        return render_template("login/login.html")
    groups = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["groups"]
    group_info = groups[group]
    sets = group_info["folders"][folder]["sets"]
    set_name = sets[int(name)]
    sets.remove(set_name)
    query = {"username":username()}
    update = {"$set":{"data.groups."+group+".folders."+folder+".sets":sets}}
    user_data_db.update_one(query, update)
    return {"success":True}

@app.route("/api/smartsubject",methods=["POST","GET"])
def api_smartsubject():
    data = request.get_json()
    return {"subject":subject(data["text"])}

@app.route("/settings",methods=["POST","GET"])
def settings():
    if login() == False:
        return render_template("login/login/login.html")
    notifications = {}
    if request.method == "POST":
        theme = request.form["theme"]
        user_data_db.update_one({"username":username(),"type":"user_data"},{"$set":{"data.settings.interface.theme":theme}})
    return render_template("settings/settings.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/focus")
def focuse():
    if login() == False:
        return render_template("login/login.html")
    notifications = {}
    return render_template("focus.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/features")
def about():
    return render_template("login/about.html")

@app.route("/streak")
def streaks():
    if login() == False:
        return render_template("login/login.html")
    notifications = {}
    return render_template("/home/streak.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/updates")
def updates():
    return render_template("login/update.html")

@app.route("/updates/<title>")
def view_update(title):
    """
    Renders the view_update.html template with the specified title.

    Args:
        title (str): The title to be passed to the template.

    Returns:
        The rendered template.
    """
    return render_template("login/view_update.html",title=title)


@app.route("/api/learn/like",methods=["POST","GET"])
def api_learn_like():
    data = request.get_json()
    return {"liked":True}

@app.route("/offline/home")
def offline_home():
    return render_template("offline_home.html")

@app.route('/webhook', methods=['POST'])
def webhook():
    event = None
    payload = request.data
    sig_header = request.headers['STRIPE_SIGNATURE']
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        raise e

    except stripe.error.SignatureVerificationError as e:
        raise e
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        print(session)
        if session["payment_status"] == "paid":
            user_data_db.update_one({"username":session["metadata"]["name"],"type":"user_data"},{"$set":{"data.level":session["metadata"]["plan"]}})
    else:
        print('Unhandled event type {}'.format(event['type']))
    return jsonify(success=True)

@app.route('/join/<plan>', methods=['POST'])
def create_checkout_session(plan):
    YOUR_DOMAIN = "https://beta.booogle.app/"
    if plan == "premium":
        price_id = "price_1OaKMPEg9DaDrNLaYFm4Uggt"
    elif plan == "pro":
        price_id = "price_1OaKNQEg9DaDrNLaRiOBrfzi"
    elif plan == "elite":
        price_id = "price_1OaKNrEg9DaDrNLaGPsrMJ28"
    else:
        session["notifications"] = [{"title":"Failed","body":"Invalid Plan","type":"warning","icon":"ph-warning-circle"}]

        return redirect("/")
    try:
        checkout_session = stripe.checkout.Session.create(

            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=YOUR_DOMAIN + 'join/success/'+plan,
            cancel_url=YOUR_DOMAIN + 'join/cancel/'+plan,
            metadata = {
                "name":username(),
                "plan":plan
            },
        )
    except Exception as e:
        return "Error"
    return redirect(checkout_session.url, code=303)

@app.route("/classroom/<classroom>")
def classroom(classroom):
    if login() == False:
        return render_template("login/login.html")
    notifications = []
    folders = {}
    owner = username()
    sets = {}
    user_data = {}
    return render_template("groups/classes/classroom.html",folders=folders,owner=owner,sets=sets,user_data=user_data,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/new/learn",methods=["POST","GET"])
def new_learn():
    if login() == False:
        return render_template("login/login.html")
    notifications = []
    if request.method == "POST":
        title = request.form["title"]
        desc = request.form["desc"]
        subject = request.form["subject"]
        background = request.form["cover"]
        title_mod = mod(title)
        desc_mod = mod(desc)
        if title_mod == 1 or desc_mod == 1:
            session["notifications"] = [{"title":"Failed","body":"Title Or Description Contain Possible Rude/Inappropriate Content","type":"warning","icon":"ph-warning-circle"}]
            return redirect("/new/learn/")
        else:
            return redirect("/edit/learn/"+title)
    return render_template("learn/new_learn.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/learn")
def learn():
    if login() == False:
        return render_template("login/login.html")
    notifications = {}
    learn_sets = {
        "id-ejejeje":{
            "settings":{
            "name":"Title",
            "desc":"Desc",
            "background":"gear",
            "user":"Test",
            "level":False,
            "subject":"Other"
            }
        }
    }
    return render_template("learn/learn.html",learn_sets=learn_sets,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)


@app.route("/set_profile_image",methods=["POST","GET"])
def set_profile_image():
    if login() == False:
        return render_template("login/login.html")
    if request.method == "POST":
        image = request.form["image"]
        query = {"username":username()}
        update = {"$set":{"data.profile_image":image}}
        user_data_db.update_one(query, update)
        return redirect("/")
    notifications = {}
    current_color = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["profile_image"]
    return render_template("set_profile_image.html",current_color=current_color,notifications=notifications,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()))

@app.route("/api/smartstudy",methods=["POST","GET"])
def api_smartstudy():
    data = request.get_json()
    print(data)
    return "Success"

@app.route("/api/ans_fix",methods=["POST","GET"])
def api_ans_fix():
    data = request.get_json()
    fixed = {"ans":answer_fix(data["ans"])}

    return fixed

@app.route("/learn/<set>")
def learn_set(set):
    if login() == False:
        return render_template("login/login.html")
    notifications = {}
    return render_template("learn/learn_set.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/edit/learn/<set>")
def edit_learn_set(set):
  
    if login() == False:
        return render_template("login/login.html")
    notifications = {}
    return render_template("learn/edit_learn_set.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/custom_upgrade")
def custom_upgrade():
    if login() == False:
        return render_template("login/login.html")
    notifications = {}
    return render_template("custom_upgrade.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/code/<set>")
def code_ide(set):
    if login() == False:
        return render_template("login/login.html")
    notifications = {}
    set_data = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["code"][set]
    title = set_data["title"]
    instructions = set_data["instructions"]
    return render_template("tools/ide.html",code="",owner=username(),type="user",id=set,title=title,instructions=instructions,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/code/@<user>/<set>")
def code_ide_user(user,set):
    if login() == False:
        notifications = []
        users_name = "Guest"
        settings = {"interface":{"theme":"green","cards":"straight"},"accessibility":{"fontSize":"normal","font":"roboto"}}
        boosting = [False,"/static/logo.png"]
        streak = 0
    else:
        notifications = []
        users_name = username()
        settings = get_settings()
        boosting = userinfo(username())
        streak = get_streak()
    set_data = user_data_db.find_one({"username":user,"type":"user_data"})["data"]["code"][set]
    title = set_data["title"]
    instructions = set_data["instructions"]
    return render_template("tools/ide.html",code="",owner=user,type="community",id=set,title=title,instructions=instructions,name=users_name,streak=streak,settings=settings,boosting=boosting,notifications=notifications)

@app.route("/new/code",methods=["POST","GET"])
def new_code():
    if login() == False:
        return render_template("login/login.html")
    notifications = {}
    if request.method == "POST":
        id = gen_id()
        title = request.form["title"]
        desc = request.form["desc"]
        background = request.form["cover"]
        title_mod = mod(title)
        desc_mod = mod(desc)
        lang = request.form["subject"]
        instructions = request.form["instructions"]
        query = {"username":username()}
        update = {"$set":{"data.code."+id:{"id":id,"title":title,"desc":desc,"background":background,"language":lang,"user":username(),"instructions":instructions,"level":userinfo(username())[0]}}}
        user_data_db.update_one(query, update)
        if title_mod == 1 or desc_mod == 1:
            session["notifications"] = [{"title":"Failed","body":"Title Or Description Contain Possible Rude/Inappropriate Content","type":"warning","icon":"ph-warning-circle"}]
            return redirect("/new/code/")
        else:
            return redirect("/code/"+id)
    return render_template("sets/new_code.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

 
@app.route("/api/smartcode",methods=["POST","GET"])
def api_smnartcode():
    data = request.get_json()
    return {"subject":code_lang(data["text"])}

@app.route("/publish/code/<set>")
def publish_code(set):
    if login() == False:
        return render_template("login/login.html")
    published_sets = global_data_db.find_one({"name":"code_sets"})["data"]
    for i in published_sets:
        if set in i:
            session["notifications"] = [{"title":"Failed","body":"Set Already Exists On Community","type":"warning","icon":"ph-warning-circle"}]
            return redirect("/")
    query = {"name":"code_sets"}
    update = {"$push":{"data":[username(),set]}}
    global_data_db.update_one(query, update)
    return redirect("/")

@app.route("/edit/code/<set>",methods=["POST","GET"])
def edit_code(set):
    if login() == False:
        return render_template("login/login.html")
    notifications = {}
    if request.method == "POST":
        title = request.form["title"]
        desc = request.form["desc"]
        background = request.form["cover"]
        lang = request.form["subject"]
        instructions = request.form["instructions"]
        query = {"username":username()}
        update = {"$set":{"data.code."+set:{"id":set,"title":title,"desc":desc,"background":background,"language":lang,"user":username(),"instructions":instructions,"level":userinfo(username())[0]}}}
        user_data_db.update_one(query, update)
        return redirect("/code/"+set)
    else:
        set_data = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["code"][set]
        return render_template("sets/edit_code.html",set_data=set_data,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/delete/code/<set>",methods=["POST","GET"])
def delete_code(set):
    if login() == False:
        return render_template("login/login.html")
    query = {"username":username()}
    update = {"$unset":{"data.code."+set:""}}
    user_data_db.update_one(query, update)
    session["notifications"] = [{"title":"Success","body":"Set Deleted","type":"success","icon":"ph-check-circle"}]
    for i in global_data_db.find_one({"name":"code_sets"})["data"]:
        if set in i:
            query = {"name":"code_sets"}
            update = {"$pull":{"data":[username(),set]}}
            global_data_db.update_one(query, update)
    return redirect("/")

@app.route("/new/assignment/<group>",methods=["POST","GET"])
def new_assignment(group):
    if login() == False:
        return render_template("login/login.html")
    if request.method == "POST":
        title = request.form["title"]
        date = request.form["date"]
        type = request.form["type"]
        set = request.form["set"]
        id = gen_id()
        if type == "code":
            set_name = get_code_sets()[set]["title"]
        else:
            set_name = get_sets()[set]["settings"]["name"]
        task = {
            "title":title,
            "date":date,
            "type":type,
            "set":set,
            "set_name":set_name,
            "data":{}
        }
        query = {"username":username()}
        update = {"$set":{"data.groups."+group+".assignments."+id:task}}
        user_data_db.update_one(query, update)
        return redirect("/group/"+group)
    notifications = {}
    sets = get_sets()
    code_sets = get_code_sets()
    return render_template("groups/classes/new_assignment.html",sets=sets,code_sets=code_sets,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/group/<group>/task/<task>")
def group_task(group,task):
    if login() == False:
        return render_template("login/login.html")
    added_groups = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["added_groups"]
    groups = list(user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["groups"].keys())
    if group in groups:
        owner = username()
        this_group = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["groups"][group]
    else:
        for i in added_groups:
            print(i)
            if i[1] == group:
                owner = i[0]
                this_group = user_data_db.find_one({"username":i[0],"type":"user_data"})["data"]["groups"][group]
    task_info = this_group["assignments"][task]
    set = task_info["set"]
    if owner == username():
        return redirect("/class/admin/"+group+"/"+task)
    if task_info["type"] == "code":
        return redirect("/task/code/"+owner+"/"+set+"/"+task+"/"+group)
    elif task_info["type"] == "flashcards":
        return redirect("/task/flashcards/"+owner+"/"+set+"/"+task+"/"+group)
    else:
        session["task"] = {"owner":owner,"set_id":set,"task":task,"group":group}
        return redirect("/questions/@"+owner+"/"+set)

@app.route("/task/code/<owner>/<set>/<task>/<group>")
def task_code(owner,set,task,group):
    if login() == False:
        return render_template("login/login.html")
    notifications = {}
    set_data = user_data_db.find_one({"username":owner,"type":"user_data"})["data"]["code"][set]
    title = set_data["title"]
    instructions = set_data["instructions"]
    return render_template("tools/ide.html",code="",group_id=group,task_id=task,owner=owner,type="task",id=set,title=title,instructions=instructions,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/submit/code",methods=["POST","GET"])
def submit_code():
    data = request.get_json()
    query = {"username":data["owner"]}
    update = {"$set":{"data.groups."+data["group_id"]+".assignments."+data["task_id"]+".data."+username():data["code"]}}
    user_data_db.update_one(query, update)
    return {"success":True}

@app.route("/task/flashcards/<owner>/<set_id>/<task>/<group>")
def task_flashcards(owner,set_id,task,group):
    if login() == False:
        return render_template("login/login.html")
    notifications = {}
    session["task"] = {"owner":owner,"set_id":set_id,"task":task,"group":group}
    set = user_data_db.find_one({"username":owner,"type":"user_data"})["data"]["sets"][set_id]
    return render_template("tools/cards.html",title=set_id,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),sets=set,notifications=notifications)

@app.route("/class/admin/<group>/<task>")
def class_admin(group,task):
    if login() == False:
        return render_template("login/login.html")
    notifications = {}
    group_info = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["groups"][group]
    task_info = group_info["assignments"][task]
    users = group_info["users"]
    return render_template("groups/classes/admin.html",users=users,group_id=group,task_id=task,group_info=group_info,task=task_info,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/code/class/admin/<group>/<task>/@<user>")
def code_ide_class(group,task,user):
    if login() == False:
        return render_template("login/login.html")
    notifications = {}
    set_name = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["groups"][group]["assignments"][task]["set"]
    set_data = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["code"][set_name]
    title = set_data["title"]
    instructions = set_data["instructions"]
    code = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["groups"][group]["assignments"][task]["data"][user]
    return render_template("tools/ide.html",code=code,owner=username(),type="class",id=set_name,title=title,instructions=instructions,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/questions/class/admin/<group>/<task>/@<user>")
def class_admin_questions(group,task,user):
    if login() == False:
        return render_template("login/login.html")
    notifications = {}
    task = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["groups"][group]["assignments"][task]
    user_info = task["data"][user]
    score = 0
    total = 0
    print(user_info)
    for i in user_info:
        print(i)
        total += 1
        if user_info[i]["correct"] == True:
            score += 1
    percentage = round((score/total)*100)
    time = "WIP"
    return render_template("groups/classes/questions_view.html",time=time,total=total,percentage=percentage,score=score,user=user,group=group,task=task,user_info=user_info,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)


@app.route("/whiteboard")
def whiteboard():
    if login() == False:
        return render_template("login/login.html")
    notifications = {}
    return render_template("tools/whiteboard.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

app.run(host='0.0.0.0', port=80,debug=True)