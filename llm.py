
import openai
import json

with open("keys/key.txt", "r") as f:
    key = f.read().strip()
openai.api_key = key

menus = json.load(open("menu.json"))


def init_llm_level_guess(user_input):
    # e.g. I want to order some cake and I would like you to show me some of the options of the restaurant and types of the cakes
    prompt = f"""Predict what is the user's preferred level of control over an AI recommender for each stage of ordering food from Doordash based on their input. There are four stages: selecting restaurant, selecting food, selecting delivery method, and selecting tips. Each stage has four levels of control: 0 for automatic AI selecting, 1 for showing AI recommendations, and 2 for full user control. Note that we prefer having lower levels of controls overall to save users' time.

User input: I am excited about ordering something new today
Levels: 1 2 0 1

User input: Just deliver me a burger
Levels: 0 0 0 0

User input: I want to try some tuna sashimi but I am not sure where to order from
Levels: 1 0 1 0

User input: I want some mexican food
Levels: 0 1 0 0

User input: I am hungr now, anything is fine
Levels: 0 0 0 0

User input: {user_input.strip()}
Levels:"""
    completion = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=10,
        temperature=0.1,
        n=1,
        stop="\n"
    )['choices'][0]['text']

    return [int(x) for x in completion.strip().split(" ")]


def build_prompt_history(word, local_feedback=None):
    prompt_history = "User Input: Anything"
    if local_feedback is not None:
        prompt_history = ""
        for l in local_feedback:
            prompt_history += f"User Input: {l[0]}"
            if len(l) > 1:
                if type(l[1]) == list:
                    l[1] = ", ".join(l[1])
                prompt_history += f"\nPreviously suggested {word}: {l[1]}\n\n"

    prompt_history += "\nSuggested " + word + ":"
    return prompt_history


def get_llm_restaurant_recommendation(state_dict, local_feedback=None):
    prompt_history = "User Input: Anything"
    if local_feedback is not None:
        prompt_history = build_prompt_history("Restaurants", local_feedback)

    restaurants = []
    for name, menu in menus.items():
        restaurants.append(name)

    prompt = f"""Suggest three restaurants for the user to order from based on their input, ranked from more suggested to less suggested. The restaurants are: {", ".join(restaurants)}. The sugggested three restaurants should be separated by commas.

{prompt_history}"""
    # print(prompt)

    completion = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=100,
        temperature=0.1,
        n=1,
        stop="\n"
    )['choices'][0]['text']

    return [x.strip() for x in completion.strip().split(",")]


def get_llm_food_recommendation(state_dict, local_feedback=None):

    prompt_history = "User Input: Anything"
    if local_feedback is not None:
        prompt_history = build_prompt_history("Dishes", local_feedback)

    restaurant = state_dict[0]["selection"]
    dishes = list(menus[restaurant].keys())

    prompt = f"""Suggest three dishes combo for the user based on their input, ranked from more suggested to less suggested. Each dish combo should inlcude 1 to three dishes, separated by commas. The dishes are: {", ".join(dishes)}. The sugggested three dishes should be separated by semicolons.

{prompt_history}"""
    # print(prompt)

    completion = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=100,
        temperature=0.1,
        n=1,
        stop="\n"
    )['choices'][0]['text']

    return [x.strip() for x in completion.strip().split(";")]


def get_llm_delivery_option_recommendation(state_dict, local_feedback=None):
    prompt_history = "User Input: Anything"
    if local_feedback is not None:
        prompt_history = build_prompt_history("Method", local_feedback)

    restaurant = state_dict[0]["selection"]

    prompt = f"""The user has chosen to order from {restaurant}. Suggest three delivery methods from Pickup, Pickup in 15 min, Pickup in 30 min, Delivery to home, or Delivery to work for the user based on their input, ranked from more suggested to less suggested. The sugggested three methods should be separated by commas.

{prompt_history}"""
    # print(prompt)

    completion = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=10,
        temperature=0.1,
        n=1,
        stop="\n"
    )['choices'][0]['text']

    return [x.strip() for x in completion.strip().split(",")]


def get_llm_tips_option_recommendation(state_dict, local_feedback=None):
    prompt_history = "User Input: Anything"
    if local_feedback is not None:
        prompt_history = build_prompt_history("Tips Amount", local_feedback)

    restaurant = state_dict[0]["selection"]
    dish = state_dict[1]["selection"]

    prompt = f"""The user has chosen to order {dish} from {restaurant} via the selected delivery option \"{state_dict[2]["selection"]}\". Suggest three tips amount in us dollar for the user based on their input, ranked from more suggested to less suggested. The sugggested three tips amount should be separated by commas.

{prompt_history}"""
    # print(prompt)

    completion = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=10,
        temperature=0.1,
        n=1,
        stop="\n"
    )['choices'][0]['text']

    return [x.strip() for x in completion.strip().split(",")]
