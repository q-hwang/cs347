# cs347


# Backend Interaction flow

server.py gives a basic text interface for the pipepline 

## Overview and assumptitons

There are four stages: ["restaurant", "food items", "delivery methods", "tips"]

There are four levels for each stage:
0: do not display what is the selected option (not implemented now for debugging)
1: skip the stage and display the selected option at the summary page (default)
2: give options at the summary page 
3: user direct control (currently assuming user will just enter a name directly)


There are three edit actions (buttons) for each stage:
0: reroll/enter a chat message
1: increase control (-> recommendation -> direct control)
2: select a option among the recommended (give an index)

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

There are three edit actions (buttons):
0: reroll
1: increase control (-> recommendation -> direct control)
2: select a option among the recommended (give an index)
For option 0 and 1, user can additional specify a message that is passed to LLM.

Input format:
<edit_stage_id>,<edit_action_id>,<optional selection_id for 2/ message for 0>

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

1. We first get an intial guess of the levels using get_init_adapt_guess
2. We basically iteratively handle each stage according to the level, until we run into requiring user input
3. Get the user input. 
4. Roll back to handle the stage that user edited in 3. If this input also affects later stages, clear those selections for recomptutation as well
5. resume handeling stages sequentially from the edited stage; basically repeat from 2
6. user enter confirm. We collect the data for adaptation


## Elicit User preference
1. if user choose to increase level in a stage -> increase level recorded to what user ends up having
2. if user choose to not edit a stage -> decrease level gradually by 1/(expected number of round before user trusts this). This expected_number doubles every time the level of this stage is increased, so that this decay becomes slower and slower.

## Adapt to user preference
1. context adaptation: LLM gives an guess (always used in combination with others; the combination ratio is CONTEXT_WEIGHT=1)
2. global adaptation: if current user is new, we init from average of other user (average range: last SMOOTH=1)
3. user adaptation: if current user has history record, we use the average of this user (average range: last SMOOTH=1)


More details about code:
- display_summary_webpage: display the summary and get user input
- display_full_webpage: display the interface for direct manipulation and get user input
- state_dict/init_guess_state_dict: all the state information, basically records what is displayed in the summary page + dialog history for LLM
- debug flag prints out 1) what information LLM receives at each point, 2) which stage is being handled 2) state_dict (basically records what is displayed in the summary page + dialog history for LLM) 
- affects_stage: when changing the selection of stage A, all stages it affects will need to be rehandled

TODO:
- currently the level can only increase but not decrease. will implement the global data collection and adjustment.
- some actions might not be valid or should not be allowed e.g. should not allow confirm when user has not selected everything.
- have not tested starting from a different default
