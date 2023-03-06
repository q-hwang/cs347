
import random
import jsonlines
import numpy as np
import glob
import os
import copy
from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
import threading


from llm import init_llm_level_guess, get_llm_restaurant_recommendation, get_llm_food_recommendation, get_llm_delivery_option_recommendation, get_llm_tips_option_recommendation
debug = False

STAGES = ["restaurant", "food items", "delivery method", "tips"]
ADAPTATION_PENALTY = 2
SMOOTH = 1
CONTEXT_WEIGHT = 1

curr_stage_idx = 0
state_dict = []
user_name = ''
init_input = ''
init_level_guess = []

# Initialize flask webserver and socket
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['CORS_ALLOWED_ORIGINS'] = ['http://localhost:3001']
app.config['CORS_SUPPORTS_CREDENTIALS'] = True
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3001")


def get_user_input(m):
    input_string = m
    emit('recommendations', "==================================\n\n")
    if "CONFIRM" in input_string:
        return True, 0, 0, ""
    inputs = input_string.split(",") 
    edit_stage = int(inputs[0])
    button  = int(inputs[1])
    message = ""
    if len(inputs) > 2:
        message = inputs[2]
    return False, edit_stage, button, message 

init_guess_state_dict = [
    {
        "level": 1, 
        "affects_stage": [1,2,3],
        "affected_by": [],
        "handeler": get_llm_restaurant_recommendation, 
        "selection": None,
        "local_feedback": "",
        "expected_adapt_time": 1,
        "edited": False,
    },
    {
        "level": 1, 
        "affects_stage": [2, 3],
        "affected_by": [0],
        "handeler": get_llm_food_recommendation, 
        "selection": None,
        "local_feedback": "",
        "expected_adapt_time": 1,
        "edited": False,
    },
    {
        "level": 1, 
        "affects_stage": [3],
        "affected_by": [0, 1],
        "handeler": get_llm_delivery_option_recommendation, 
        "selection": None,
        "local_feedback": "",
        "expected_adapt_time": 1,
        "edited": False,
    },
    {
        "level": 1, 
        "affects_stage": [],
        "affected_by": [0, 1, 2],
        "handeler": get_llm_tips_option_recommendation, 
        "selection": None,
        "local_feedback": "",
        "expected_adapt_time": 1,
        "edited": False,
    }
]

def display_summary_webpage(state_dict):
    message = ""
    for s in range(len(STAGES)):
        selection = state_dict[s]["selection"] 
        if selection is None:
            break
        message += f"Stage {s}: Selected {STAGES[s]}:\n" + str(selection) + "\n\n"
    emit('recommendations', message)
        
    
@socketio.on('message')
def get_user_input_buttons(message):
    print (f"{message} adsfjkladsf")
    emit('recommendations', "\nTo enter an action, following this format: <edit_stage_id>,<edit_action_id>, optional: <a chat messgae message if edit_action_id=0/selection_id if edit_action_id=2/>\nActions:   0: Reroll/Chat, 1: Increase Level, 2: Select Option\n\nTo confirm the order, type CONFIRM\n\n")

    confirm, edit_stage, button, message = get_user_input(message)
    selected_option_idx = None
    local_feedback = ""
    reroll = False 
    increase_level = False

    if button == 0:
        reroll = True
    if button == 1:
        increase_level = True
    if button == 2:
        selected_option_idx = int(message) # a selection
    else:
        local_feedback = message

    continue_session(True, confirm, edit_stage, selected_option_idx, local_feedback, reroll, increase_level)

def display_full_webpage(state_dict, curr_stage_idx):
    display_summary_webpage(state_dict)
    emit('recommendations', f"Stage {curr_stage_idx} [display the original webpage...]:")
    selected_option = input('User give option:')
    return selected_option

def get_init_level_guess(user_name, user_input):

    # estimate this user's preference in this context    
    context_level = np.array(init_llm_level_guess(user_input))

    # estimate all user's preference
    all_user_level_default = np.array([1,1,1,1]) # default
    all_user_level = all_user_level_default

    all_user_levels = []
    for f in glob.glob("histories/*_levels.jsonl"):
        user_levels = []
        with jsonlines.open(f) as reader:
            for obj in reader:
                init_input, level = obj
                user_levels.append(level)
        all_user_levels.append(np.mean(user_levels[-SMOOTH:], axis=0)) 
    if len(all_user_levels) != 0:
        all_user_level = np.mean(all_user_levels, axis=0)

    # estimate this user's preference
    if os.path.exists(f"histories/{user_name}_levels.jsonl"):
        this_user_levels = []
        with jsonlines.open(f"histories/{user_name}_levels.jsonl") as reader:
            for obj in reader:
                init_input, level = obj
                this_user_levels.append(level)
        this_user_level = np.mean(this_user_levels[-SMOOTH:], axis=0)
        return this_user_level * (1-CONTEXT_WEIGHT) + context_level * CONTEXT_WEIGHT
    else:
        return (all_user_level * len(all_user_levels) + all_user_level_default*3) / (len(all_user_levels)+3) * (1-CONTEXT_WEIGHT) + context_level* CONTEXT_WEIGHT
    
def get_init_adapt_guess(user_name):
    this_user_adapt = np.array([1,1,1,1]) # default
    if os.path.exists(f"histories/{user_name}_levels.jsonl"):
        with jsonlines.open(f"histories/{user_name}_expected_adapt_times.jsonl") as reader:
            for adapt in reader:
                return adapt
    
    return this_user_adapt

def is_finalized(state_dict, stage_idx):
    return type(state_dict[stage_idx]["selection"]) == str

# def socket_input(message):
#     response = None
#     socketio.emit('input', message)

#     @socketio.on('message')
#     def handle_output(data):
#         nonlocal response
#         response = data

#     while response is None:
#         socketio.sleep(0.1)

#     return response

@socketio.event
def connect():
    emit('recommendations', "To start, enter your name, comma separated with your initial input \n\n")


@socketio.on('init_message')
def getUserInfo(init_message):
    global curr_stage_idx
    global state_dict
    global user_name
    global init_input
    global init_level_guess

    curr_stage_idx = 0
    user_name, init_input = init_message.split(",")
    emit('recommendations', "\n\n")

    print(f"User {user_name} is starting the session with input: {init_input}")

    # TODO: try populate this initial guess with log.txt, heuristic + maybe with LLM using few shot prompting 
    init_level_guess = get_init_level_guess(user_name, init_input)
    init_adapt_guess = get_init_adapt_guess(user_name)
    # emit('recommendations', init_level_guess)
    # emit('recommendations', init_adapt_guess)
    for i in range(len(STAGES)):
        init_guess_state_dict[i]["level"] = round(init_level_guess[i])
        init_guess_state_dict[i]["expected_adapt_time"] = int(init_adapt_guess[i])
        init_guess_state_dict[i]["local_feedback"] = [[init_input]]
    state_dict = copy.deepcopy(init_guess_state_dict)
    continue_session(False)


def continue_session(displayed, confirm=None, edit_stage=None, selected_option_idx=None, local_feedback=None, reroll=None, increase_level=None):
    # initial handeling
    global curr_stage_idx
    global state_dict
    global user_name
    global init_input
    global init_level_guess


    while True:
        if curr_stage_idx == len(STAGES):
            # user engaging screen
            if not displayed:
                display_summary_webpage(state_dict)
                return
            else:
                displayed = False
                if confirm:
                    # user confirm! 
                    filled = True
                    for s in range(len(STAGES)):
                        if not is_finalized(state_dict, s):
                            emit('recommendations', "CANNOT CONFIRM, need to complete " + STAGES[s])
                            filled = False
                            break
                    if filled:
                        # save interaction result to history
                        with jsonlines.open(f"histories/{user_name}_levels.jsonl", mode='a') as writer:
                            end_estimate = state_dict
                            for i in range(len(state_dict)):
                                if state_dict[i]["level"] > init_guess_state_dict[i]["level"]:
                                    if debug:
                                        emit('recommendations', "ADAPTATION INCREASE")
                                    end_estimate[i]["expected_adapt_time"] = end_estimate[i]["expected_adapt_time"] * ADAPTATION_PENALTY
                                else:
                                    if debug:
                                        emit('recommendations', "ADAPTATION DECREASE")
                                    end_estimate[i]["level"] = max(init_level_guess[i] - 1/state_dict[i]["expected_adapt_time"], 0)
                    
                            writer.write((init_input, [x["level"] for x  in end_estimate]))

                        with jsonlines.open(f"histories/{user_name}_expected_adapt_times.jsonl", mode='w') as writer:
                            writer.write([x["expected_adapt_time"] for x  in end_estimate])
                        exit()
                    else:
                        continue
                else:
                    # user request to update a stage
                    if selected_option_idx is not None:
                        # user selected an option from suggestion or direct manipulation
                        state_dict[edit_stage]["selection"] = state_dict[edit_stage]["selection"][selected_option_idx]
                        curr_stage_idx = edit_stage + 1
                    else:
                        # user wants to edit the stage with AI
                        _stage_idcurrx = edit_stage
                        state_dict[edit_stage]["selection"] = None
                        state_dict[edit_stage]["edited"] = True
                        state_dict[curr_stage_idx]["local_feedback"].append([user_message])
                        if increase_level:
                            curr_level = state_dict[curr_stage_idx]["level"]
                            state_dict[curr_stage_idx]["level"] =  min(curr_level + 1, 3)
                    
                    # erase other affected stages for recomputation
                    for s in state_dict[edit_stage]["affects_stage"]:
                        state_dict[s]["selection"] = None
                    continue

        
        stage_name = STAGES[curr_stage_idx]
        stage_level = state_dict[curr_stage_idx]["level"]
        if debug:
            emit('recommendations', "handling: " + stage_name + " " + str(stage_level))
            emit('recommendations', str(state_dict))

        if state_dict[curr_stage_idx]["selection"] is not None or any([not is_finalized(state_dict, s) for s in  state_dict[curr_stage_idx]["affected_by"]]):
            # do not handle this stage yet either because the result has already been computed or the previous stage is not finalized
            curr_stage_idx += 1 
            continue

        if stage_level == 3:
            # direct maipulation:
            selected_option = display_full_webpage(state_dict, curr_stage_idx)
            state_dict[curr_stage_idx]["selection"] = selected_option

        if stage_level  == 2:
            # recommend three options to user
            local_feedback = state_dict[curr_stage_idx]["local_feedback"]
            llm_suggestions = state_dict[curr_stage_idx]["handeler"](state_dict, local_feedback)
            state_dict[curr_stage_idx]["selection"] = llm_suggestions
            state_dict[curr_stage_idx]["local_feedback"][-1].append(llm_suggestions)
            curr_stage_idx = len(STAGES)
            continue

        if stage_level in [0, 1]:
            # AI select and skip
            local_feedback = state_dict[curr_stage_idx]["local_feedback"]
            llm_suggestions = state_dict[curr_stage_idx]["handeler"](state_dict, local_feedback)
            state_dict[curr_stage_idx]["selection"] = llm_suggestions[0]
            state_dict[curr_stage_idx]["local_feedback"][-1].append(llm_suggestions[0])
        
        # erase other affected stages for recomputation
        for s in state_dict[curr_stage_idx]["affects_stage"]:
            state_dict[s]["selection"] = None
        curr_stage_idx += 1 


if __name__ == "__main__":
    socketio.run(app, port=5001, debug=True)

