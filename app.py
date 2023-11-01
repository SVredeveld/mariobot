import os
import json
import time as time_module
import hupper
from flask import Flask, request, Response, render_template
from slack_sdk import WebClient
from azure.storage.blob import BlobServiceClient

app = Flask(__name__)

# Initialize the Slack WebClient with your bot token
client = WebClient(token=os.environ.get('SLACK_TOKEN'))

# Load leaderboard data from Azure Blob Storage on startup
LEADERBOARD_BLOB_CONTAINER = "mariobot-leaderboard"
LEADERBOARD_BLOB_NAME = "leaderboard.json"
TRACK_BLOB_NAME = "track.json"
DEADLINE_BLOB_NAME = "deadline.json"

user_cache = {
    "users": [],
    "timestamp": 0
}
CACHE_EXPIRATION_TIME = 3600


def connect_blob(blob_name):
    blob_service_client = BlobServiceClient.from_connection_string(os.environ["AZURE_CONNECTIONSTRING"])
    return blob_service_client.get_blob_client(container=LEADERBOARD_BLOB_CONTAINER, blob=blob_name)


def download_blob(blob_name):
    blob_client = connect_blob(blob_name)
    blob_content = blob_client.download_blob().readall()
    return {} if not blob_content else json.loads(blob_content)


def upload_blob(blob_name, data):
    blob_client = connect_blob(blob_name)
    blob_client.upload_blob(json.dumps(data), overwrite=True)


def get_track():
    return download_blob(TRACK_BLOB_NAME)


def set_track(track):
    upload_blob(TRACK_BLOB_NAME, track)


def get_deadline():
    return download_blob(DEADLINE_BLOB_NAME)


def set_deadline(deadline):
    upload_blob(DEADLINE_BLOB_NAME, deadline)


def get_leaderboard():
    return download_blob(LEADERBOARD_BLOB_NAME)


def set_leaderboard(leaderboard):
    upload_blob(LEADERBOARD_BLOB_NAME, leaderboard)


def update_leaderboard(user, time):
    leaderboard = get_leaderboard()
    leaderboard[user] = time
    set_leaderboard(leaderboard)
    return leaderboard


def reset_leaderboard():
    leaderboard = {}
    set_leaderboard(leaderboard)


def sort_leaderboard(leaderboard):
    return sorted(leaderboard.items(), key=lambda entry: entry[1])


def format_leaderboard(leaderboard):
    if not leaderboard:
        return "Leaderboard is empty."

    formatted_leaderboard = "\n".join([f"{rank}. {score}\t| <@{user}>" for rank, (user, score) in enumerate(sort_leaderboard(leaderboard), start=1)])
    return formatted_leaderboard


def get_placement_of_user(user):
    leaderboard = sort_leaderboard(get_leaderboard())
    try:
        return list(dict(leaderboard).keys()).index(user) + 1
    except:
        return 0


# A function that gets the 'real_name' of a user. We use caching since users_list 
# gets all users in an organisation and that doesn't change that often
def get_real_name_from_username(username):
    current_time = time_module.time()
    if current_time - user_cache["timestamp"] > CACHE_EXPIRATION_TIME:
        # If cache is expired, fetch the user list again and update the cache
        users_list = client.users_list()
        if users_list.get("ok"):
            user_cache["users"] = users_list["members"]
            user_cache["timestamp"] = current_time
    else:
        # If cache hasn't expired, use the cached data
        users_list = {"members": user_cache["users"]}

    for member in users_list["members"]:
        if 'name' in member and member['name'] == username:
            return member['real_name']

    return None


@app.route('/time', methods=['POST'])
def command_time():
    form_data = request.form
    channel_id = form_data['channel_id']
    user = form_data['user_name']
    time = str(form_data['text'])

    previous_placement = get_placement_of_user(user)
    leaderboard = update_leaderboard(user, time)
    current_placement = get_placement_of_user(user)

    if current_placement == 1:
        text = f"NEW FASTEST TIME! <@{user}> set a new track record with a time of {time}."
    elif current_placement == 2:
        text = f"NEW SECOND TIME! <@{user}> set a new second track time with a time of {time}."
    elif current_placement == 3:
        text = f"NEW THIRD TIME! <@{user}> set a new third track time with a time of {time}."
    else:
        text = f"Time score updated for <@{user}> with a time of {time}."

    if previous_placement == 0:
        text += f" They entered the race at place {current_placement}!"
    elif previous_placement != 0 and previous_placement == current_placement:
        text += f" They remained at place {previous_placement}."
    else:
        text += f" They went from place {previous_placement} to place {current_placement}!"

    text += f"\n\nNew leaderboard:\n{format_leaderboard(leaderboard)}"

    client.chat_postMessage(channel=channel_id, text=text)
    return Response(), 200


@app.route('/leaderboard', methods=['POST'])
def command_leaderboard():
    form_data = request.form
    channel_id = form_data['channel_id']
    user_id = form_data["user_id"]

    leaderboard = get_leaderboard()
    text = (f"Current leaderboard:\n{format_leaderboard(leaderboard)}"
            if leaderboard
            else f"Sorry, no time has been set on the leaderboard yet. Be the first to do so!")

    client.chat_postEphemeral(channel=channel_id, user=user_id, text=text)
    return Response(), 200


@app.route('/resetleaderboard', methods=['POST'])
def command_resetleaderboard():
    form_data = request.form
    channel_id = form_data['channel_id']

    leaderboard = get_leaderboard()
    reset_leaderboard()
    text = f"And the games have ended! Congrats to the winner!\n{format_leaderboard(leaderboard)}"

    client.chat_postMessage(channel=channel_id, text=text)
    return Response(), 200


@app.route('/track', methods=["POST"])
def command_track():
    form_data = request.form
    channel_id = form_data['channel_id']
    user_id = form_data["user_id"]

    track = get_track()
    text = (f"The current track to race on is: {track}."
            if track
            else f"Sorry, no track has been selected yet.")

    client.chat_postEphemeral(channel=channel_id, user=user_id, text=text)
    return Response(), 200


@app.route('/setnewtrack', methods=["POST"])
def command_setnewtrack():
    form_data = request.form
    channel_id = form_data['channel_id']
    track = str(form_data['text'])

    set_track(track)
    text = f"The new track to race on is: {track}."

    client.chat_postMessage(channel=channel_id, text=text)
    return Response(), 200


@app.route('/deadline', methods=["POST"])
def command_deadline():
    form_data = request.form
    channel_id = form_data['channel_id']
    user_id = form_data["user_id"]

    deadline = get_deadline()
    text = (f"The last day to race on the current track is set on: {deadline}."
            if deadline
            else f"Sorry, no deadline has been set yet.")

    client.chat_postEphemeral(channel=channel_id, user=user_id, text=text)
    return Response(), 200


@app.route('/setnewdeadline', methods=["POST"])
def command_setnewdeadline():
    form_data = request.form
    channel_id = form_data['channel_id']
    deadline = str(form_data['text'])

    set_deadline(deadline)
    text = f"The last day to race on the current track is now set on: {deadline}."

    client.chat_postMessage(channel=channel_id, text=text)
    return Response(), 200


@app.route('/help', methods=["POST"])
def command_help():
    form_data = request.form
    channel_id = form_data['channel_id']
    user_id = form_data['user_id']
    message = "Hi! New here? Let me help you! \n\nThese are the commands you can use:\n\n`/leaderboard` - Shows you the current leaderboard. \n`/track` - Shows the track that our racers are currently destroying. \n`/time` - Wanna join or have a new time? Add it here! \n`/deadline` - We race the current track till this date. After this date, no new times can be added \n \n \nThese next commands are a bit heavier, so don't just run these without chatting with the other racers! \n \n`/setnewtrack` - When the racers pick a new track, you can add the name of this new track here. \n`/setnewdeadline` When a new track is chosen, add a new deadline here. \n`/resetleaderboard` - This wipes the whole leaderboard. BE CAREFUL! Once deleted, the leaderboard CANNOT be restored!"

    client.chat_postEphemeral(channel=channel_id, user=user_id, text=message)
    return Response(), 200


@app.route('/leaderboard', methods=['GET'])
def dashboard():
    leaderboard_with_real_names = []
    leaderboard = sort_leaderboard(get_leaderboard())
    for user, time_entry in leaderboard:
        leaderboard_with_real_names.append((get_real_name_from_username(user) or user, time_entry))
    current_track = get_track()
    return render_template('dashboard.html', leaderboard=leaderboard_with_real_names, currentTrack=current_track)


def start_app_development():
    app.run(debug=True, host='0.0.0.0', port=5000)


if __name__ == '__main__':
    if os.environ.get("DEVELOPMENT") == "true":
        hupper.start_reloader('app.start_app_development')
    else:
        app.run(debug=False)
