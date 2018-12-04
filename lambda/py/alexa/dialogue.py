from random import choice

choose_card = [
    "what is the next card",
    "Next card please",
    "Focus, see the next card, be the next card, say the next card",
    "And the next card is ?",
    "next card",
    "let your mind go blank. Well not that blank. What card is next?",
    "Concentrate and say whats next",
    "You've got an idea forming in your head. Its a card called?",
    "Name that card",
]


def choose_a_card():
    choose_a_card = choice(choose_card)
    return choose_a_card
