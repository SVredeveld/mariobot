import os
import json
from flask import Flask, request, jsonify, Response
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slackeventsapi import SlackEventAdapter
from azure.storage.blob import BlobServiceClient

app = Flask(__name__)

# Initialize the Slack WebClient with your bot token
client = WebClient(token=os.environ['SLACK_TOKEN'])

# Load leaderboard data from Azure Blob Storage on startup
LEADERBOARD_BLOB_CONTAINER = "mariobot-leaderboard"
LEADERBOARD_BLOB_NAME = "leaderboard.json"

def connect_blob():
    blob_service_client = BlobServiceClient.from_connection_string(os.environ["AZURE_CONNECTIONSTRING"])
    blob_client = blob_service_client.get_blob_client(container=LEADERBOARD_BLOB_CONTAINER, blob=LEADERBOARD_BLOB_NAME)
    return blob_client

def delete_leaderboard():
    global leaderboard_data  # Access the global variable to modify it
    leaderboard_data = {}    # Set the leaderboard_data dictionary to an empty dictionary

def load_leaderboard():
    try:
        blob_client = connect_blob()

        leaderboard_data_blob = blob_client.download_blob()
        return json.loads(leaderboard_data_blob.readall())
    except Exception as e:
        return {e}

def save_leaderboard():
    blob_client = connect_blob()

    blob_client.upload_blob(json.dumps(leaderboard_data), overwrite=True)

leaderboard_data = load_leaderboard()

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
        message = f"Time score updated for <@{user}>."
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
    resetmessage = "And the games have ended! Congrats to the winner!"
    channel_id = form_data['channel_id']

    delete_leaderboard()  # Call the function to reset the leaderboard_data dictionary
    client.chat_postMessage(channel=channel_id, text=resetmessage + leaderboardMessage)
    return Response(), 200


if __name__ == '__main__':
    app.run(debug=True)

