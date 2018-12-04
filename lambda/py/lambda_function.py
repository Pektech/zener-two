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

from .alexa import data

required_slots = "game_length"
rounds_allowed = ["5", "10", "25"]

# Skill builder object

sb = SkillBuilder()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# request handlers launch bstython with bstpy lambda.py.lambda_function.handler


@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input):
    """Handler for Skill Launch."""

    speech_text = data.WELCOME
    return (
        handler_input.response_builder.speak(speech_text)
        .set_card(SimpleCard("Zener Cards", speech_text))
        .set_should_end_session(False)
        .response
    )


@sb.request_handler(
    can_handle_func=lambda handler_input: is_intent_name("ReadyGame")(handler_input)
    and handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED
)
def ready_game_handler(handler_input):

    # current_intent gets details about returned intent for checking use .name, .slots etc
    current_intent = handler_input.request_envelope.request.intent
    logger.info("In ReadyGameHandler")
    if (
        current_intent.slots["game_length"].name in required_slots
        and current_intent.slots["game_length"].value not in rounds_allowed
    ):
        print("need length")
        return (
            handler_input.response_builder.speak("ok how long a a game would you like")
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

    return handler_input.response_builder.add_directive(
        DelegateDirective(updated_intent=current_intent)
    ).response


@sb.request_handler(
    can_handle_func=lambda handler_input: is_intent_name("ReadyGame")(handler_input)
    and handler_input.request_envelope.request.dialog_state == DialogState.COMPLETED
)
def start_game(handler_input):
    return handler_input.response_builder.speak("now we can start the game").response


@sb.request_handler(
    can_handle_func=lambda input: is_intent_name("AMAZON.CancelIntent")(input)
    or is_intent_name("AMAZON.StopIntent")(input)
)
def cancel_and_stop_intent_handler(handler_input):
    """Single handler for Cancel and Stop Intent."""
    # type: (HandlerInput) -> Response
    speech_text = "Thanks for playing!!"

    handler_input.response_builder.speak(speech_text).set_should_end_session(True)
    return handler_input.response_builder.response


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


handler = sb.lambda_handler()
