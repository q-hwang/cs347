
import random

STAGES = ["restaurant", "food items", "delivery_address", "tips"]

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

def get_llm_restaurant_recommendation(state_dict, global_prompt=None, local_feedback=None):
    print("LLM: " + global_prompt + "    " + local_feedback)
    return random.choices(["r1", "r2", "r3"],k=2)

def get_llm_food_recommendation(state_dict, global_prompt=None, local_feedback=None):
    print("LLM: " + global_prompt + "    " + local_feedback)
    return random.choices(["f1", "f2", "f3"],k=2)

def get_llm_delivery_option_recommendation(state_dict, global_prompt=None, local_feedback=None):
    print("LLM: " + global_prompt + "    " + local_feedback)
    return random.choices(["d1", "d2", "d3"],k=2)

def get_llm_tips_option_recommendation(state_dict, global_prompt=None, local_feedback=None):
    print("LLM: " + global_prompt + "    " + local_feedback)
    return random.choices(["t1", "t2", "t3"],k=2)

init_guess_state_dict = [
    {
        "level": 1, 
        "affects_stage": [1,3],
        "handeler": get_llm_restaurant_recommendation, 
        "selection": None,
        "local_feedback": ""
    },
    {
        "level": 1, 
        "affects_stage": [3],
        "handeler": get_llm_food_recommendation, 
        "selection": None,
        "local_feedback": ""
    },
    {
        "level": 1, 
        "affects_stage": [],
        "handeler": get_llm_delivery_option_recommendation, 
        "selection": None,
        "local_feedback": ""
    },
    {
        "level": 1, 
        "affects_stage": [],
        "handeler": get_llm_tips_option_recommendation, 
        "selection": None,
        "local_feedback": ""
    }
]

def display_summary_webpage(state_dict):
    for s in range(len(STAGES)):
        selection = state_dict[s]["selection"] 
        if selection is None:
            break
        print(f"Selected {STAGES[s]}:\n" + str(selection))
   
    # get user response: 
        # selected_option
        # local_feedback (chat)
        # reroll, increase_level
    confirm, edit_stage, button, message = get_user_input()
    print(confirm, edit_stage, button, message)
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


if __name__ == "__main__":
    print("APP: Welcome! What do you want to eat?")
    init_input = input('User:')
    state_dict = init_guess_state_dict

    # initial handeling
    curr_stage_idx = 0
    while True:
        if curr_stage_idx == len(STAGES):
            # user engaging screen
            confirm, edit_stage, selected_option_idx, local_feedback, reroll, increase_level = display_summary_webpage(state_dict)
            print(confirm, edit_stage, selected_option_idx, local_feedback, reroll, increase_level)
            if confirm:
                # TODO: check all stages are filled up
                exit()
            else:
                if selected_option_idx is not None:
                    state_dict[edit_stage]["selection"] = state_dict[edit_stage]["selection"][selected_option_idx]
                    for s in state_dict[edit_stage]["affects_stage"]:
                        state_dict[s]["selection"] = None
                    curr_stage_idx = edit_stage + 1
                else:
                    curr_stage_idx = edit_stage
                    state_dict[edit_stage]["selection"] = None
                    state_dict[curr_stage_idx]["local_feedback"] += local_feedback
                    if increase_level:
                        curr_level = state_dict[curr_stage_idx]["level"]
                        state_dict[curr_stage_idx]["level"] =  min(curr_level + 1, 3)
                continue

        
        stage_name = STAGES[curr_stage_idx]
        stage_level = state_dict[curr_stage_idx]["level"]
        print("handling: " + stage_name, stage_level)
        print(state_dict)
        if state_dict[curr_stage_idx]["selection"] is not None:
            curr_stage_idx += 1 
            continue

        if stage_level == 3:
            # direct maipulation:
            selected_option = display_full_webpage(state_dict, curr_stage_idx)
            state_dict[curr_stage_idx]["selection"] = selected_option
        if stage_level  == 2:
            # recommend to user

            local_feedback = state_dict[curr_stage_idx]["local_feedback"]
            llm_suggestions = state_dict[curr_stage_idx]["handeler"](state_dict, init_input, local_feedback)
            state_dict[curr_stage_idx]["selection"] = llm_suggestions
            curr_stage_idx = len(STAGES)
            continue

        if stage_level in [0, 1]:
            # skip

            local_feedback = state_dict[curr_stage_idx]["local_feedback"]
            llm_suggestions = state_dict[curr_stage_idx]["handeler"](state_dict, init_input, local_feedback)
            state_dict[curr_stage_idx]["selection"] = llm_suggestions[0]
        
        for s in state_dict[curr_stage_idx]["affects_stage"]:
            state_dict[s]["selection"] = None
        curr_stage_idx += 1 
        
        


