import os
import json
from flask import Flask, request, Response
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


def connect_leaderboard_blob():
    blob_service_client = BlobServiceClient.from_connection_string(os.environ["AZURE_CONNECTIONSTRING"])
    blob_leaderboard_client = blob_service_client.get_blob_client(container=LEADERBOARD_BLOB_CONTAINER, blob=LEADERBOARD_BLOB_NAME)
    return blob_leaderboard_client

def connect_track_blob():
    blob_service_client = BlobServiceClient.from_connection_string(os.environ["AZURE_CONNECTIONSTRING"])
    blob_track_client = blob_service_client.get_blob_client(container=LEADERBOARD_BLOB_CONTAINER, blob=TRACK_BLOB_NAME)
    return blob_track_client

def connect_deadline_blob():
    blob_service_client = BlobServiceClient.from_connection_string(os.environ["AZURE_CONNECTIONSTRING"])
    blob_deadline_client = blob_service_client.get_blob_client(container=LEADERBOARD_BLOB_CONTAINER, blob=DEADLINE_BLOB_NAME)
    return blob_deadline_client

def delete_leaderboard():
    global leaderboard_data  # Access the global variable to modify it
    leaderboard_data = {}    # Set the leaderboard_data dictionary to an empty dictionary

def load_leaderboard():
    try:
        blob_leaderboard_client = connect_leaderboard_blob()

        leaderboard_data_blob = blob_leaderboard_client.download_blob()
        return json.loads(leaderboard_data_blob.readall())
    except Exception as e:
        return {e}

def save_leaderboard():
    blob_leaderboard_client = connect_leaderboard_blob()

    blob_leaderboard_client.upload_blob(json.dumps(leaderboard_data), overwrite=True)

def load_track():
    try:
        blob_track_client = connect_track_blob()

        track_data_blob = blob_track_client.download_blob()
        return json.loads(track_data_blob.readall())
    except Exception as e:
        return {e}

def save_track():
    blob_track_client = connect_track_blob()

    blob_track_client.upload_blob(json.dumps(track_data), overwrite=True)

def load_deadline():
    try:
        blob_deadline_client = connect_deadline_blob()

        deadline_data_blob = blob_deadline_client.download_blob()
        return json.loads(deadline_data_blob.readall())
    except Exception as e:
        return {e}

def save_deadline():
    blob_deadline_client = connect_deadline_blob()

    blob_deadline_client.upload_blob(json.dumps(deadline_data), overwrite=True)

leaderboard_data = load_leaderboard()

track_data = load_track()

deadline_data = load_deadline()

# leaderboard_data = {
#     'user1': '12:123:123',
#     'user2': '45:672:453',
#     'user3': '55:555:555'
# }

# track_data = ''

# track_deadline = ''

def get_track():
    if not any(track_data):
        return 'sorry, no track is selected yet'
    return f"The new track to race on is: {track_data}"

def update_track(message):
    global track_data
    track_data = message

def get_deadline():
    if not any(track_deadline):
        return 'sorry, no deadline is set yet'
    return f"The last day to race on {track_data} is {track_deadline}"

def update_deadline(message):
    global track_deadline
    track_deadline = message

def update_leaderboard(user, score):
    leaderboard_data[user] = score

def get_leaderboard():
    sorted_leaderboard = sorted(leaderboard_data.items(), key=lambda x: x[1])
    return sorted_leaderboard


def format_leaderboard():
    if not any(leaderboard_data):
        if not any(leaderboard_data.values()):
            return "Leaderboard is empty."

    sorted_leaderboard = get_leaderboard()
    leaderboard_str = "\n".join([f"{score}     | <@{user}>" for user, score in sorted_leaderboard])
    return f"Leaderboard:\n{leaderboard_str}"

@app.route('/time', methods=['POST'])
def time():
    form_data = request.form
    user = form_data['user_name']
    text = form_data.get('text', '')
    channel_id = form_data['channel_id']

    try:
        time = str(text)
        update_leaderboard(user, time)
        save_leaderboard()  # Save the leaderboard data to Azure Blob Storage after updating
        leaderboard = format_leaderboard()

        message = f"Time score updated for <@{user}>. \n\n {leaderboard}"
    except ValueError:
        message = "Invalid time format. Please use the following format: nn:nnn:nnn"

    return Response(client.chat_postMessage(channel=channel_id, text=message)), 200



@app.route('/leaderboard', methods=['POST'])
def leaderboard():
    form_data = request.form
    channel_id = form_data['channel_id']
    
    message = format_leaderboard()
    client.chat_postMessage(channel=channel_id, text=message)
    return Response(), 200

@app.route('/resetleaderboard', methods=['POST'])
def resetleaderboard():
    form_data = request.form
    leaderboardMessage = format_leaderboard()
    resetmessage = "And the games have ended! Congrats to the winner!\n"
    channel_id = form_data['channel_id']

    delete_leaderboard()  # Call the function to reset the leaderboard_data dictionary
    client.chat_postMessage(channel=channel_id, text=resetmessage + leaderboardMessage)
    return Response(), 200

@app.route('/track', methods=["POST"])
def track():
    form_data = request.form
    text = get_track()
    channel_id = form_data['channel_id']

    client.chat_postMessage(channel=channel_id, text=text)
    return Response(), 200

@app.route('/setnewtrack', methods=["POST"])
def setnewtrack():
    form_data = request.form
    message = form_data['text']
    update_track(message)
    channel_id = form_data['channel_id']
    testmessage = get_track()

    client.chat_postMessage(channel=channel_id, text=testmessage)
    return Response(), 200

@app.route('/deadline', methods=["POST"])
def deadline():
    form_data = request.form
    text = get_deadline()
    channel_id = form_data['channel_id']

    client.chat_postMessage(channel=channel_id, text=text)
    return Response(), 200

@app.route('/setnewdeadline', methods=["POST"])
def setnewdeadline():
    form_data = request.form
    message = form_data['text']
    update_deadline(message)
    channel_id = form_data['channel_id']
    testmessage = get_deadline()

    client.chat_postMessage(channel=channel_id, text=testmessage)
    return Response(), 200

@app.route('/help', methods=["POST"])
def help():
    form_data = request.form
    channel_id = form_data['channel_id']
    message = "Hi! New here? Let me help you! \n\nThese are the commands you can use:\n\n`/leaderboard` - Shows you the current leaderboard. \n`/track` - Shows the track that our racers are currently destroying. \n`/time` - Wanna join or have a new time? Add it here! \n`/deadline` - We race the current track till this date. After this date, no new times can be added \n \n \nThese next commands are a bit heavier, so don't just run these without chatting with the other racers! \n \n`/setnewtrack` - When the racers pick a new track, you can add the name of this new track here. \n`/setnewdeadline` When a new track is chosen, add a new deadline here. \n`/resetleaderboard` - This whipes the whole leaderboard. BE CAREFUL! Once deleted, the leaderboard CANNOT be restored!"

    client.chat_postMessage(channel=channel_id, text=message)
    return Response(), 200

if __name__ == '__main__':
    app.run(debug=False)

