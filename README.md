# 🍄 MarioBot for Slack - Time Tracker & Leaderboard

Welcome to the MarioBot repository! Our Slack bot is designed to streamline time-tracking within your team. Just add your time, and MarioBot will handle the rest, keeping tabs on everyone's input. Compete with your friends or colleagues and climb the leaderboard to see who's the most punctual!

##Features:

🕒 **Time Tracking:** Quickly add your times and let the bot manage the rest.
🏆 **Leaderboard:** See who's on top with our integrated leaderboard.
🤖 **Slack Integration:** Seamlessly integrated with your Slack workspace.

Get started with MarioBot and make time-tracking fun and competitive!

## Local Development
This section provides a guide to get the bot up and running on your local machine. Whether you're looking to contribute or just play around with the code, you'll find everything you need to get started here.

### Prerequisites:
 - [Docker desktop](https://www.docker.com/products/docker-desktop/)
   - Or Docker and docker-compose (Docker desktop includes both)
 - [ngrok](https://ngrok.com/download)
 - A Slackbot and Slack workspace

### Setup:
1. Clone the repository
2. Rename the `.env.example` file to `.env` and fill in the values
3. Run `docker-compose up` to start the bot
4. Go to `http://localhost:4040` to get the ngrok URL
5. Go to your Slackbot settings and add the ngrok URL as the request URL in your slash command settings
6. You're all set! Try adding a time to the bot and see if it works! Changing the python code will automatically restart the bot, so you can test your changes immediately.