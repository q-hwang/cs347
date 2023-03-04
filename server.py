
import random
import jsonlines
import numpy as np
import glob
import os
import copy
from llm import init_llm_level_guess, get_llm_restaurant_recommendation, get_llm_food_recommendation, get_llm_delivery_option_recommendation, get_llm_tips_option_recommendation
debug = False

STAGES = ["restaurant", "food items", "delivery method", "tips"]
ADAPTATION_PENALTY = 2
SMOOTH = 1
CONTEXT_WEIGHT = 1

def get_user_input():
    input_string = input('User:')
    if "CONFIRM" in input_string:
        return True, 0, 0, ""
    inputs = input_string.split(",") 
    edit_stage = int(inputs[0])
    button  = int(inputs[1])
    message = ""
    if len(inputs) > 2:
        message = inputs[2]
    return  False, edit_stage, button, message 

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
        "affects_stage": [3],
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
        "affected_by": [0],
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
    for s in range(len(STAGES)):
        selection = state_dict[s]["selection"] 
        if selection is None:
            break
        print(f"Selected {STAGES[s]}:\n" + str(selection))

    confirm, edit_stage, button, message = get_user_input()
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

    return confirm, edit_stage, selected_option_idx, local_feedback, reroll, increase_level



def display_full_webpage(state_dict, curr_stage_idx):
    
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


if __name__ == "__main__":
    print("APP: Welcome! What do you want?")
    user_name = input('User Name:')
    init_input = input('User:')
    # TODO: try populate this initial guess with log.txt, heuristic + maybe with LLM using few shot prompting 
    init_level_guess = get_init_level_guess(user_name, init_input)
    init_adapt_guess = get_init_adapt_guess(user_name)
    print(init_level_guess)
    print(init_adapt_guess)
    for i in range(len(STAGES)):
        init_guess_state_dict[i]["level"] = round(init_level_guess[i])
        init_guess_state_dict[i]["expected_adapt_time"] = int(init_adapt_guess[i])
        init_guess_state_dict[i]["local_feedback"] = [[init_input]]
    state_dict = copy.deepcopy(init_guess_state_dict)

    # initial handeling
    curr_stage_idx = 0
    while True:
        if curr_stage_idx == len(STAGES):
            # user engaging screen
            confirm, edit_stage, selected_option_idx, user_message, reroll, increase_level = display_summary_webpage(state_dict)
            if confirm:
                filled = True
                for s in range(len(STAGES)):
                    if not is_finalized(state_dict, s):
                        print("CANNOT CONFIRM, need to complete " + STAGES[s])
                        filled = False
                        break
                if filled:
                    with jsonlines.open(f"histories/{user_name}_levels.jsonl", mode='a') as writer:
                        end_estimate = state_dict
                        for i in range(len(state_dict)):
                            if state_dict[i]["level"] > init_guess_state_dict[i]["level"]:
                                if debug:
                                    print("ADAPTATION INCREASE")
                                end_estimate[i]["expected_adapt_time"] = end_estimate[i]["expected_adapt_time"] * ADAPTATION_PENALTY
                            # elif not state_dict[i]["edited"]:
                            else:
                                if debug:
                                    print("ADAPTATION DECREASE")
                                end_estimate[i]["level"] = max(init_level_guess[i] - 1/state_dict[i]["expected_adapt_time"], 0)
                
                        writer.write((init_input, [x["level"] for x  in end_estimate]))

                    with jsonlines.open(f"histories/{user_name}_expected_adapt_times.jsonl", mode='w') as writer:
                        writer.write([x["expected_adapt_time"] for x  in end_estimate])

                    # with open(f"{user_name}_log.txt", "a+") as f:
                    #     f.write(str((init_input, [x["level"] for x  in state_dict])))
                    exit()
                else:
                    continue
            else:
                if selected_option_idx is not None:
                    state_dict[edit_stage]["selection"] = state_dict[edit_stage]["selection"][selected_option_idx]
                    for s in state_dict[edit_stage]["affects_stage"]:
                        state_dict[s]["selection"] = None
                    curr_stage_idx = edit_stage + 1
                else:
                    curr_stage_idx = edit_stage
                    state_dict[edit_stage]["selection"] = None
                    state_dict[edit_stage]["edited"] = True
                    state_dict[curr_stage_idx]["local_feedback"].append([user_message])
                    if increase_level:
                        curr_level = state_dict[curr_stage_idx]["level"]
                        state_dict[curr_stage_idx]["level"] =  min(curr_level + 1, 3)
                continue

        
        stage_name = STAGES[curr_stage_idx]
        stage_level = state_dict[curr_stage_idx]["level"]
        if debug:
            print("handling: " + stage_name, stage_level)
            print(state_dict)
        if state_dict[curr_stage_idx]["selection"] is not None or any([not is_finalized(state_dict, s) for s in  state_dict[curr_stage_idx]["affected_by"]]):
            curr_stage_idx += 1 
            continue

        if stage_level == 3:
            # direct maipulation:
            selected_option = display_full_webpage(state_dict, curr_stage_idx)
            state_dict[curr_stage_idx]["selection"] = selected_option
        if stage_level  == 2:
            # recommend to user

            local_feedback = state_dict[curr_stage_idx]["local_feedback"]
            llm_suggestions = state_dict[curr_stage_idx]["handeler"](state_dict, local_feedback)
            state_dict[curr_stage_idx]["selection"] = llm_suggestions
            init_guess_state_dict[i]["local_feedback"][-1].append(llm_suggestions)
            curr_stage_idx = len(STAGES)
            continue

        if stage_level in [0, 1]:
            # skip

            local_feedback = state_dict[curr_stage_idx]["local_feedback"]
            llm_suggestions = state_dict[curr_stage_idx]["handeler"](state_dict, local_feedback)
            state_dict[curr_stage_idx]["selection"] = llm_suggestions[0]
            init_guess_state_dict[i]["local_feedback"][-1].append(llm_suggestions[0])
        
        for s in state_dict[curr_stage_idx]["affects_stage"]:
            state_dict[s]["selection"] = None
        curr_stage_idx += 1 
        
        


