from flask import Flask, render_template,redirect,request,current_app,session
from api.static.fun import get_folders,get_settings,get_streak,get_sets,hash_value,gen_user_token,add_streak,streak,login,check_image,gen_id,make_dict_group,user_data_group,username,recommend,rule_id,gen_code,leaderboard_dict,similarity,userinfo,make_dict,mod,play_dict,smart,last_7,week_add,stats_dict,update,make_dict_folder,subject,make_dict_rules
from better_profanity import profanity
import emoji
import requests
import os,random,json,re
import cohere
from urllib.parse import urlparse
from datetime import timedelta
from datetime import datetime
from flask_compress import Compress
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
client = MongoClient("mongodb+srv://GoodVessel92551:Gzw9KNoZEwhgIkpq@booogle.j0arbkm.mongodb.net/?retryWrites=true&w=majority")
db = client["Booogle_Revise"]
global_data_db = db["Global_Data"]
user_data_db = db["User_Data"]

app = Flask(__name__)
app.secret_key = os.getenv('secret_key')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365)
compress = Compress(app)

@app.route("/")
def home():
    print(login())
    if login() == False:
        return render_template("login.html")
    if session.get("notifications"):
        notifications = session.get("notifications")
        session.pop("notifications")
    else:
        notifications = []
    users_groups = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["groups"]
    added_groups = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["added_groups"]
    for i in added_groups:
        owners_username = i[0]
        group = i[1]
        group_data = user_data_db.fin_one({"username":owners_username,"type":"user_data"})["data"]["groups"][group]
        users_groups[group] = group_data
    streak()
    return render_template("home.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),sets=get_sets(),is_new=new,notifications=notifications,folders=get_folders(),groups=users_groups)

@app.route("/signup",methods=["POST","GET"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_value(request.form["password"])
        pattern = re.compile('^[a-zA-Z0-9]+$')
        usernames = global_data_db.find_one({"name":"usernames"})
        if username not in usernames["data"] and len(username) < 15 and bool(pattern.match(username)) and request.form["password"] == request.form["repeat_password"]:
            print("correct")
            user_data = {"username":username,"type":"user_data","data":{
                "streak":{"streak":0,"time":str(datetime.now())},
                "sets":{},
                "level":"",
                "groups":{},
                "rules":{},
                "added_groups":[],
                "folders":{},
                "settings":{"interface":{"theme":"green","cards":"straight"},"accessibility":{"fontSize":"normal","font":"roboto"}},
                "password":password
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
        how = request.form["how"]
        role = request.form["role"]
    return render_template("signup.html")

@app.route("/login",methods=["POST","GET"])
def user_login():
    if request.method == "POST":
        username = request.form["username"]
        password = hash(request.form["password"]+os.getenv('salt'))
        if username in db["usernames"]:
            if password == db["B-AUTH-"+username]["password"]:
                user_token = gen_user_token()
                session["token"] = user_token
                db["B-KEYS"][hash(user_token+os.getenv('salt'))] = username
                return redirect("/")
    return render_template("login_account.html")

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
    settings = db[username]["sets"][set]["settings"]
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
    view_sets = {}
    share_links = []
    for i, (name_key, set_name) in enumerate(sets):
        name = user_data_db.find_one({"username":name_key,"type":"user_data"})
        print(name_key)
        share_links.append("/share/@"+name_key+"/"+set_name)
        set_data = name["data"]["sets"][set_name]
        view_sets[i] = set_data
    return render_template("community.html",streak=streak,share_links=share_links,name=users_name,settings=settings,boosting=boosting,sets=make_dict(view_sets),notifications=notifications)

@app.route("/recommended")
def recommended():
    if login() == False:
        return render_template("login.html")
    recommended = recommend(db[username()]["sets"])
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
        return render_template("login.html")
    sets = list(db["sets"])
    for i in range(len(sets)):
        db[sets[i][0]]["sets"][sets[i][1]]["settings"]["subject"] = subject(sets[i][1])
    return redirect("/community")

@app.route("/publish/<name>")
def publish(name):
    if login() == False:
        return render_template("login.html")
    level = userinfo(username())[0]
    amount = 0
    sets_list = global_data_db.find_one({"name":"sets"})["data"]
    for i in sets_list:
        if username() in i:
            amount += 1
    if amount >= 2 and level == False:
        return "Max Amount"
    elif amount >= 3 and level == "boost":
        return "Max Amount"
    elif amount >= 5 and level == "pro":
        return "Max Amount"
    elif amount >= 10 and level == "premium":
        return "Max Amount"
    elif amount >= 20 and level == "elite":
        return "Max Amount"
    set = get_sets()[name]
    for i in range(1,len(set)):
        quest = set[f"Q{i}"]["question"]
        if mod(quest) == "1" or profanity.contains_profanity(quest):
            session["notifications"] = ["You Can't Publish This Set, Due To It Cointains Profanity Or Rude Text. (Question:"+str(i)+")"]
            return redirect("/")
        for j in set[f"Q{i}"]["answers"]:
            ans = set[f"Q{i}"]["answers"][j]
            if mod(ans) == "1" or profanity.contains_profanity(ans):
                session["notifications"] = ["You Can't Publish This Set, Due To It Cointains Profanity Or Rude Text. (Answer:"+str(i)+")"]
                return redirect("/")
    query = {"name":"sets"}
    update = {"$push": {"data": [username(),name]}}
    global_data_db.update_one(query, update)
    session["notifications"] = [f"Success! ✅ You Have Published: {name}"]
    return redirect("/community")

@app.route("/download/@<user_name>/<name>")
def download(user_name,name):
    if login() == False:
        return render_template("login.html")
    amount = 0
    if name in db[username()]["sets"].keys():
        for i in db[username()]["sets"].keys():
            if name in i:
                amount += 1
        name2 = f"{name} ({amount})"
    else:
        name2 = name
    db[username()]["sets"][name2] = db[user_name]["sets"][name]
    db[username()]["sets"][name2]["settings"]["folder"] = False
    for i in db[username()]["rules"]:
        which_subject = db[username()]["rules"][i]["subject"]
        folder = db[username()]["rules"][i]["folder"]
        if folder not in db[username()]["folders"]:
            del db[username()]["rules"][i]
        if subject(name) == which_subject and db[username()]["sets"][name2]["settings"]["folder"] == False:
            db[username()]["folders"][folder]["sets"].append(name2)
            db[username()]["sets"][name2]["settings"]["folder"] = True
    return redirect("/")

@app.route("/delete/@<user_name>/<name>")
def delete2(user_name,name):
    if login() == False:
        return render_template("login.html")
    if username() == user_name or "GoodVessel92551" == username():
        for i in db["sets"]:
            if user_name in i and name in i:
                db["sets"].remove(i)
    else:
        session["notifications"] = ["You Can Not Delete This Set. 🔒"]
        return redirect("/community")
    session["notifications"] = [f"Success! ✅ You Deleted This From The Community: {name}"]
    return redirect("/")

@app.route("/flashcards/@<username>/<name>")
def falshcards2(username,name):
    notifications = []
    settings = {"interface":{"theme":"green","cards":"straight"},"accessibility":{"fontSize":"normal","font":"roboto"}}
    return render_template("cards.html",streak=0,title=name,settings=settings,name="Guest",boosting=False,profile_pic="https://booogle-revise-2.goodvessel92551.repl.co/static/logo.png",sets=make_dict(db[username]["sets"])[name],notifications=notifications)

@app.route("/fill/@<username>/<name>")
def fills(username,name):
    notifications = []
    settings = {"interface":{"theme":"green","cards":"straight"},"accessibility":{"fontSize":"normal","font":"roboto"}}
    return render_template("fill.html",streak=0,title=name,name="Guest",settings=settings,boosting=False,profile_pic="https://booogle-revise-2.goodvessel92551.repl.co/static/logo.png",set=make_dict(db[username]["sets"])[name],notifications=notifications)

@app.route("/questions/@<username>/<name>",methods=["POST","GET"])
def questions(username,name):
    notifications = []
    settings = {"interface":{"theme":"green","cards":"straight"},"accessibility":{"fontSize":"normal","font":"roboto"}}
    set = make_dict(db[username]["sets"])[name]
    if request.method == "POST":
        current = session.get("current")
        if session.get("current")["current"] == len(session.get("current")["order"]):
            return render_template("finish.html",name="Guest",boosting=False,profile_pic="https://booogle-revise-2.goodvessel92551.repl.co/static/logo.png",notifications=notifications)
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
            if answer in answers:
                return render_template("correct.html",settings=settings,name="Guest",boosting=False,profile_pic="https://booogle-revise-2.goodvessel92551.repl.co/static/logo.png",answer=answer1,notifications=notifications)
            else:
                return render_template("wrong.html",settings=settings,name="Guest",boosting=False,profile_pic="https://booogle-revise-2.goodvessel92551.repl.co/static/logo.png",answer=answer1,notifications=notifications)
        else:
            session["next"] = "False"
    else:
        order = []
        for i in range(1,len(set)):
            order.append("Q"+str(i))
        random.shuffle(order)
        session["next"] = "False"
        session["current"] = {"current":0,"order":order}
    ans = []
    if session.get("current")["current"] == len(session.get("current")["order"]):
        return render_template("finish.html",settings=settings,name="Guest",boosting=False,profile_pic="https://booogle-revise-2.goodvessel92551.repl.co/static/logo.png",notifications=notifications)
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
    return render_template("question.html",streak=0,title=name,settings=settings,name="Guest",boosting=False,profile_pic="https://booogle-revise-2.goodvessel92551.repl.co/static/logo.png",sets=make_dict(db[username]["sets"])[name],ans=ans,question=question,notifications=notifications,owner=username,total_quests=len(current["order"]),set=name,quest_num = current["order"][current["current"]])

@app.route("/new/folder",methods=["POST","GET"])
def new_folder():
    if login() == False:
        return render_template("login.html")
    notifications = []
    if request.method == "POST":
        title = emoji.demojize(request.form["title"]).strip()
        desc = request.form["desc"]
        cover = request.form["cover"]
        try:
            db[username()]["folders"]
        except:
            db[username()]["folders"] = {}
        else:
            if title in list(db[username()]["folders"]):
                session["notifications"] = ["📂 You already have a folder with that name!"]
                return redirect("/")
            else:
                db[username()]["folders"][title] = {
                    "name":title,
                    "desc":desc,
                    "background":cover,
                    "sets":[]
                }
            return redirect("/")
    return render_template("new_folder.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/folder/<folder>",methods=["POST","GET"])
def folder(folder):
    if login() == False:
        return render_template("login.html")
    notifications = []
    sets = {}
    names = db[username()]["folders"][folder]["sets"]
    for i in names:
        sets[i] = db[username()]["sets"][i]
    return render_template("folder.html",sets=make_dict(sets),name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications,title=db[username()]["folders"][folder]["name"])

@app.route("/add/folder/<folder>")
def add_folder(folder):
    if login() == False:
        return render_template("login.html")
    notifications = []
    sets = get_sets()
    return render_template("folder_add.html",sets=sets,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications,folder_title=db[username()]["folders"][folder]["name"])

@app.route("/edit/folder/<folder>",methods=["POST","GET"])
def edit_folder(folder):
    if login() == False:
        return render_template("login.html")
    notifications = []
    sets = {}
    if request.method == "POST":
        old_folder = db[username()]["folders"][folder]
        del db[username()]["folders"][folder]
        title = emoji.demojize(request.form["title"]).strip()
        desc = request.form["desc"]
        cover = request.form["cover"]
        db[username()]["folders"][title] = {
            "name":title,
            "desc":desc,
            "background":cover,
            "sets":old_folder["sets"]
        }
        return redirect("/folder/"+title)
    else:
        names = db[username()]["folders"][folder]["sets"]
        for i in names:
            sets[i] = db[username()]["sets"][i]
    return render_template("edit_folder.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications,folder=make_dict_folder(db[username()]["folders"])[folder])

@app.route("/remove/folder/<folder>")
def remove_folder(folder):
    if login() == False:
        return render_template("login.html")
    for i in db[username()]["folders"][folder]["sets"]:
        db[username()]["sets"][i]["settings"]["folder"] = False
    del db[username()]["folders"][folder]
    return redirect("/")

@app.route("/remove/folder/<folder>/<name>")
def remove_folder_sey(folder,name):
    if login() == False:
        return render_template("login.html")
    db[username()]["folders"][folder]["sets"].remove(name)
    db[username()]["sets"][name]["settings"]["folder"] = False
    return redirect("/folder/"+folder)
    
@app.route("/add/folder/<folder>/<name>")
def add_folder_set(folder,name):
    if login() == False:
        return render_template("login.html")
    if name in list(db[username()]["folders"][folder]["sets"]):
        return "Error"
    else:
        db[username()]["folders"][folder]["sets"].append(name)
        db[username()]["sets"][name]["settings"]["folder"] = True
        return redirect("/folder/"+folder)

@app.route("/new",methods=["POST","GET"])
def new():
    if login() == False:
        return render_template("login.html")
    notifications = []
    level = userinfo(username())[0]
    if request.method == "POST":
        premium = ["pro","art","bike","elite","car","castle","code","hill","map","flask"]
        pro = ["elite","car","castle","code","hill","map","flask"]
        elite = ["boost","premium","pro","art","bike","elite","car","castle","code","hill","map","flask"]
        title = emoji.demojize(request.form["title"]).strip()
        desc = request.form["desc"]
        cover = request.form["cover"]
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
            session["notifications"] = ["This Set Already Exists."]
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
                    "folder":False
                }
            }
            user_data_db.update_one({"username":username(),"type":"user_data"},{"$set":{"data.sets."+title:new_set}})
            session["current_set"] = title
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
        return render_template("new.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),title=title,desc=desc,background=background,notifications=notifications)

@app.route("/new/question",methods=["POST","GET"])
def new_question():
    if login() == False:
        return render_template("login.html")
    notifications = []
    if request.method == "POST":
        level = userinfo(username())[0]
        quest = request.form["quest"]
        ans = request.form["ans1"]
        image_url = request.form["image_url"]
        pattern = re.compile(r'\.(jpg|jpeg|png|gif|bmp|svg|tiff)$', re.IGNORECASE)
        type = smart(ans)
        quest_num =str(len(get_sets()[session.get("current_set")]))
        new_quest = {"status":mod(quest),"question":quest,"answers":{"ans1":ans},"type":type}
        if bool(pattern.search(image_url)):
            image_data = check_image(image_url)
            if "rating_label" in image_data:
                if image_data["rating_label"] != "adult":
                    new_quest["image"] = {"url":image_url,"rating":image_data["rating_label"]}
        user_data_db.update_one({"username":username(),"type":"user_data"},{"$set":{"data.sets."+session.get("current_set")+".Q"+quest_num:new_quest}})
        if request.form["button"] == "finish":
            session.pop("current_set")
            return redirect("/")
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
    return render_template("new_question.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),quest=quest,ans=ans,rude=rude,len=length,notifications=notifications)

@app.route("/new/question/generate",methods=["POST","GET"])
def generate():
    if login() == False:
        return render_template("login.html")
    if request.method == "POST":
        level = userinfo(username())[0]
        quest = request.form["quest"]
        
        if level == "pro" or level == "elite":
            if len(quest.split()) < 3:
                session["quest_len"] = quest
            elif mod(quest) != "1" and profanity.contains_profanity(quest) == False:
                co = cohere.Client(os.getenv('AI_key'))
                try:
                    response = co.generate(
                        model='command-xlarge-beta',
                        prompt='You are Booogle Revise AI and you are a AI assistant, Answer this: \"'+quest+'\" as concise as possible',
                        max_tokens=100,
                        temperature=0.5,
                        k=0,
                        p=0.75,
                        stop_sequences=[],
                        return_likelihoods='NONE'
                    )
                except:
                    ans = "There Was An Error"
                else:
                    ans = response.generations[0].text.lstrip()
                session["quest"] = {"quest":quest,"ans":ans}
            else:
                session["quest_rude"] = quest
        else:
            session["quest"] = {"quest":quest,"ans":""}
    return redirect("/new/question")

@app.route("/edit/<name>",methods=["POST","GET"])
def edit(name):
    if login() == False:
        return render_template("login.html")
    notifications = []
    if request.method == "POST":
        for i in range(len(list(db["sets"]))):
            if name in db["sets"][i] and username() in db["sets"][i]:
                db["sets"][i] = [username(),emoji.demojize(request.form["title"])]
        what_user = db[username()]["sets"][name]["settings"]["user"]
        if what_user == username():
            what_level = userinfo(username())[0]
        else:
            what_level = db[username()]["sets"][name]["settings"]["level"]
        try:
            folder = db[username()]["sets"][name]["settings"]["folder"]
        except:
            folder = False
        set = db[username()]["sets"][name]
        del db[username()]["sets"][name]
        db[username()]["sets"][emoji.demojize(request.form["title"])]  = {
            "settings":{
                "name":emoji.demojize(request.form["title"]),
                "desc":request.form["desc"],
                "public":False,
                "background":request.form["cover"],
                "user":what_user,
                "level":what_level,
                "folder":folder,
                "subject":subject(emoji.demojize(request.form["title"]))
            }
        }
        if folder == True:
            for i in db[username()]["folders"].keys():
                if set in db[username()]["folders"][i]["sets"]:
                    db[username()]["folders"][i]["sets"].remove(set)
                    db[username()]["folders"][i]["sets"].append(emoji.demojize(request.form["title"]))
        level = userinfo(username())[0]
        for i in range(1,len(list(request.form)[3:])):
            if (len(db[username()]["sets"][emoji.demojize(request.form["title"])]) >= 15 and (level == False or level == "boost")) or (len(db[username()]["sets"][emoji.demojize(request.form["title"])]) >= 20 and level == "premium") or (len(db[username()]["sets"][emoji.demojize(request.form["title"])]) >= 25 and level == "pro") or (len(db[username()]["sets"][emoji.demojize(request.form["title"])]) >= 35 and level == "elite"):
                session["notifications"] = ["Max Amount Of Questions."]
                return redirect("/")
            else:
                try:
                    quest = request.form[f"Q{i}"]

                except:
                    break
                else:
                    quest_profanity = profanity.contains_profanity(quest)
                    db[username()]["sets"][emoji.demojize(request.form["title"])][f"Q{i}"] = {"status":mod(quest),"question":quest,"answers":{"ans1":request.form[f"A{i}"]}}
                    db[username()]["sets"][emoji.demojize(request.form["title"])][f"Q{i}"]["type"] = smart(request.form[f"A{i}"])
                    image_url = request.form[f"img{i}"]
                    pattern = re.compile(r'\.(jpg|jpeg|png|gif|bmp|svg|tiff)$', re.IGNORECASE)
                    if bool(pattern.search(image_url)):
                        image_data = check_image(image_url)
                        if "rating_label" in image_data:
                            if image_data["rating_label"] != "adult":
                                db[username()]["sets"][emoji.demojize(request.form["title"])][f"Q{i}"]["image"] = {"url":image_url,"rating":image_data["rating_label"]}
                    if quest_profanity:
                        db[username()]["sets"][emoji.demojize(request.form["title"])][f"Q{i}"]["status"] = mod(quest)        
        session["notifications"] = [f"Success! ✅ You Have Edited: {name}"]
        return redirect("/")
    return render_template("edit.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),sets=get_sets()[name],notifications=notifications)

@app.route("/sw.js", methods=["GET"])
def sw():
    return current_app.send_static_file("sw.js")

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
    return "Ofline"

@app.route("/flashcards/<name>")
def flashcards(name):
    if login() == False:
        return render_template("login.html")
    notifications = []
    add_streak()
    return render_template("cards.html",title=name,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),sets=get_sets()[name],notifications=notifications)

@app.route("/questions/<name>",methods=["POST","GET"])
def question(name):
    if login() == False:
        return render_template("login.html")
    notifications = []
    set = get_sets()[name]
    if request.method == "POST":
        current = session.get("current")
        if session.get("current")["current"] == len(session.get("current")["order"]):
            return render_template("finish.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications,stats=session["stats"])
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
                session["stats"][str(current["current"]+1)] = {"quest":quest,"correct":True}
                return render_template("correct.html",title=name,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),answer=answer1,notifications=notifications)
            else:
                session["stats"][str(current["current"]+1)] = {"quest":quest,"correct":False}
                return render_template("wrong.html",title=name,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),answer=answer1,notifications=notifications)
        else:
            session["next"] = "False"
    else:
        if len(set) < 4:
            session["notifications"] = ["You Need More Questions"]
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
        return render_template("finish.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications,stats=session["stats"])
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
    return render_template("question.html",title=name,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),sets=get_sets()[name],ans=ans,question=question,notifications=notifications,quest_num = current["order"][current["current"]],set=name,total_quests=len(current["order"]),owner=username())

@app.route("/api/questions",methods=["POST","GET"])
def api_quest_ans():
    correct = False
    data = request.get_json()
    print(data)
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
    return render_template("finish.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=[],stats=session["stats"])

@app.route("/delete/<name>")
def delete(name):
    if login() == False:
        return render_template("login.html")
    for i in db["sets"]:
        if name in i and username() in i:
            db["sets"].remove(i)
    del db[username()]["sets"][name] 
    session["notifications"] = [f"Success! ✅ You Have Deleted: {name}"]
    return redirect("/")

@app.route("/api/account/<api_key>/<id>/<name>",methods=["GET"])
def add_account(api_key,id,name):
    r = requests.get(f"https://Booogle-API.goodvessel92551.repl.co/api/{os.getenv('key')}/{id}/{name}")
    if name in db["users"]:
        return "User Exsits"
    if api_key == r.json()["token"]:
        db["users"].append(name)
        db[name] = {}
        db[name]["sets"] = {}
        db[name]["level"] = ""
        db[name]["folders"] = {}
        last_7_days = last_7()
        db[name]["stats"] = {"last_7":{}}
        for i in last_7_days:
            db[name]["stats"]["last_7"][i] = {"sets":0}
        db[name]["stats"]["total"] = {"sets":0,"published":0,"made":0}
        return "Success"
    else:
        return "Invalid API Key"

@app.route("/api/<api_key>/<id>/<name>",methods=["GET"])
def api(api_key,id,name):
    if name not in db["users"]:
        return "No User"
    else:
        r = requests.get(f"https://Booogle-API.goodvessel92551.repl.co/api/{os.getenv('key')}/{id}/{name}")
        if api_key == r.json()["token"]:
            sets = db[name]["sets"]
            return make_dict(sets)
        else:
            return "Invalid API Key"

@app.route("/api/delete/<api_key>/<id>/<name>/<set_name>",methods=["GET"])
def api_del(api_key,id,name,set_name):
    r = requests.get(f"https://Booogle-API.goodvessel92551.repl.co/api/{os.getenv('key')}/{id}/{name}")
    if api_key == r.json()["token"]:
        del db[name]["sets"][set_name]
        return "Done"
    else:
        return "Invalid API Key"

@app.route("/api/new/<api_key>/<id>/<name>/<set_name>/<set_desc>/<cover_img>",methods=["GET"])
def api_new(api_key,id,name,set_name,set_desc,cover_img):
    r = requests.get(f"https://Booogle-API.goodvessel92551.repl.co/api/{os.getenv('key')}/{id}/{name}")
    if api_key == r.json()["token"]:
        level = db[name]["level"]
        if set_name in list(db[name]["sets"]):
            return "Do not repeat set names"
        elif (len(db[name]["sets"]) >= 10 and (level != "premium" and level != "pro" and level != "elite")) or (len(db[name]["sets"]) >= 20 and level == "premium") or (len(db[name]["sets"]) >= 20 and level == "pro") or (len(db[name]["sets"]) >= 20 and level == "elite"):
            return "You Have Reached The Max Amount Of Sets."
        elif len(set_name) > 80 or len(set_name) == 0 or len(set_desc) > 150 or len(set_desc) == 0:
            return "Error"
        db[name]["sets"][emoji.demojize(set_name)] = {
            "settings":{
                "name":set_name,
                "desc":set_desc,
                "public":False,
                "background":cover_img,
                "user":name,
                "level":"booogle"
            }
        }
        return "Done"
    else:
        return "Invalid API Key"

@app.route("/api/new_quest/<api_key>/<id>/<name>/<set_name>/<quest>/<ans>",methods=["GET"])
def api_quest(api_key,id,name,set_name,quest,ans):
    r = requests.get(f"https://Booogle-API.goodvessel92551.repl.co/api/{os.getenv('key')}/{id}/{name}")
    if api_key == r.json()["token"]:
        type = smart(ans)
        db[name]["sets"][emoji.demojize(set_name)]["Q"+str(len(db[name]["sets"][emoji.demojize(set_name)]))] = {"status":mod(quest),"question":quest,"answers":{"ans1":ans},"type":type}
        return "Done"
    else:
        return "Invalid API Key"


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
        return render_template("login.html")
    notifications = []
    return render_template("finish_flash.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/fill/<name>")
def fill(name):
    if login() == False:
        return render_template("login.html")
    notifications = []
    add_streak()
    return render_template("fill.html",title=name,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),set=get_sets()[name],notifications=notifications)

@app.errorhandler(500)
def server_error(e):
    session["notifications"] = ["There Was An Error 😭 Please Try Again Later"]
    return redirect("/")
    #return render_template('500.html'), 500

@app.errorhandler(404)
def page_not_found(e):
    session["notifications"] = ["The Page That You Were Looking For Does Not Exist Here 😭"]
    return redirect("/")
    #return render_template('404.html'), 404

@app.route("/stats/@<user>")
def stats(user):
    db[user]["stats"] = update(db[user]["stats"])
    return render_template("stats.html",stats=stats_dict(update(db[user]["stats"])))

@app.route("/leaderboard")
def leaderboard():
    users = db["users"]
    leaderboard = {}
    for i in users:
        try:
            current_user = db[i]["stats"]["total"]["sets"]
        except:
            db[i]["stats"] = {"last_7":{}}
            last_7_days = last_7()
            for j in last_7_days:
                db[i]["stats"]["last_7"][j] = {"sets":0}
            db[i]["stats"]["total"] = {"sets":0,"published":0,"made":0}
        current_user = db[i]["stats"]["total"]["sets"]
        leaderboard[i] = current_user
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda item: item[1])
    sorted_leaderboard.reverse()
    return render_template("leaderboard.html",leaderboard=sorted_leaderboard[0:10])

@app.route("/ai/revise")
def ai_revise():
    if login() == False:
        return render_template("login.html")
    notifications = []
    return render_template("ai_revise.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/ai/revise/generate",methods=["POST","GET"])
def ai_revise_generate():
    data = request.get_json()
    url = request.referrer
    parsed_url = urlparse(url)
    subdomain_list = parsed_url.hostname.split('.')
    subdomain = subdomain_list[-3] + "." + subdomain_list[-2] + "." + subdomain_list[-1]
    if subdomain != "goodvessel92551.repl.co":
        {"error": "You cannot come from that domain."}
    prompt = data['prompt']
    messages = data["messages"]
    topic = messages[0]
    messages.remove(topic)
    ans = True
    if len(messages)%2 == 0:
        ans = False
    if ans == True:
        prompt = f"You are Booogle Revise AI and you are a AI assistant, Is this question right? {messages[-1]}. Also give me another revision question on the topic: {topic}. Make sure to do this."
    else:
        prompt = f"You are Booogle Revise AI and you are a AI assistant, Give me a {topic}'s revision question."
    co = cohere.Client(os.getenv('AI_key'))
    response = co.generate(
        model='command-xlarge-beta',
        prompt=prompt,
        max_tokens=100,
        temperature=0.8,
        k=0,
        p=0.75,
        stop_sequences=[],
        return_likelihoods='NONE'
    )
    ans = ans = response.generations[0].text.lstrip()
    return {"ans":ans}

@app.route("/test/<set>",methods=["POST","GET"])
def test_mode(set):
    if login() == False:
        return render_template("login.html")
    notifications = []
    questions = []
    quest_set = {}
    if db[username()]["level"] != "elite":
        session["notifications"] = ["🔐 You Are Not Elite "]
        return redirect("/")
    if request.method == "POST":
        for i in range(1,len(db[username()]["sets"][set])):
            ans = request.form[f"Q{i}"]
            quest = db[username()]["sets"][set][f"Q{i}"]["question"]
            similarity_num = similarity(ans.lower(),db[username()]["sets"][set][f"Q{i}"]["answers"]["ans1"].lower())
            if similarity_num > 0.8:
                session["stats"][str(i)] = {"quest":quest,"correct":True}
            else:
                session["stats"][str(i)] = {"quest":quest,"correct":False}
        return render_template("finish.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications,stats=session["stats"])
    else:
        for i in range(1,len(db[username()]["sets"][set])):
            questions = []
            for j in range(1,len(db[username()]["sets"][set])):
                questions.append(f"Q{j}")
            quest_set[f"Q{i}"] = {
                "question":db[username()]["sets"][set][f"Q{i}"]["question"],
                "type":None,
                "answer":None
            }
            quest = db[username()]["sets"][set][f"Q{i}"]
            if len(quest["answers"]["ans1"].split()) < 10 and random.randint(0,2) == 0:
                quest_set[f"Q{i}"]["type"] = "text"
                quest_set[f"Q{i}"]["answer"] = quest["answers"]["ans1"]
            else:
                answers = [quest["answers"]["ans1"]]
                temp = questions
                temp.remove(f"Q{i}")
                for j in range(1,len(db[username()]["sets"][set])):
                    ans = db[username()]["sets"][set][f"Q{j}"]
                    if ans["type"] == quest["type"] and ans["answers"]["ans1"] != quest["answers"]["ans1"]:
                        answers.append(ans["answers"]["ans1"])
                    if len(answers) == 3:
                        break
                
                if len(answers) != 3:
                    while len(answers) != 3:
                        random_ans = random.choice(temp)
                        answers.append(db[username()]["sets"][set][random_ans]["answers"]["ans1"])
                        temp.remove(random_ans)
                random.shuffle(answers)
                quest_set[f"Q{i}"]["type"] = "multi"
                quest_set[f"Q{i}"]["answer"] = answers
            if session.get("stats"):
                session.pop("stats")
            session["stats"] = {}
    return render_template("test_mode.html",title=set,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),set=get_sets()[set],notifications=notifications,quest_set=quest_set)

@app.route("/play", methods=["POST","GET"])
def play():
    if login() == False:
        return render_template("login.html")
    if request.method == "POST":
        code = request.form["code"]
        try:
            db["play"][code]
        except:
            session["notifications"] = [f"🔑 {code} Is Not A valid Key, Please Try Again"]
            return redirect("/play")
        else:
            return redirect(f"/play/{code}")
    if session.get("notifications"):
        notifications = session.get("notifications")
        session.pop("notifications")
    else:
        notifications = []
    return render_template("play.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/play/stats/<code>")
def play_sets(code):
    if login() == False:
        return render_template("login.html")
    notifications = []
    return render_template("play_stats.html",code=code,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/play/<code>")
def play_code(code):
    if login() == False:
        return render_template("login.html")
    notifications = []
    players = len(db["play"][code]["users"])
    level = userinfo(username())[0]
    if (players >= 3 and (level == False or level == "boost")) or (players >= 5 and level == "premium") or (players >= 10 and level == "pro") or (players >= 15 and level == "elite"):
        session["notifications"] = ["👥 There Are No More Spaces For More Players"]
        return redirect("/")
    if code not in list(db["play"]):
        session["notifications"] = ["🗝️ Please Enter A Valid Code"]
        return redirect("/play")
    db["play"][code]["users"][username()] = {
        "score":{},
        "user_image":userinfo(username())[1]
    }
    return render_template("play_hub.html",code=code,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/play/leave/<code>")
def leave_code(code):
    if login() == False:
        return render_template("login.html")
    db["play"][code]["users"].pop(username())
    return redirect("/")

@app.route("/host")
def host():
    if login() == False:
        return render_template("login.html")
    notifications = []
    for i in db["play"]:
        if db["play"][i]["host"] == username():
            del db["play"][i]
    code = random.randint(100000,999999)
    return render_template("host.html",code=code,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications,sets=get_sets())


@app.route("/play/host/<code>/<set>")
def play_host(code,set):
    if login() == False:
        return render_template("login.html")
    notifications = []
    db["play"][code] = {
        "host":username(),
        "users":{},
        "started":False,
        "set":set
    }
    return render_template("play_host.html",code=code,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/play/start/<code>")
def play_start(code):
    if login() == False:
        return render_template("login.html")
    notifications = []
    if db["play"][code]["host"] == username():
        db["play"][code]["started"] = True
        return render_template("play_start.html",quests=len(db[db["play"][code]["host"]]["sets"][db["play"][code]["set"]]),users=play_dict(db["play"][code]["users"]),code=code,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)
    else:
        return redirect(f"/play/{code}")

@app.route("/play/started/<code>",methods=["POST","GET"])
def play_started(code):
    if login() == False:
        return render_template("login.html")
    name = db["play"][code]["set"]
    host = db["play"][code]["host"]
    notifications = []
    set = make_dict(db[host]["sets"])[name]
    if request.method == "POST":
        current = session.get("current")
        if session.get("current")["current"] == len(session.get("current")["order"]):
            return render_template("play_finish.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications,stats=session["stats"])
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
                db["play"][code]["users"][username()]["score"][str(current["current"]+1)] = {"quest":quest,"correct":True}
                return render_template("correct.html",title=name,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),answer=answer1,notifications=notifications)
            else:
                db["play"][code]["users"][username()]["score"][str(current["current"]+1)] = {"quest":quest,"correct":False}
                return render_template("wrong.html",title=name,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),answer=answer1,notifications=notifications)
        else:
            session["next"] = "False"
    else:
        if len(set) < 4:
            session["notifications"] = ["You Need More Questions"]
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
        return render_template("play_finish.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications,stats=session["stats"])
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
    return render_template("question.html",title=name,name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),sets=make_dict(db[host]["sets"])[name],ans=ans,question=question,notifications=notifications)

@app.route("/play/end/<code>")
def play_end(code):
    if login() == False:
        return render_template("login.html")
    if username() == db["play"][code]["host"]:
        del db["play"][code]
    else:
        session["notifications"] = ["🔐 You Are Not The Host"]
        return redirect("/")
    return redirect("/")

@app.route("/api/play/started/<code>")
def play_started_api(code):
    if login() == False:
        return render_template("login.html")
    started = {"started":db["play"][code]["started"]}
    return started

@app.route("/api/play/leaderboard/<code>")
def play_leaderboard_api(code):
    if login() == False:
        return render_template("login.html")
    leaderboard = play_dict(db["play"][code]["users"])
    return leaderboard

@app.route("/automations",methods=["GET","POST"])
def automations():
    if login() == False:
        return render_template("login.html")
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
                        session["notifications"] = ["🤖 Automation Already Exists For Subject"]
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
    
@app.route("/test")
def test():
    print(db[username()])
    print(login())
    print(username())
    return redirect("/")

@app.route("/login/code",methods=["GET","POST"])
def code():
    if request.method == "POST":
        for i in db["codes"]:
            if db["codes"][i] == request.form["code"]:
                session["Code"] = request.form["code"]
    return redirect("/")

    
@app.route("/code")
def user_code():
    if login() == False:
        return render_template("login.html")
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
        return render_template("login.html")
    notifications = []
    return render_template("schedule.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/teach")
def teach():
    if login() == False:
        return render_template("login.html")
    notifications = []
    return render_template("teach/teach.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/teach/classroom/<id>")
def classroom(id):
    if login() == False:
        return render_template("login.html")
    notifications = []
    return render_template("teach/classroom.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/new/group",methods=["GET","POST"])
def new_group():
    if login() == False:
        return render_template("login.html")
    if request.method == "POST":
        title = request.form["title"]
        desc = request.form["desc"]
        cover = request.form["cover"]
        id = gen_id()
        print(id)
        group = {
            "sets":[],
            "users":[username()],
            "settings":{
                "Title":title,
                "Desc":desc,
                "Cover":cover,
                "Owner":username(),
                "upload_own":False
            }
        }
        db[username()]["groups"][title] = group
        return redirect("/")
    notifications = []
    return render_template("groups/new_group.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/edit/group/<group>")
def edit_group(group):
    if login() == False:
        return render_template("login.html")
    group_info = make_dict_group(db[username()]["groups"][group])
    notifications = []
    return render_template("groups/edit_group.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),group_info=group_info,notifications=notifications)

@app.route("/group/<group>",methods=["POST","GET"])
def group(group):
    if login() == False:
        return render_template("login.html")
    if session.get("notifications"):
        notifications = session.get("notifications")
        session.pop("notifications")
    else:
        notifications = []
    if request.method == "POST":
        add_username = request.form["username"]
        if add_username not in db["users"]:
            session["notifications"] = ["Unable To Find User"]
        elif add_username in db[username()]["groups"][group]["users"]:
            session["notifications"] = ["User Is Already In Group"]
        else:
            try:
                db[username()]["groups"]
                db[add_username]["added_groups"]
            except:
                db[add_username]["groups"] = {}
                db[add_username]["added_groups"] = []
            db[add_username]["added_groups"].append([username(),group])
            db[username()]["groups"][group]["users"].append(add_username)
            session["notifications"] = ["User Added To The Group"]
        return redirect("/group/"+group)
    else:
        sets = {}
        if group in list(db[username()]["groups"]):
            names = db[username()]["groups"][group]["sets"]
            owner = db[username()]["groups"][group]["settings"]["Owner"]
        else:
            for i in db[username()]["added_groups"]:
                if i[1] == group:
                    names = db[i[0]]["groups"][group]["sets"]
                    owner = db[i[0]]["groups"][group]["settings"]["Owner"]
        for i in names:
            sets[i] = db[owner]["sets"][i]
        user_data = user_data_group(list(db[owner]["groups"][group]["users"]))
        return render_template("groups/group.html",user_data=user_data,sets=make_dict(sets),name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications,title=group,owner=owner)
    
@app.route("/add/group/<group>/<name>")
def add_group_set(group,name):
    if login() == False:
        return render_template("login.html")
    if name in list(db[username()]["groups"][group]["sets"]):
        return "Error"
    else:
        db[username()]["groups"][group]["sets"].append(name)
        return redirect("/group/"+group)
        
@app.route("/remove/group/<group>")
def remove_group(group):
    if login() == False:
        return render_template("login.html")
    del db[username()]["groups"][group]
    return redirect("/")

@app.route("/remove/group/<group>/<name>")
def remove_group_user(group,name):
    if login() == False:
        return render_template("login.html")
    owner = db[username()]["groups"][group]["settings"]["Owner"]
    db[owner]["groups"][group]["users"].remove(name)
    for i in range(len(db[name]["added_groups"])):
        print(i)
        if owner in db[name]["added_groups"][i] and group in db[name]["added_groups"][i]:
            db[name]["added_groups"].pop(i)
    return redirect("/group/"+group)

@app.route("/api/smartsubject",methods=["POST","GET"])
def api_smartsubject():
    data = request.get_json()
    return {"subject":subject(data["text"])}

@app.route("/settings",methods=["POST","GET"])
def settings():
    if login() == False:
        return render_template("login.html")
    notifications = {}
    if request.method == "POST":
        theme = request.form["theme"]
        db[username()]["settings"]["interface"]["theme"] = theme
    return render_template("settings/settings.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/community/rate/@<usersname>/<set_name>")
def rate(usersname,set_name):
    if login() == False:
        return render_template("login.html")
    notifications = {}
    return render_template("rate.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/focus")
def focuse():
    if login() == False:
        return render_template("login.html")
    notifications = {}
    return render_template("focus.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

@app.route("/features")
def about():
    return render_template("about.html")

@app.route("/streaks")
def streaks():
    if login() == False:
        return redner_template("login.html")
    notifications = {}
    return render_template("focus.html",name=username(),streak=get_streak(),settings=get_settings(),boosting=userinfo(username()),notifications=notifications)

app.run(host="0.0.0.0",port=8080,debug=True)