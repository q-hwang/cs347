

STAGES = ["restaurant", "food items", "delivery_address", "tips"]

def get_user_input():
    input_string = input('User:')
    inputs = input_string.split(",") 
    confirm = inputs[0] == "T"
    edit_stage = int(inputs[1])
    button  = int(inputs[2])
    message = inputs[3]
    return confirm, edit_stage, button, message 

def get_llm_restaurant_recommendation(level, global_prompt=None, local_feedback=None):
    return ["r1", "r2"]

def get_llm_food_recommendation(level, global_prompt=None, local_feedback=None):
    return ["f1", "f2"]

def get_llm_delivery_option_recommendation(level, global_prompt=None, local_feedback=None):
    return ["d1", "d2"]

def get_llm_tips_option_recommendation(level, global_prompt=None, local_feedback=None):
    return ["t1", "t2"]

init_guess_state_dict = [
    {
        "level": 1, 
        "affects_stage": [1,3],
        "handeler": get_llm_restaurant_recommendation, 
        "selection": None,
        "local_feedback": None
    },
    {
        "level": 1, 
        "affects_stage": [3],
        "handeler": get_llm_food_recommendation, 
        "selection": None,
        "local_feedback": None
    },
    {
        "level": 1, 
        "affects_stage": [],
        "handeler": get_llm_delivery_option_recommendation, 
        "selection": None,
        "local_feedback": None
    },
    {
        "level": 1, 
        "affects_stage": [],
        "handeler": get_llm_tips_option_recommendation, 
        "selection": None,
        "local_feedback": None
    }
]

def display_summary_webpage(state_dict):
    for s in range(len(STAGES)):
        selection = state_dict[s]["selection"] 
        if selection is None:
            break
        print(f"Selected {STAGES[s]}:" + selection)
   
    # get user response: 
        # selected_option
        # local_feedback (chat)
        # reroll, increase_level
    confirm, edit_stage, button, message = get_user_input()
    selected_option, local_feedback, reroll, increase_level

    if button == 0:
        reroll = True
    if button == 1:
        increase_level = True
    if button == 2:
        selected_option = message
    else:
        local_feedback = message

    return confirm, edit_stage, selected_option, local_feedback, reroll, increase_level



def display_full_webpage(state_dict, curr_stage_idx):
    
    # get user response: 
        # selected_option
    return selected_option


if __name__ == "__main__":
    print("APP: Welcome! What do you want to eat?")
    init_input = get_user_input()
    state_dict = init_guess_state_dict
    webpage_state = display_full_webpage(state_dict, -1)

    # initial handeling
    curr_stage_idx = 0
    while True:
        if curr_stage_idx == len(STAGES):
            # user engaging screen
            confirm, edit_stage, selected_option, local_feedback, reroll, increase_level = display_summary_webpage(state_dict, curr_stage_idx)
            if confirm:
                # TODO: check all stages are filled up
                exit()
            else:
                if selected_option is not None:
                    state_dict[edit_stage]["selection"] = selected_option
                    for s in state_dict[edit_stage]["affects_stage"]:
                        state_dict[edit_stage]["selection"] = None
                    for s in range(len(STAGES)):
                        if state_dict[edit_stage]["selection"] is None:
                            curr_stage_idx = s
                else:
                    curr_stage_idx = edit_stage
                    state_dict[curr_stage_idx]["local_feedback"] = local_feedback
                    if increase_level:
                        state_dict[curr_stage_idx]["level"] += 1
                continue

    
        stage_name = STAGES[curr_stage_idx]
        stage_level = state_dict[curr_stage_idx]["level"]
        if stage_level == 3:
            # direct maipulation:
            selected_option = display_full_webpage(state_dict, curr_stage_idx)
            state_dict[curr_stage_idx]["selection"] = selected_option
        if stage_level  == 2:
            # recommend to user

            local_feedback = state_dict[curr_stage_idx]["local_feedback"]
            llm_suggestions = state_dict[curr_stage_idx]["handeler"](stage_level, init_input, local_feedback)
            state_dict[curr_stage_idx]["selection"] = llm_suggestions
            curr_stage_idx = len(STAGES)
            continue

        if stage_level == [0, 1]:
            # skip

            local_feedback = state_dict[curr_stage_idx]["local_feedback"]
            llm_suggestions = state_dict[curr_stage_idx]["handeler"](stage_level, init_input, local_feedback)
            state_dict[curr_stage_idx]["selection"] = llm_suggestions[0]
        
        curr_stage_idx += 1 
        
        


