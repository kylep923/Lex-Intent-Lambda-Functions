import json
import dateutil.parser
import datetime
import time
import os
import math
import random
import logging
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from firebase import firebase

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

"""--- Global Variables ---"""

api_key = '8FYmwxXYXU_kd11xclK0HQ'
grid_name = 'WestAcersDemo'
location = ''
firebase = firebase.FirebaseApplication('https://wayfinding-9f0fe.firebaseio.com/', None)




""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message, response_card):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message,
            'responseCard': response_card
        }
    }


def confirm_intent(session_attributes, intent_name, slots, message, response_card):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots,
            'message': message,
            'responseCard': response_card
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


def build_response_card(title, subtitle, options):
    """
    Build a responseCard with a title, subtitle, and an optional set of options which should be displayed as buttons.
    """
    buttons = None
    if options is not None:
        buttons = []
        for i in range(min(5, len(options))):
            buttons.append(options[i])

    return {
        'contentType': 'application/vnd.amazonaws.card.generic',
        'version': 1,
        'genericAttachments': [{
            'title': title,
            'subTitle': subtitle,
            'buttons': buttons
        }]
    }
    
""" --- Helper Functions --- """

def is_valid_command(command):
    valid_commands = ['rotate', 'next slide', 'mute', 'volume up', 'volume down']
    results = process.extract(command, valid_commands, limit=2)
    print results
    return command



""" --- Functions that control the bot's behavior --- """

def send_command(intent_request):
    command = intent_request['currentIntent']['slots']['command_slot']
    slots = intent_request['currentIntent']['slots']
    source = intent_request['invocationSource']
    output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    valid_command = is_valid_command(command)

    if source == 'DialogCodeHook':
        if not location:
            return elicit_slot(
                    output_session_attributes,
                    intent_request['currentIntent']['name'],
                    intent_request['currentIntent']['slots'],
                    'LocationTypevalue',
                    {'contentType': 'PlainText', 'content': 'What location would you like to find?'},
                    build_response_card(
                        'Specify location', 'What location would you like to find?',
                        None
                    )
                )
                
        if is_valid_command != False:
            slots['LocationTypevalue'] = valid_command
            return delegate(output_session_attributes, slots)
            
        else:
            return elicit_slot(
                    output_session_attributes,
                    intent_request['currentIntent']['name'],
                    intent_request['currentIntent']['slots'],
                    'LocationTypevalue',
                    {'contentType': 'PlainText', 'content': 'I could not find that location. Are you looking for another location?'},
                    build_response_card(
                        'Specify location', 'I could not find that location. Are you looking for another location?',
                        None
                    )
                )
    
    return close(
                output_session_attributes,
                'Fulfilled',
                {
                    'contentType': 'PlainText',
                    'content': 'I will find {}'.format(location)
                }
            )


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'SendCommand':
        return send_command(intent_request)
    raise Exception('Intent with name ' + intent_name + ' not supported')
    


""" --- Main handler --- """

def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
