# cs347

server.py gives a basic text interface for mocking the pipepline with fake llm suggestions and fake menus. Fake LLM just give 2 random suggestions from the fake menu (e.g. f1,f2,f3)

There are four stages: ["restaurant", "food items", "delivery_address", "tips"]

There are four levels for each stage:
0: do not display what is the selected option (not implemented now for debugging)
1: skip the stage and display the selected option at the summary page (default)
2: give options at the summary page 
3: user direct control (currently assuming user will just enter a name directly)


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
<edit_stage_id>,<edit_action_id>,<optional selection_id for 2/message for 0 or 1>

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
