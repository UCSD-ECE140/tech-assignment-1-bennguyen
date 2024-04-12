import os
import json
import copy
from collections import OrderedDict

import paho.mqtt.client as paho
from paho import mqtt
from dotenv import load_dotenv

from InputTypes import NewPlayer
from game import Game
from moveset import Moveset

import time
import logging
# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

import random  # Add this line for random module
from collections import deque

import copy




# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    """
        Prints the result of the connection with a reasoncode to stdout ( used as callback for connect )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param flags: these are response flags sent by the broker
        :param rc: stands for reasonCode, which is a code for the connection result
        :param properties: can be used in MQTTv5, but is optional
    """
    print("CONNACK received with code %s." % rc)


# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, properties=None):
    """
        Prints mid to stdout to reassure a successful publish ( used as callback for publish )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
        :param properties: can be used in MQTTv5, but is optional
    """
    print("mid: " + str(mid))


# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    """
        Prints a reassurance for successfully subscribing
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
        :param granted_qos: this is the qos that you declare when subscribing, use the same one for publishing
        :param properties: can be used in MQTTv5, but is optional
    """
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


# triggered on message from subscription
def on_message(client, userdata, msg):
    """
        Runs game logic and dispatches behavior depending on route
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param msg: the message with topic and payload
    """
    print("message: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    topic_list = msg.topic.split("/")

    # Validate it is input we can deal with
    if topic_list[-1] in dispatch.keys(): 
        dispatch[topic_list[-1]](client, topic_list, msg.payload)



# Dispatched function, adds player to a lobby & team
def add_player(client, topic_list, msg_payload):
    # Parse and Validate Input Data
    try:
        player = NewPlayer(**json.loads(msg_payload))
    except:
        print("ValidationError in create_game")
        return
    
    # If lobby doesn't exists...
    if player.lobby_name not in client.team_dict.keys():
        client.team_dict[player.lobby_name] = {}
        client.team_dict[player.lobby_name]['started'] = False

    if client.team_dict[player.lobby_name]['started']:
        publish_error_to_lobby(client, player.lobby_name, "Game has already started, please make a new lobby")

    add_team(client, player)

    print(f'Added Player: {player.player_name} to Team: {player.team_name}')


def add_team(client, player):
    # If team not in lobby, make new team and start a player list for the team
    if player.team_name not in client.team_dict[player.lobby_name].keys():
        client.team_dict[player.lobby_name][player.team_name] = [player.player_name,]    
    # If team already exists, add player to existing list
    else:
        client.team_dict[player.lobby_name][player.team_name].append(player.player_name)

move_to_Moveset = {
    'UP' : Moveset.UP,
    'DOWN' : Moveset.DOWN,
    'LEFT' : Moveset.LEFT,
    'RIGHT' : Moveset.RIGHT
}

#handles all the logic and move resolve issue. also handles gameover when all coins collected
#Print updated map after all players have move.
#didn't trigger game over when all coins were collected
#DIDN'T PRINT MAP after collecting all coins
# Dispatched Function: handles player movement commands
def player_move(client, topic_list, msg_payload):
    lobby_name = topic_list[1]
    player_name = topic_list[2]
    if lobby_name in client.team_dict.keys():
        try:
            new_move = msg_payload.decode()

            client.move_dict[lobby_name][player_name] = (player_name, move_to_Moveset[new_move])
            game: Game = client.game_dict[lobby_name]

            # If all players made a move, resolve movement
            if len(game.all_players) == len(client.move_dict[lobby_name]):
                for player, move in client.move_dict[lobby_name].values():
                    game.movePlayer(player, move)

                # Publish player states after all movement is resolved
                for player, _ in client.move_dict[lobby_name].values():
                    client.publish(f'games/{lobby_name}/{player}/game_state', json.dumps(game.getGameData(player)))

                # Clear move list
                client.move_dict[lobby_name].clear()
                print(game.map)
                client.publish(f'games/{lobby_name}/scores', json.dumps(game.getScores()))
                if game.gameOver():
                    # Publish game over, remove game
                    publish_to_lobby(client, lobby_name, "Game Over: All coins have been collected")

                    #added print statement to signal game over
                    print("Game Over: All coins have been collected")
                    #added final scores
                    scores = game.getScores()
                    print("Final Scores:")
                    for team, score in scores.items():
                        print(f"{team}: {score}")
                    winning_team = max(scores, key=scores.get)
                    print(f"The winning team is: {winning_team}")


                    client.team_dict.pop(lobby_name)
                    client.move_dict.pop(lobby_name)
                    client.game_dict.pop(lobby_name)

        except Exception as e:
            raise e
            publish_error_to_lobby(client, lobby_name, e.__str__)
    else:
        publish_error_to_lobby(client, lobby_name, "Lobby name not found.")


# Dispatched function: Instantiates Game object
def start_game(client, topic_list, msg_payload):
    lobby_name = topic_list[1]
    if isinstance(msg_payload, bytes) and msg_payload.decode() == "START":
        if lobby_name in client.team_dict.keys():
                # create new game
                dict_copy = copy.deepcopy(client.team_dict[lobby_name])
                dict_copy.pop('started')

                game = Game(dict_copy)
                client.game_dict[lobby_name] = game
                client.move_dict[lobby_name] = OrderedDict()
                client.team_dict[lobby_name]["started"] = True

                for player in game.all_players.keys():
                    client.publish(f'games/{lobby_name}/{player}/game_state', json.dumps(game.getGameData(player)))


                print(game.map)
    elif isinstance(msg_payload, bytes) and msg_payload.decode() == "STOP":
        publish_to_lobby(client, lobby_name, "Game Over: Game has been stopped")
        client.team_dict.pop(lobby_name, None)
        client.move_dict.pop(lobby_name, None)
        client.game_dict.pop(lobby_name, None)

def publish_error_to_lobby(client, lobby_name, error):
    publish_to_lobby(client, lobby_name, f"Error: {error}")


def publish_to_lobby(client, lobby_name, msg):
    client.publish(f"games/{lobby_name}/lobby", msg)


dispatch = {
    'new_game' : add_player,
    'move' : player_move,
    'start' : start_game,
}

#newly created function to meet challenge 2 delierables 
#function to get user input and call player_move
#don't add any space for entering user input
def user_input_move(client, lobby_name, player_name):
    user_input = input(f"Select move for {player_name} (UP/DOWN/LEFT/RIGHT): ").upper()
    player_move(client, [None, lobby_name, player_name], user_input.encode())


if __name__ == '__main__':
    load_dotenv(dotenv_path='./credentials.env')
    
    broker_address = os.environ.get('BROKER_ADDRESS')
    broker_port = int(os.environ.get('BROKER_PORT'))
    username = os.environ.get('USER_NAME')
    password = os.environ.get('PASSWORD')

    client = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION1, client_id="GameClient", userdata=None, protocol=paho.MQTTv5)
    
    # enable TLS for secure connection
    client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    # set username and password
    client.username_pw_set(username, password)
    # connect to HiveMQ Cloud on port 8883 (default for MQTT)
    client.connect(broker_address, broker_port)

    # setting callbacks, use separate functions like above for better visibility
    client.on_subscribe = on_subscribe # Can comment out to not print when subscribing to new topics
    client.on_message = on_message
    client.on_publish = on_publish # Can comment out to not print when publishing to topics
    
    # custom dictionary to track players
    client.team_dict = {} # Keeps tracks of players before a game starts {'lobby_name' : {'team_name' : [player_name, ...]}}
    client.game_dict = {} # Keeps track of the games {{'lobby_name' : Game Object}
    client.move_dict = {} # Keeps track of the games {{'lobby_name' : Game Object}


    lobby_name = "my_lobby"

    client.subscribe("new_game")
    client.subscribe('games/+/start')
    client.subscribe('games/+/+/move')

    # Subscribe to error and lobby topics
    client.subscribe("games/+/error")
    client.subscribe("games/+/lobby")
    client.subscribe(f"games/{lobby_name}/lobby")


    client.loop_start()  # Start the loop asynchronously

    try:
        lobby_name = "my_lobby"

        team_players = {
            "TeamA": ["BEN", "WILLIAM"],
            "TeamB": ["TOM", "JERRY"]
        }

        for team, players in team_players.items():
            for player_name in players:
                add_player(client, [None, lobby_name], json.dumps({"lobby_name": lobby_name, "team_name": team, "player_name": player_name}))
            
        start_game(client, [None, lobby_name], b"START")

        round_counter=0
        while True:
            if not client.team_dict:  # Check if team_dict is empty
                break  # Break out of the loop if it's empty

            for key, value in client.team_dict[lobby_name].items():
                # Check if the value is a list (which represents a team)
                if isinstance(value, list):
                    # Print the team name
                    print("Team:", key)
                    
                    # Iterate over the player names in the team
                    for player_name in value:
                        move = random.choice(["UP", "DOWN", "LEFT", "RIGHT"])
                        print("Player:", player_name, "moved", move)
                        player_move(client, [None, lobby_name, player_name], move.encode())

                # Increment the round counter at the end of each round
            round_counter += 1
            print(f"End of Round {round_counter}")


    except KeyboardInterrupt:
        logger.info("Exiting...")
        client.disconnect()

