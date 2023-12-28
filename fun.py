import requests,os,json,random,re
from better_profanity import profanity
from booogle_ai_tools.moderation import moderation
from booogle_ai_tools.smartmatch import smartmatch
from booogle_ai_tools.smartsubject import smartsubject
import datetime,time
from datetime import datetime
from Levenshtein import distance
from collections import Counter
from flask import session
from pymongo import MongoClient
from dotenv import load_dotenv
import hashlib

load_dotenv()
client = MongoClient("mongodb+srv://GoodVessel92551:Gzw9KNoZEwhgIkpq@booogle.j0arbkm.mongodb.net/?retryWrites=true&w=majority")
db = client["Booogle_Revise"]
global_data_db = db["Global_Data"]
user_data_db = db["User_Data"]

def get_sets():
    sets = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["sets"]
    return sets

def get_streak():
    streak = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["streak"]["streak"]
    return streak

def get_settings():
    settings = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["settings"]
    return settings

def get_folders():
    folders = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["folders"]
    return folders

def hash_value(data):
    sha256 = hashlib.sha256()
    sha256.update(str(data).encode('utf-8'))
    return sha256.hexdigest()

def gen_user_token():
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    token = ""
    for i in range(20):
        token += random.choice(chars)
    return token

def streak():
    current_streak = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["streak"]
    print(current_streak)
    current_time = datetime.now()
    time_difference = current_time - datetime.strptime(current_streak["time"], "%Y-%m-%d %H:%M:%S.%f")
    if current_streak["time"] == 0:
        current_streak["streak"] = 0
        current_streak["time"] = str(current_time)
    elif time_difference.seconds/3600 > 24:
        current_streak["streak"] = 0
        current_streak["time"] = str(current_time)
    query = {"name":username(),"type":"user_data"}
    new_value = {"$set":{"data.streak":current_streak}}
    user_data_db.update_one(query,new_value)
    return

def add_streak():
    streak()
    current_streak = user_data_db.find_one({"username":username(),"type":"user_data"})["data"]["streak"]
    old_time = datetime.strptime(str(current_streak["time"]), "%Y-%m-%d %H:%M:%S.%f")
    current = datetime.now()
    new_streak = current_streak
    if old_time.year == current.year and old_time.month == current.month and old_time.day == current.day:
        new_streak["time"] = str(current)
    else:
        new_streak["streak"] += 1
        new_streak["time"] = str(current)
    query = {"name":username(),"type":"user_data"}
    new_value = {"$set":{"data.streak":new_streak}}
    user_data_db.update_one(query,new_value)

def login():
    if session.get("token"):
        keys = global_data_db.find_one({"name":"B-KEYS"})
        print(keys["data"])
        print(session.get("token"))
        print(hash_value(session.get("token")))
        if str(hash_value(session.get("token"))) in keys["data"]:
            return True
    return False

def username():
    keys = global_data_db.find_one({"name":"B-KEYS"})
    username = keys["data"][str(hash_value(session.get("token")))]
    return username

def recommend(sets):
    subjects = Counter()
    recommended = []
    for i in sets:
        try:
            subjects[sets[i]["settings"]["subject"]] += 1
        except KeyError:
            sets[i]["settings"]["subject"] = subject(i)
            subjects[sets[i]["settings"]["subject"]] += 1
    subjects = dict(sorted(subjects.items(), key=lambda x: x[1], reverse=True))
    for i in db["sets"]:
        for j in range(len(subjects)):
            set_subject = db[i[0]]["sets"][i[1]]["settings"]["subject"]
            if i[0] != username() and i[1] not in sets and set_subject != "Other":
                if set_subject == list(subjects.keys())[j]:
                    recommended.append([i[0], i[1]])
    return recommended


def sort_dict(dictionary):
    sorted_items = sorted(dictionary.items(), key=lambda x: x[1], reverse=True)
    sorted_dict = {k: v for k, v in sorted_items}
    return sorted_dict

def similarity(str1, str2):
    if str1 in str2:
        num = 1
    else:
        num = 1 - (distance(str1, str2) / max(len(str1), len(str2)))
    if len(str2.split()) >= 5 and num > 0.5:
        return 1
    else:
        return num

def stats_dict(dictionary):
    dictionary = dict(dictionary)
    list_keys = list(dictionary)
    for i in list_keys:
        dictionary[i] = dict(dictionary[i])
        if i == "last_7":
            list_keys_2 = list(dictionary[i])
            for j in list_keys_2:
                dictionary[i][j] = dict(dictionary[i][j])
    return dictionary

def play_dict(dictionary):
    dictionary = dict(dictionary)
    list_keys = list(dictionary)
    for i in list_keys:
        dictionary[i] = dict(dictionary[i])
        dictionary[i]["score"] = dict(dictionary[i]["score"])
        if dictionary[i]["score"] != {}:
            for j in list(dictionary[i]["score"]):
                dictionary[i]["score"][j] = dict(dictionary[i]["score"][j])
    return dictionary

def leaderboard_dict(dictionary):
    dictionary = dict(dictionary)
    list_keys = list(dictionary)
    for i in list_keys:
        dictionary[i] = dict(dictionary[i])
        list_keys_2 = list(dictionary[i])
        for j in list_keys_2:
            dictionary[i][j] = dict(dictionary[i][j])
            list_keys_3 = list(dictionary[i][j])
            for k in list_keys_3:
                dictionary[i][j][k] = dict(dictionary[i][j][k])
    return dictionary

#def gen(prompt):
    #return generation.prompt(prompt)

def smart(text):
    return smartmatch.text(text)

def subject(text):
    return smartsubject.text(text)

def mod(text):
    ans = moderation.prompt(text)
    if "?" not in text and ans == "2":
        ans = 0
    if profanity.contains_profanity(text):
        ans = 1
    return ans


def last_7():
    today = datetime.date.today()
    last_7_days = []
    for i in range(7):
        day = today - datetime.timedelta(days=i)
        last_7_days.append(str(day))
    return last_7_days

def ago_7():
    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=8)
    return str(week_ago)

def current_date():
    return str(datetime.date.today())

def update(stats):
    days = list(stats["last_7"])
    last_7_days = last_7()
    nums = []
    dates = []
    for i in last_7_days:
        if i in days:
            nums.append([i,stats["last_7"][i]["sets"]])
            dates.append(i)
    stats["last_7"] = {}
    for i in last_7_days:
        if i in dates:
            for j in range(len(nums)):
                if nums[j][0] == i:
                    stats["last_7"][i] = {"sets":nums[j][1]}
        else:
            stats["last_7"][i] = {"sets":0}
    return stats

def week_add(stats):
    current = current_date()
    update(stats)
    stats["last_7"][current]["sets"] += 1
    return stats

def make_dict_rules(dictionary):
    list = dict(dictionary)
    for i in list:
        list[i] = dict(dictionary[i])
    return list

def make_dict_folder(dictionary):
    list = dict(dictionary)
    for i in list:
        list[i] = dict(dictionary[i])
        list[i]["sets"] = dictionary[i]["sets"][0:]
    return list

def rule_id():
    return random.randint(10000,99999)

def gen_id():
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    id = ""
    for i in range(10):
        id += random.choice(chars)
    id += str(time.time())
    print(id)
    return id

def make_dict(dictionary):
    list = dict(dictionary)
    for i in list:
        list[i] = dict(dictionary[i])
        for j in list[i]:
            if j == "sets" or j == "users":
                list[i][j] = dictionary[i][j][0:]
            else:
                list[i][j] = dict(dictionary[i][j])
                if "answers" in list[i][j].keys():
                    list[i][j]["answers"] = dict(dictionary[i][j]["answers"])
                if "image" in list[i][j].keys():
                    list[i][j]["image"] = dict(dictionary[i][j]["image"])
    return list


def userinfo(username):
    return [False,"/static/logo.png"]

def gen_code():
    code = ""
    list = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM!£$%^&*()1234567890:@;.,;]"
    for i in range(20):
        char = random.choice(list)
        code += char
    return code

def user_data_group(users):
    users_data = {}
    for i in users:
        name = i
        data = userinfo(name)
        profile_pic = data[1]
        level = data[0]
        users_data[name] = {
            "name":name,
            "profile_pic":profile_pic,
            "level":level
        }
    return users_data

def make_dict_group(group):
    group = dict(group)
    group["sets"] = list(group["sets"])
    group["users"] = list(group["users"])
    group["settings"] = dict(group["settings"])
    return group

def check_image(url):
    r = requests.get("https://api.moderatecontent.com/moderate/?key="+os.environ['image_key']+"&url="+url)
    print(r.text)
    return r.json()