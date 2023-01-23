# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"
import time

from typing import Any, Text, Dict, List

from rasa.core.agent import Agent
from rasa.core.channels import OutputChannel
from rasa.core.nlg import NaturalLanguageGenerator
from rasa.core.policies.fallback import FallbackPolicy
from rasa.core.policies.policy import Policy
from rasa.shared.core.trackers import DialogueStateTracker
from rasa.shared.core.events import Event
from rasa_sdk.events import SlotSet, FollowupAction, ActiveLoop
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

from thefuzz import fuzz
from thefuzz import process

import re
import requests
import random

domainUrl = "http://datavisualizationinlinguistics.herokuapp.com:8000/"
from cryptography.fernet import Fernet


def encrypt(message: bytes, key: bytes) -> bytes:
    return Fernet(key).encrypt(message)


def decrypt(token: bytes, key: bytes) -> bytes:
    return Fernet(key).decrypt(token)


class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_hello_world"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Hello World!")

        return []


# class storeSessionSlots(Action):
#
#     def name(self) -> Text:
#         return "action_store_session_slots"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         print(tracker.latest_message['entities'])
#
#         return [SlotSet("csrftoken", "text2"),SlotSet("csrfmiddlewaretoken", "text3")]

# class ActionLogout(Action):
#
#     def name(self) -> Text:
#         return "action_logout"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         if (tracker.get_slot("sessionid") and tracker.get_slot("sessionid") != "None"):
#             response = requests.get(domainUrl + "logout/", params={"csrfmiddlewaretoken": tracker.get_slot("csrfmiddlewaretoken")},
#                          cookies={"sessionid": tracker.get_slot("sessionid"),
#                                   "csrftoken": tracker.get_slot("csrftoken")})
#         else:
#             dispatcher.utter_message(
#                 text="It is not possible to close a session that does not exist, you are not logged in...")
#             return []
#
#         if (response):  # successful response
#             dispatcher.utter_message(text="intent_logout")
#             return [SlotSet("sessionid", None)]
#         else:
#             dispatcher.utter_message(text="An error has occurred")
#             return []

class ActionLogout(Action):

    def name(self) -> Text:
        return "action_logout"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="intent_logout")
        return [SlotSet("sessionid", None)]


class ActionCheckSessionLogin(Action):

    def name(self) -> Text:
        return "action_check_session_login"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if tracker.get_slot("user_is_logged_in"):
            return [FollowupAction("utter_logout_to_login")]
        else:
            return [FollowupAction("login_form")]


class ActionCheckSessionSignup(Action):

    def name(self) -> Text:
        return "action_check_session_signup"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if tracker.get_slot("user_is_logged_in"):
            return [FollowupAction("utter_logout_to_signup")]
        else:
            return [FollowupAction("signup_form")]


class ActionLogoutToLoginCancellation(Action):

    def name(self) -> Text:
        return "action_logout_to_login_cancellation"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="I will keep your current session open")
        return [SlotSet("username", None), SlotSet("password", None)]


class ActionLogoutToSignupCancellation(Action):

    def name(self) -> Text:
        return "action_logout_to_signup_cancellation"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Okey! I will not log you out")
        return [SlotSet("username", None), SlotSet("password", None), SlotSet("password_confirmation", None)]


# class ActionLogin(Action):
#
#     def name(self) -> Text:
#         return "action_login"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         if (tracker.get_slot("sessionid") and tracker.get_slot("sessionid") != "None"):
#             dispatcher.utter_message(
#                 text="You are already logged in, do you want me to log you out to start a new session?")
#             # return [SlotSet("new_session", True)]
#             return []
#         else:
#             key = b'ZeuY3kEaYn2XkyPQPQKgDmDeDRJfKYM3-tTx_5NmMm4='
#             response = requests.post(domainUrl + "login/", data={"rasaserver": "true",
#                     "csrfmiddlewaretoken": tracker.get_slot("csrfmiddlewaretoken"),
#                     "username": encrypt(tracker.get_slot("username").encode(), key).decode(),
#                     "password": encrypt(tracker.get_slot("password").encode(), key).decode()},
#                     cookies={"csrftoken": tracker.get_slot("csrftoken")})
#
#         if (response):  # successful response
#             dispatcher.utter_message(text='intent_login,' + encrypt(tracker.get_slot("username").encode(), key).decode() + ',' + encrypt(tracker.get_slot("password").encode(), key).decode())
#             return []
#         else:
#             dispatcher.utter_message(text="An error has occurred")
#             return [SlotSet("sessionid", None)]
#
#
# class ActionNewSession(Action):
#
#     def name(self) -> Text:
#         return "action_new_login"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         if (tracker.get_slot("sessionid") and tracker.get_slot("sessionid") != "None"):
#             response = requests.get(domainUrl + "logout/", params={"csrfmiddlewaretoken": tracker.get_slot("csrfmiddlewaretoken")},
#                          cookies={"sessionid": tracker.get_slot("sessionid"),
#                                   "csrftoken": tracker.get_slot("csrftoken")})
#         else:
#             dispatcher.utter_message(
#                 text="I have lost the previous session, but you can start a new session anyway.")
#
#         if (response):  # successful response
#             dispatcher.utter_message(text="intent_logout")
#         else:
#             dispatcher.utter_message(text="An error has occurred")
#
#         return [SlotSet("new_session", False)]
#
# class ActionSignup(Action):
#
#     def name(self) -> Text:
#         return "action_signup"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         if (tracker.get_slot("sessionid") and tracker.get_slot("sessionid") != "None"):
#             dispatcher.utter_message(
#                 text="You are logged in, do you want me to log you out so you can register as another user?")
#             # return [SlotSet("new_session", True)]
#             return []
#         else:
#             key = b'JlgbJKpxVhwF3NXJf_n-lt4c4AvdCATnuXYDK4xivPY='
#             response = requests.post(domainUrl + "signup/", data={"rasaserver": "true",
#                         "csrfmiddlewaretoken": tracker.get_slot("csrfmiddlewaretoken"),
#                         "username": encrypt(tracker.get_slot("username").encode(), key).decode(),
#                         "password1": encrypt(tracker.get_slot("password").encode(), key).decode(),
#                         "password2": encrypt(tracker.get_slot("password_confirmation").encode(), key).decode()},
#                         cookies={"csrftoken": tracker.get_slot("csrftoken")})
#
#         if (response):  # successful response
#             dispatcher.utter_message(text='intent_signup,' + encrypt(tracker.get_slot("username").encode(), key).decode()
#                                           + ',' + encrypt(tracker.get_slot("password").encode(), key).decode()
#                                           + ',' + encrypt(tracker.get_slot("password_confirmation").encode(), key).decode())
#             return []
#         else:
#             dispatcher.utter_message(text="An error has occurred")
#             return [SlotSet("sessionid", None)]

def user_wants_to_exit_form(tracker):
    return tracker.latest_message['intent'].get('name') == 'cancel_form' or tracker.latest_message['intent'].get(
        'name') == 'deny'


class ActionLogin(Action):

    def name(self) -> Text:
        return "action_login"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if tracker.get_slot("username") == None:
            dispatcher.utter_message(text="I have cancelled the form")
            return []
        else:
            key = b'ZeuY3kEaYn2XkyPQPQKgDmDeDRJfKYM3-tTx_5NmMm4='
            dispatcher.utter_message(
                text='intent_login,' + encrypt(tracker.get_slot("username").encode(), key).decode() + ',' + encrypt(
                    tracker.get_slot("password").encode(), key).decode())
            return [SlotSet("username", None), SlotSet("password", None)]


class ValidateLoginForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_login_form"

    def validate_username(self,
                          slot_value: Any,
                          dispatcher: CollectingDispatcher,
                          tracker: Tracker,
                          domain: DomainDict,
                          ) -> Dict[Text, Any]:

        if user_wants_to_exit_form(tracker):
            return {"requested_slot": None, "username": None}

    def validate_password(self,
                          slot_value: Any,
                          dispatcher: CollectingDispatcher,
                          tracker: Tracker,
                          domain: DomainDict,
                          ) -> Dict[Text, Any]:

        if user_wants_to_exit_form(tracker):
            return {"requested_slot": None, "username": None, "password": None}


class ActionSignup(Action):

    def name(self) -> Text:
        return "action_signup"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if tracker.get_slot("username") == None:
            dispatcher.utter_message(text="I have cancelled the form")
            return []
        else:
            key = b'JlgbJKpxVhwF3NXJf_n-lt4c4AvdCATnuXYDK4xivPY='
            dispatcher.utter_message(
                text='intent_signup,' + encrypt(tracker.get_slot("username").encode(), key).decode()
                     + ',' + encrypt(tracker.get_slot("password").encode(), key).decode()
                     + ',' + encrypt(tracker.get_slot("password_confirmation").encode(), key).decode())
            return [SlotSet("username", None), SlotSet("password", None), SlotSet("password_confirmation", None)]


class ValidateSignupForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_signup_form"

    def validate_username(self,
                          slot_value: Any,
                          dispatcher: CollectingDispatcher,
                          tracker: Tracker,
                          domain: DomainDict,
                          ) -> Dict[Text, Any]:

        if user_wants_to_exit_form(tracker):
            return {"requested_slot": None, "username": None}

        # Validate username value.
        # make a pattern
        pattern = "^[A-Za-z0-9@.+-_]*$"

        if len(slot_value) > 150:
            dispatcher.utter_message(
                text="Ensure this value has at most 150 characters (it has " + str(len(slot_value)) + ")")
        elif not re.match(pattern, slot_value):
            dispatcher.utter_message(
                text="Enter a valid username. This value may contain only letters, numbers, and @/./+/-/_ characters.")
        else:
            # validation succeeded, set the value of the "username" slot to value
            return {"username": slot_value}

        # validation failed, set this slot to None so that the
        # user will be asked for the slot again
        return {"username": None}

    @staticmethod
    def common_passwords_db() -> List[Text]:
        # Database of common passwords
        return ["12345", "123456", "1234567", "12345678", "123456789", "qwerty", "password", "123123", "123123123",
                "1234567890", "qwerty123", "password1", "football", "monkey", "baseball", "dragon"]

    def validate_password(self,
                          slot_value: Any,
                          dispatcher: CollectingDispatcher,
                          tracker: Tracker,
                          domain: DomainDict,
                          ) -> Dict[Text, Any]:

        if user_wants_to_exit_form(tracker):
            return {"requested_slot": None, "username": None, "password": None}

        # Validate password value.
        succeed = True

        if slot_value == tracker.get_slot("username"):
            dispatcher.utter_message(text="The password is too similar to the username.")
            succeed = False
        if len(slot_value) < 8:
            dispatcher.utter_message(text="This password is too short. It must contain at least 8 characters.")
            succeed = False
        # Check if the password is within a dictionary of common passwords
        # or if the password consists of the same character repeated multiple times
        if slot_value.lower() in self.common_passwords_db() or slot_value.lower() == len(slot_value) * slot_value[
            0].lower():
            dispatcher.utter_message(text="This password is too common.")
            succeed = False
        if slot_value.isdigit():
            dispatcher.utter_message(text="This password is entirely numeric.")
            succeed = False
        if succeed:
            # validation succeeded, set the value of the "password" slot to value
            return {"password": slot_value}
        else:
            # validation failed, set this slot to None so that the
            # user will be asked for the slot again
            return {"password": None}

    def validate_password_confirmation(self,
                                       slot_value: Any,
                                       dispatcher: CollectingDispatcher,
                                       tracker: Tracker,
                                       domain: DomainDict,
                                       ) -> Dict[Text, Any]:

        if user_wants_to_exit_form(tracker):
            return {"requested_slot": None, "username": None, "password": None, "password_confirmation": None}


class ActionOpenDocument(Action):

    def name(self) -> Text:
        return "action_open_document"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if tracker.get_slot("document_requested") == None:
            dispatcher.utter_message(text="I have cancelled the form")
            return []
        else:
            document_requested_value = tracker.get_slot("document_requested")

            for e in tracker.latest_message['entities']:
                if e['entity'] == 'document_requested':
                    document_requested_value = e['value']

            dispatcher.utter_message(text='intent_open_document,' + document_requested_value)
            return [SlotSet("document_requested", None)]


class ValidateDocumentSelectionForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_document_selection_form"

    def validate_document_requested(self,
                                    slot_value: Any,
                                    dispatcher: CollectingDispatcher,
                                    tracker: Tracker,
                                    domain: DomainDict,
                                    ) -> Dict[Text, Any]:
        if user_wants_to_exit_form(tracker):
            return {"requested_slot": None, "document_requested": None}


class ActionGreet(Action):

    def name(self) -> Text:
        return "action_greet"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        nickname_value = tracker.get_slot("nickname")
        first_login_value = None
        greet_again_value = None
        for e in tracker.latest_message['entities']:
            if e['entity'] == 'greet_again':
                greet_again_value = e['value'] == "True"
            elif e['entity'] == 'first_login':
                first_login_value = e['value'] == "True"

        messages_not_logged = ["Hey! Nice to see you here, I am a Chatbot here to help you 😄", "Hello! I'm a Chatbot here to help if you need me 😄",
                               "Hi, I am a Chatbot here to guide you 😄",
                               "Hello there, I am a Chatbot here to help you 😄"] if not greet_again_value else ["How else can I help you? 😉",
                                                                                "What else can I do for you? 😉"]

        if tracker.get_slot("sessionid") and tracker.get_slot("sessionid") != "None":
            if nickname_value:
                messages = ["Hey, " + nickname_value + ". Nice to see you! 😄",
                            "Hi, " + nickname_value + ". How are you? 😄",
                            "Hello, " + nickname_value + ". I'm here if you need me 😄"] if not greet_again_value else \
                    ["Hey, " + nickname_value + ". How else can I help you? 😉",
                     "Hi, " + nickname_value + ". What else can I do for you? 😉"]
                dispatcher.utter_message(text=random.choice(messages))

                if first_login_value:
                    # Save in the database that the user has made his first chat connection
                    response_firstchat = requests.post(domainUrl + "save_first_login/",
                                                       data={"csrfmiddlewaretoken": tracker.get_slot(
                                                           "csrfmiddlewaretoken"),
                                                           "first_login": False},
                                                       cookies={"sessionid": tracker.get_slot("sessionid"),
                                                                "csrftoken": tracker.get_slot("csrftoken")})

                    if response_firstchat:  # successful response
                        return [FollowupAction("utter_help_what_can_you_do"), SlotSet("nickname", nickname_value),
                                SlotSet("first_login", first_login_value), SlotSet("user_is_logged_in", True)]
                    else:
                        dispatcher.utter_message(text="An error has occurred")
                        return []
                else:
                    return [SlotSet("nickname", nickname_value), SlotSet("first_login", first_login_value),
                            SlotSet("user_is_logged_in", True)]
            else:
                dispatcher.utter_message(text=random.choice(messages_not_logged))

                return [SlotSet("nickname", nickname_value), SlotSet("first_login", first_login_value),
                        SlotSet("user_is_logged_in", False)]

        # If the user is not logged in or does not have a nickname
        dispatcher.utter_message(text=random.choice(messages_not_logged))
        return [SlotSet("nickname", nickname_value), SlotSet("user_is_logged_in", False)]


class ActionGenerateResponseMessage(Action):

    def name(self) -> Text:
        return "action_generate_response_message"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text_msg = None
        next_action = None
        for e in tracker.latest_message['entities']:
            if e['entity'] == 'response_message':
                text_msg = e['value']
            elif e['entity'] == 'next_action':
                next_action = e['value']

        dispatcher.utter_message(text=text_msg)
        if next_action and next_action != 'None':
            return [FollowupAction(next_action)]
        return []


filters_ids = {
    "not toxic": "highlight-toxicity-0", "non toxic": "highlight-toxicity-0", "very toxic": "highlight-toxicity-3",
    "mildly toxic": "highlight-toxicity-1",
    "toxic": "highlight-toxicity-2", "positive stance": "highlight-stance-positive",
    "negative stance": "highlight-stance-negative", "neutral stance": "highlight-stance-neutral",
    "target person": "highlight-target-person", "target group": "highlight-target-group",
    "stereotype": "highlight-target-stereotype", "all targets": "selectAll-target",
    "constructiveness": "highlight-features-constructiveness", "argumentation": "highlight-features-argumentation",
    "sarcasm": "highlight-features-sarcasm", "mockery": "highlight-features-mockery",
    "intolerance": "highlight-features-intolerance", "improper language": "highlight-features-improper-language",
    "insult": "highlight-features-insult", "aggressiveness": "highlight-features-aggressiveness",
    "all features": "selectAll-features"
}
choices = ["not toxic", "non toxic", "very toxic", "mildly toxic", "toxic", "positive stance", "negative stance",
           "neutral stance", "target person", "target group", "stereotype", "all targets", "constructiveness",
           "argumentation", "sarcasm", "mockery", "intolerance", "improper language", "insult", "aggressiveness",
           "all features"]
threshold = 60


class ActionHighlightCheck(Action):

    def name(self) -> Text:
        return "action_highlight_check"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        values = []
        for e in tracker.latest_message['entities']:
            if e['entity'] == 'filter_name':
                result, confidence = process.extractOne(e['value'], choices)
                if confidence >= threshold:
                    values.append(filters_ids[result])
        dispatcher.utter_message(text="intent_filter," + ';'.join(values))

        return [SlotSet("previous_filters", values)]


class ActionHighlightCheckLast(Action):

    def name(self) -> Text:
        return "action_highlight_check_last"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if not tracker.get_slot("previous_filters"):
            dispatcher.utter_message(text="You have not interacted with any filter through the chat yet")
        else:
            dispatcher.utter_message(text="intent_filter," + ';'.join(tracker.get_slot("previous_filters")))
        return []


class ActionHighlightSwitch(Action):

    def name(self) -> Text:
        return "action_highlight_switch"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        values = []
        for e in tracker.latest_message['entities']:
            if e['entity'] == 'filter_name':
                result, confidence = process.extractOne(e['value'], choices)
                if confidence >= threshold:
                    values.append(filters_ids[result])
        dispatcher.utter_message(text="intent_filter_switch," + ';'.join(values))

        return [SlotSet("previous_filters", values)]


class ActionHighlightSwitchLast(Action):

    def name(self) -> Text:
        return "action_highlight_switch_last"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if not tracker.get_slot("previous_filters"):
            dispatcher.utter_message(text="You have not interacted with any filter through the chat yet")
        else:
            dispatcher.utter_message(text="intent_filter_switch," + ';'.join(tracker.get_slot("previous_filters")))
        return []


class ActionHighlightUncheck(Action):

    def name(self) -> Text:
        return "action_highlight_uncheck"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        values = []
        for e in tracker.latest_message['entities']:
            if e['entity'] == 'filter_name':
                result, confidence = process.extractOne(e['value'], choices)
                if confidence >= threshold:
                    values.append(filters_ids[result])
        dispatcher.utter_message(text="intent_filter_uncheck," + ';'.join(values))

        return [SlotSet("previous_filters", values)]


class ActionHighlightUncheckLast(Action):

    def name(self) -> Text:
        return "action_highlight_uncheck_last"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if not tracker.get_slot("previous_filters"):
            dispatcher.utter_message(text="You have not interacted with any filter through the chat yet")
        else:
            dispatcher.utter_message(text="intent_filter_uncheck," + ';'.join(tracker.get_slot("previous_filters")))
        return []

    # class PrintLetterByLetter(Action):
    #     def name(self) -> Text:
    #         return "action_print_letter_by_letter"
    #
    #     def run(self, dispatcher: CollectingDispatcher,
    #             tracker: Tracker,
    #             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
    #         message = tracker.latest_message.get("text")
    #         for letter in message:
    #             dispatcher.utter_message(letter)
    #             time.sleep(0.1)
    #

    # class ActionSendPopupShownMessage(Action):
    #
    #     def name(self) -> Text:
    #         return "action_send_popup_shown_message"
    #
    #     def run(self, dispatcher: CollectingDispatcher,
    #             tracker: Tracker,
    #             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
    #         print("Popup shown action called")
    #         message = "Hello! The pop-up window you requested has been opened for the first time."
    #         dispatcher.utter_message(text=message)
    #         return []


class ActionSendPopupShownMessage(Action):
    def name(self) -> Text:
        return "action_send_popup_shown_message"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        popup_shown = tracker.get_slot("popup_shown")
        if not popup_shown:
            message = "Hello! The pop-up window you requested has been opened for the first time."
            dispatcher.utter_message(text=message)
            return [SlotSet("popup_shown", True)]
        print(f"popup_shown: {tracker.get_slot('popup_shown')}")
        return []



class Options(Action):

  def name(self) -> Text:
    return "action_options"

  def run(
    self,
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
    domain: DomainDict
  ) -> List:

    if tracker.slots.get("is_new_user", False):
      if tracker.slots.get("account_type", None) == "primary":
        dispatcher.utter_message(
          response="utter_options_new_user_primary"
        )
      elif tracker.slots.get("account_type", None) == "secondary":
        dispatcher.utter_message(
          response="utter_options_new_user_secondary"
        )
    else:
      dispatcher.utter_message(
        response="utter_options_return_user"
      )

    return []