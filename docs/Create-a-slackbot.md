# Creating and Installing a Slack Bot

This document provides a guide on how to create a Slack bot and install it into your Slack workspace.

## Prerequisites

- A Slack account
- A Slack workspace to test in

## Step 1: Create a New Slack App

1. Navigate to the [Slack API](https://api.slack.com/apps) site.
2. Click on the `Create New App` button.
   - Choose the 'from scratch' option.
   - Enter your App's name.
   - Choose the workspace you want to develop your app in.
   - Click the `Create App` button.

## Step 2: Configure the Slack App

1. **Basic Information**: Under the `Settings` section, you can configure various settings like displaying the app's name, description, and icon.
2. **Bot User**: Add a bot user under the `Features` section to give your app a personality and presence in Slack.
   - Click on `Bot Users`.
   - Click the `Add a Bot User` button to add a new bot user.
   - Configure the display name, default username, and other settings.
3. **Permissions**: Configure the app's permissions to grant specific capabilities and control its access within the workspace.
   - Navigate to `OAuth & Permissions` in the `Features` section.
   - Scroll down to the `Scopes` section, and add the following permissions
       - chat:write
       - commands
       - users:read
       - channels:read
4. **Slash commands**: Add a slash command to your app to enable users to interact with it.
   - Navigate to `Slash Commands` in the `Features` section.
   - Click the `Create New Command` button.
   - Enter the command name and description.
   - Enter your ngrok endpoint following with the slash commands as defined in the `app.py` file. e.g. `https://<ngrok-endpoint>/setnewtrack`
      - To get your ngrok endpoint, go to https://localhost:4040/ and copy the `Forwarding` URL.
          - This URL is temporary and will change every time you restart ngrok when using the free version. This means you will have to update the slash command URL every time you restart ngrok.
   - Click the `Save` button.

## Step 3: Install the App to Workspace

1. Return to the [Slack API](https://api.slack.com/apps) dashboard and select your app.
2. Navigate to `OAuth & Permissions` under the `Features` section.
3. Click the `Install App to Workspace` button.
4. You will be redirected to your Slack workspace and prompted with a permission modal. Review the requested permissions, then click `Allow`.

## Step 4: Verify Installation

1. Go to your Slack workspace.
2. You should see the app in the list of your workspace applications.
3. Try using your app by sending a slash command to test if it's working as expected.