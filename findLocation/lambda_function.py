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

api_key = ''
#8FYmwxXYXU_kd11xclK0HQ
grid_name = ''
#WestAcersDemo
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

def is_location(location_name):
    # This function will eventually check firebase with a building name to get all of the locations in a building to reference.
    # Strip location and locations in list of symbols and make lowercase
    if (api_key == '' and grid_name == ''):
        return "Error Session Attributes are not set!"
    location_list = get_locations(grid_name)
    #print location_list
    results = process.extract(location_name, location_list, limit=2)
    print results
    score = 75
    final_string = ''
    for location in results:
        #if location[1] > 90:
        #    return location[0]
        tmp_str = location[0]
        tmp_location_name = str(location_name)
        tmp_compare_str = str(location[0])
        tmp_score_array = []
        tmp_score1 = fuzz.ratio(tmp_location_name.upper(), tmp_compare_str.upper())
        tmp_score2 = fuzz.partial_ratio(tmp_location_name.upper(), tmp_compare_str.upper())
        tmp_score3 = fuzz.token_sort_ratio(tmp_location_name.upper(), tmp_compare_str.upper())
        tmp_score4 = fuzz.token_set_ratio(tmp_location_name.upper(), tmp_compare_str.upper())
        tmp_score_array.append(tmp_score1)
        tmp_score_array.append(tmp_score2)
        tmp_score_array.append(tmp_score3)
        tmp_score_array.append(tmp_score4)
        tmp_score_array.sort()
        
        tmp_score = tmp_score_array[2] + tmp_score_array[3]
        
        tmp_score = (float(tmp_score) / 200) * 100
        print tmp_score
        if tmp_score > score:
            score = tmp_score
            final_string = tmp_str
    if final_string == '':
        return False
    else:
        return final_string 

    

def get_locations(building_name):
    # This function will query firebse for the locations of some building
    #location_list = ["Macy's","Helzberg Diamonds", "Maurices", "Shirt Shop in the Mall", "Lids", "Gymboree", "SHU by R&G", "GameStop", "JCPenney", "Orange Julius", "Merle Norman", "Things Remembered", "Justice", "Red Brick Boutique", "Regis Salon", "bareMinerals", "Bath & Body Works", "Herberger's", "Boot Barn", "francesca's", "Stride Rite", "Almost Famous", "Chili's", "Kay Jewelers", "Gap", "LOFT", "Finish Line", "Zumiez", "Chico's", "Tradehome Shoes", "Wimmer's Diamonds", "Best Buy Mobile", "Orange Julius", "Mrs. Fields", "Eyecare Associates, PC", "Pretzelmaker", "Journeys", "Foot Locker", "lululemon", "Creative Kitchen", "Talbots", "Johnny Rockets", "Subway", "Leeann Chin", "Joe's Cajun Cafe", "Recess West", "Qdoba Mexican Grill", "Dairy Queen", "Rising Bread Company", "Lee's Hallmark", "Verizon Wireless", "Cinamen Roll Co.", "Stabo Scandinavian Imports", "AT&T Wireless", "Legacy Toys", "Victoria's Secret", "Payless ShoeSource", "Nails Pro", "Lux Spa", "Roger Maris Museum", "Pets R' Inn", "Tip Top Tux", "Mall Office", "West Acres Pharmacy", "Essentia Health", "Spencer's", "Sports City", "Hot Topic", "The Children's Place", "White House|Black Market", "Lane Bryant", "General Nutrition Center", "Express", "Zales", "Buckle", "American Eagle Outfitters", "Apricot Lane Boutique", "Christopher & Banks", "Claire's", "Evereve", "Hollister Co.", "Eddie Bauer", "Forever 21", "Gap Kids", "Motherhood Maternity", "PINK", "MasterCuts", "Halberstadt's", "LensCrafters"]
    print api_key
    print grid_name
    result = firebase.get('/' + api_key + '/buildings/' + grid_name + '/floorGrids', None)
    parsed_result = json.loads(result)
    ct = 0
    location_list = []
    for floor in parsed_result:
        try:
            for location in floor['storeInfo']:
                location_list.append(location['name'])
        except:
            print 'No locations on floor: {}'.format(ct)
    return location_list



""" --- Functions that control the bot's behavior --- """

def find_location(intent_request):
    location = intent_request['currentIntent']['slots']['LocationTypevalue']
    print location
    slots = intent_request['currentIntent']['slots']
    source = intent_request['invocationSource']
    output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    global api_key
    if intent_request['sessionAttributes']:
        api_key = intent_request['sessionAttributes']['apiKey']
    global grid_name
    if intent_request['sessionAttributes']:
        grid_name = intent_request['sessionAttributes']['gridName']
    updated_location = is_location(location)

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
        if updated_location != False:
            slots['LocationTypevalue'] = updated_location
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
    if intent_name == 'FindLocation':
        return find_location(intent_request)
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

