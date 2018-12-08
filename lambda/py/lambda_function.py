import json
import logging

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.serialize import DefaultSerializer
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler,
    AbstractExceptionHandler,
    AbstractResponseInterceptor,
    AbstractRequestInterceptor,
)
from ask_sdk_core.utils import is_intent_name, is_request_type
from ask_sdk_core.response_helper import get_plain_text_content, get_rich_text_content

from ask_sdk_model.interfaces.display import (
    ImageInstance,
    Image,
    RenderTemplateDirective,
    ListTemplate1,
    BackButtonBehavior,
    ListItem,
    BodyTemplate2,
    BodyTemplate1,
)
from ask_sdk_model import (
    ui,
    Response,
    DialogState,
    Intent,
    SlotConfirmationStatus,
    Slot,
    IntentConfirmationStatus,
)
from ask_sdk_model.ui import simple_card, SimpleCard
from ask_sdk_model.dialog import ElicitSlotDirective, DelegateDirective

from .alexa import data, cards
from .alexa import dialogue

required_slots = "game_length"
rounds_allowed = ["5", "10", "25"]
DECK = cards.shuffled_cards(cards.cards)


# Skill builder object

sb = SkillBuilder()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# request handlers launch bstython with bstpy lambda.py.lambda_function.handler


@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input):
    """Handler for Skill Launch.
    Set session attributes for the game"""
    speech_text = data.WELCOME
    game_session_attr = handler_input.attributes_manager.session_attributes
    if not game_session_attr:
        game_session_attr["GAME_STATE"] = 0
        game_session_attr["SCORE"] = 0
        game_session_attr["DECK"] = DECK
        game_session_attr["CARD_COUNT"] = 0
        game_session_attr["last_speech"] = speech_text

    return (
        handler_input.response_builder.speak(speech_text)
        .ask(game_session_attr["last_speech"])
        .set_card(SimpleCard("Zener Cards", speech_text))
        .set_should_end_session(False)
        .response
    )


@sb.request_handler(
    can_handle_func=lambda handler_input: is_intent_name("ReadyGame")(handler_input)
    and handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED
)
def ready_game_handler(handler_input):
    # handles the start of the game setting up how many rounds
    # current_intent gets details about returned intent for checking use .name, .slots etc
    current_intent = handler_input.request_envelope.request.intent
    game_session_attr = handler_input.attributes_manager.session_attributes

    logger.info("In ReadyGameHandler")
    if (
        current_intent.slots["game_length"].name in required_slots
        and current_intent.slots["game_length"].value not in rounds_allowed
    ):

        return (
            handler_input.response_builder.speak(
                "ok how big a deck of cards should I use? "
                "Five is a short game, Fifteen is X minutes, Twenty-Five "
                "is the about XX minutes but gives the most accurate score "
            )
            .ask("five ten or fifteen")
            .add_directive(
                ElicitSlotDirective(
                    slot_to_elicit="game_length",
                    updated_intent=Intent(
                        name="ReadyGame",
                        confirmation_status=IntentConfirmationStatus.NONE,
                        slots={
                            "game_length": Slot(
                                name="game_length",
                                confirmation_status=SlotConfirmationStatus.NONE,
                            )
                        },
                    ),
                )
            )
            .response
        )
    # game_session_attr['DECK_SIZE'] = current_intent.slots["game_length"].value
    # game_session_attr['GAME_RUNNING'] = 1
    return handler_input.response_builder.add_directive(
        DelegateDirective(updated_intent=current_intent)
    ).response


@sb.request_handler(
    can_handle_func=lambda handler_input: is_intent_name("ReadyGame")(handler_input)
    and handler_input.request_envelope.request.dialog_state == DialogState.COMPLETED
)
def start_game(handler_input):
    game_session_attr = handler_input.attributes_manager.session_attributes
    game_session_attr["GAME_STATE"] = "RUNNING"
    current_intent = handler_input.request_envelope.request.intent
    game_session_attr["DECK_SIZE"] = current_intent.slots["game_length"].value
    return handler_input.response_builder.speak(
        "now we can start the game.  what card am I thinking off"
    ).response


def currently_playing(handler_input):
    """Function that acts as can handle for game state."""
    # type: (HandlerInput) -> bool
    is_currently_playing = False
    session_attr = handler_input.attributes_manager.session_attributes

    if "GAME_STATE" in session_attr and session_attr["GAME_STATE"] == "RUNNING":
        is_currently_playing = True

    return is_currently_playing


@sb.request_handler(
    can_handle_func=lambda input: currently_playing(input)
    and is_intent_name("Zener")(input)
)
def play_game(handler_input):
    current_intent = handler_input.request_envelope.request.intent
    game_session_attr = handler_input.attributes_manager.session_attributes
    if "guess" in current_intent.slots:
        guess = current_intent.slots["guess"].value

    score = game_session_attr["SCORE"]
    game_deck = game_session_attr["DECK"]
    deck_size = int(game_session_attr["DECK_SIZE"])
    card_count = int(game_session_attr["CARD_COUNT"])
    print(guess)
    if guess is None or guess not in ["star", "cross", "square", "waves", "circle"]:
        output = data.ERROR
        game_session_attr["last_speech"] = output
        handler_input.response_builder.speak(output).ask(output)
        return handler_input.response_builder.response
    if card_count < (deck_size - 1):

        choose_card = dialogue.choose_a_card()

        output = choose_card
        game_session_attr["last_speech"] = output
        # print(game_deck[card_count], guess, "score = ", score)
        if guess == game_deck[card_count]:
            score += 1
        card_count += 1
        game_session_attr["CARD_COUNT"] = card_count
        game_session_attr["SCORE"] = score
        game_session_attr["last_speech"] = output
        handler_input.response_builder.speak(output).ask(
            "Please choose from Star, Cross, Waves, Square or Circle"
        )
        return handler_input.response_builder.response
        # return handler_input.response_builder.speak(output).response
    score = cards.final_score(score)
    output = f"Okay game over <break strength='strong' />{score}"
    return handler_input.response_builder.speak(output).response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(input):
    """Single handler for Cancel and Stop Intent."""
    # type: (HandlerInput) -> Response
    speech_text = data.HELP

    return (
        input.response_builder.speak(speech_text).set_should_end_session(False).response
    )


@sb.request_handler(
    can_handle_func=lambda input: is_intent_name("AMAZON.CancelIntent")(input)
    or is_intent_name("AMAZON.StopIntent")(input)
)
def cancel_and_stop_intent_handler(input):
    """Single handler for Cancel and Stop Intent."""
    # type: (HandlerInput) -> Response
    speech_text = "Thanks for playing!!"

    input.response_builder.speak(speech_text).set_should_end_session(True)
    return input.response_builder.response


@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input):
    """Handler for Session End."""
    # type: (HandlerInput) -> Response
    logger.info(
        "Session ended with reason: {}".format(
            handler_input.request_envelope.request.reason
        )
    )
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=lambda input: True)
def unhandled_intent_handler(handler_input):
    """Handler for all other unhandled requests."""
    # type: (HandlerInput) -> Response
    speech = "Sorry I do not know that particular card. Please choose from Star, Cross, Waves, Square or Circle"
    handler_input.response_builder.speak(speech).ask(speech)
    return handler_input.response_builder.response


@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception):
    """Catch all exception handler, log exception and
    respond with custom message.
    """
    # type: (HandlerInput, Exception) -> Response
    logger.error(exception, exc_info=True)
    speech = "Sorry, I can't understand that. Please say again!!"
    handler_input.response_builder.speak(speech).ask(speech)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.FallbackIntent"))
def fallback_handler(handler_input):
    """AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    """
    # type: (HandlerInput) -> Response
    speech = "The Hello World skill can't help you with that.  " "You can say hello!!"
    reprompt = "You can say hello!!"
    handler_input.response_builder.speak(speech).ask(reprompt)
    return handler_input.response_builder.response


@sb.global_response_interceptor()
def log_response(handler_input, response):
    """Response logger."""
    # type: (HandlerInput, Response) -> None
    logger.info("Response: {}".format(response))


handler = sb.lambda_handler()
