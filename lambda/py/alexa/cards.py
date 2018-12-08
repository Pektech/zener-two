"""All things related to the cards"""
from random import shuffle

cards = ["cross", "circle", "square", "waves", "star"] * 5


def shuffled_cards(cards):
    shuffle(cards)
    return cards


def final_score(score):
    if score < 2:
        return (
            f"Wow either you are really unlucky or have "
            f"some sort of anti-clairvoyance skill. You scored {score} "
        )
    elif 3 <= score <= 10:
        return (
            f" Not a bad score but the average person scores between 3 and 8. "
            f"Your final score was {score}. yeah pretty average"
        )
    else:
        return f" Wow {score} that is a really high score. Maybe you should play the lottery"
