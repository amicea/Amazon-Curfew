from flask import Flask, render_template
from flask_ask import Ask, question, statement
from difflib import get_close_matches
import Sensor
import threading
import json


app = Flask(__name__)
ask = Ask(app, "/")
macs_at_home = [] #list of all the macs which are "home"
sensor = Sensor.Sensor() #sensor object in charge of managing information about who's home

class SensorRunnerThread(threading.Thread):
    """
    A thread class in order to operate the sensing operations of the app
    """
    def run(self):
        sensor.run()


@app.route("/")
def homepage():
    """
    gives a homepage for the app. app is hosted over port 5000 since this is a Flask app. This can be used for testing to
    ensure the server is online
    :return: message text to be posted
    """
    return "homepage"


@ask.launch
def start_skill():
    """
    default intent for the skill. States who is home
    :return: a statement stating who is home
    """
    return statement(whoHome())


@ask.intent("WhoHome")
def run_who_home():
    """
    the WhoHome intents say how many people and who is home based on the registered macs
    :return: statement giving how many people and who is home based on the registered macs
    """
    return statement(whoHome())

@ask.intent("WhoLeft")
def run_who_left(firstName):
    """
    The WhoLeft intent says when a person left
    :param firstName: first name of the person to be found
    :return: returns a statement saying when a person left if that person is in the name's list otherwise Alexa says
    she does not know who you are asking for
    """
    return statement(whoLeft(firstName))

@ask.intent("WhoCame")
def run_who_arrive(firstName):
    """
    the WhoCame intnet says when a person arrived
    :param firstName: first name of person to be found
    :return: returns a statement saying when a person arrived if that person is in the name's list otherwise Alexa says
    she does not know who you are asking for
    """
    return statement(whoCame(firstName))

def whoHome():
    """
    finds all the macs_at_home translates them into names through the sensor and then give a string that can be spoken
    :return: string that can be spoken by alexa
    """
    global macs_at_home
    count = 0
    names = []
    macs_at_home = get_addresses()
    print macs_at_home
    for m in macs_at_home:
        n = sensor.map_mac(m)
        if n is not None:
            names.append(n)
            count += 1
    message = ""
    if count > 1:
        message = "there are " + str(count) + " people home."
        message += " These people are: "
    elif count == 1:
        message = "there is " + str(count) + " person home."
        message += " This person is: "
    else:
        message = "No one else is home"
    for n in names:
        message += ", " + n
    print "*" * 30
    print count
    print "*" * 30
    return message


def whoLeft(firstName):
    """
    scans the leave_log to identify when a specific person left. If that person is not found then returns a statement
    that the person is not known.
    :param firstName: first name of person to be found
    """
    with open('leave_log') as leave_log:
        data = json.load(leave_log)
        names = sensor.get_names_list()
        print "*" * 30
        nearest = get_close_matches(firstName, names)
        if nearest:
            time_left = data.get(nearest[0])
            if (time_left == None):
                return "It looks like " + firstName + " hasn't left today."
            else:
                return firstName + " left at " + convert_time(time_left)
        else:
            return "I don't know who " + firstName + " is"
def whoCame(firstName):
    """
    scans the leave_log to identify when a specific person left. If that person is not found then returns a statement
    that the person is not known.
    :param firstName: first name of person to be found
    """
    with open('arrive_log') as leave_log:
        data = json.load(leave_log)
        names = sensor.get_names_list()
        nearest = get_close_matches(firstName, names)
        if nearest:
            time_arrive = data.get(nearest[0])
            if (time_arrive== None):
                return "It looks like " + firstName + " hasn't gotten back today"
            else:
                return firstName + " arrived at " + convert_time(time_arrive)
        else:
            print "#" *30
            print firstName
            print "#" *30
            return "I don't know who " + firstName + " is"

def get_addresses():
    """

    :return: updates macs at home to have only the macs in the house. returns this new list
    """
    global macs_at_home
    macs = sensor.get_mac_dict()
    macs_at_home = []
    for m in macs:
        if macs[m] is not None:
            macs_at_home.append(m)

    return macs_at_home


def convert_time(military_time):
    """
    converts a military time to a a.m. p.m. time
    :param military_time: time in the form HH:MM:SS
    :return: a string in the form HH:MM am/pm
    """
    hour = int(float(military_time[0:2]))
    minutes = int(float(military_time[3:5]))

    if (hour == 0):
        return "12:"+ str(minutes) + 'a.m.'
    elif (hour < 12):
        return military_time[:5] + 'a.m.'
    elif (hour == 12):
        return military_time[:5] + 'p.m.'
    else:
        return str(hour - 12) + ':' + str(minutes) + 'p.m.'


#runs the actual app
if __name__ == '__main__':
    sensor_thread = SensorRunnerThread()
    sensor_thread.setDaemon(True) #ensures that sensor_thread doesn't keep running even when program is killed
    sensor_thread.start()

    app.run(debug=True, use_reloader=False, threaded = True)
