# cs347

# Overview

`cs347-frontend/` contains frontend code and `server.py` contains the main backend code.

To run the code with frontend, run `npm install` and `npm start` in `cs347-frontend/`. Then run `server.py` in another terminal.

To run the code without frontend, modify `text_mode=True` in `server.py` and run it in the terminal.


# Backend Interaction flow

`server.py` contains the main backend code, and `llm.py` contains the code for rompting LLM as the AI agent. To try it, please put your openai key in `keys/key.txt`.

## Overview and assumptitons

There are four stages: ["restaurant", "food items", "delivery methods", "tips"]

There are four levels for each stage:
0: Skip the stage and display the selected option at the summary page (default)
1: give options at the summary page
2: user direct control (currently assuming user will just enter a name directly)


There are four backend actions for each stage:
0: enter a chat message and redo the AI action
1: increase control (-> recommendation -> direct control)
2: select a option among the recommended (give an index)
3: direct manipulation

## example flow

Example flow:

1. default + user directly agree
```
APP: Welcome! What do you want to eat?
User:anything!
Selected restaurant:
r1
Selected food items:
f2
Selected delivery_address:
d1
Selected tips:
t2
User:CONFIRM
```


2. user ask to edit stage 3 (tips)

Input format:
<edit_stage_id>,<edit_action_id>,<optional message to LLM for action 0/selection_id for 2/ user manual selection for action 3>

example 1 (recommendation)
```
APP: Welcome! What do you want to eat?
User:anything!
Selected restaurant:
r3
Selected food items:
f3
Selected delivery_address:
d3
Selected tips:
t3

User:1,1 #increase control on food
Selected restaurant:
r3
Selected food items:
['f2', 'f3']
Selected delivery_address:
d3
Selected tips:
t3

User:1,2,0 #select the first recommended food
Selected restaurant:
r3
Selected food items:
f2
Selected delivery_address:
d3
Selected tips:
t3
User:CONFIRM
```


example 2 (direct control)
```
AAPP: Welcome! What do you want to eat?
User:anything
Selected restaurant:
r2
Selected food items:
f1
Selected delivery_address:
d1
Selected tips:
t2
User:1,1
Selected restaurant:
r2
Selected food items:
['f2', 'f1']
Selected delivery_address:
d1
Selected tips:
t2
User:1,1
User give option:taco
Selected restaurant:
r2
Selected food items:
taco
Selected delivery_address:
d1
Selected tips:
t1
User:CONFIRM
```

## flow logic explained
1. We first get an intial guess of the control levels using `get_init_adapt_guess`
2. We basically iteratively handle each stage according to the level using `getUserInfo` and `continue_session`, until we run into requiring user input. Send the current selection to frontend to render via `display_summary_webpage`.
3. Get the user input from the frontend or termial input. 
4. Roll back to handle the stage that user edited in step 3 using `continue_session`. If this input also affects later stages, clear those selections for recomptutation as well
5. resume handeling stages sequentially from the edited stage, basically repeating from step 2
6. user enter confirm. We collect the data for adaptation by saving it in `histories/`


## Record user's preference
1. if user choose to increase level in a stage -> increase level recorded to what user ends up having
2. if user choose to not edit a stage -> decrease level gradually by 1/(expected number of round before user trusts this). This expected_number doubles every time the level of this stage is increased, so that this decay becomes slower and slower.


## Adapt to user preference
1. context adaptation: LLM gives an guess (always used in combination with others; the combination ratio is CONTEXT_WEIGHT=0.7)
2. global adaptation: if current user is new, we init from average of other user (average range: SMOOTH=3)
3. user adaptation: if current user has history record, we use the average of this user (average range: SMOOTH=3)



More details about code:
- display_summary_webpage: display the summary and get user input
- display_full_webpage: display the interface for direct manipulation and get user input
- state_dict/init_guess_state_dict: all the state information, basically records what is displayed in the summary page + dialog history for LLM
- debug flag prints out 1) what information LLM receives at each point, 2) which stage is being handled 2) state_dict (basically records what is displayed in the summary page + dialog history for LLM) 
- affects_stage: when changing the selection of stage A, all stages it affects will need to be rehandled

TODO:
- currently does not show the total price of the food
- maybe add a bit more explanation from LLM
