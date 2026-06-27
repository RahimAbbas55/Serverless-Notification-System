# Define the channels from which the user can receive notifications and the 
# levels of notifications that can be sent to the user.
VALID_CHANNELS = ['email' , 'slack']
# Define the levels of notifications that can be sent to the user.
VALID_LEVELS = ['info' , 'warning' , 'critical' , 'error']

'''
    This function takes in a payload which is a dictionary and validates it against 
    the defined channels and levels. If the errors list is empty, it means the payload is valid. 
    If there are errors, they will be returned in the list.
'''
def validate_webhook_payload(payload: dict) -> list[str]:
    errors = []
    # Get channel input
    channel = payload.get('channel')
    if not channel:
        errors.append('Channel is required.')
    else:
        # Someone might send only 1 channel or multiple channels, so we need to handle both cases.
        channels = [channel] if isinstance(channel, str) else channel
        invalid = [c for c in channels if c not in VALID_CHANNELS]
        if invalid:
            errors.append(f"Invalid channel(s): {invalid}. Valid channels are: {list(VALID_CHANNELS)}.")
        # Validate Email Levels
        if "email" in channels:
            # Valiate the contents of the email
            if not payload.get('recipient'):
                errors.append("'Recipient' is required!")
            if not payload.get('subject'):
                errors.append("'Subject' is required!")
        '''
            In both of our channels (email and slack),
            the message is constant. The user always needs to send a message, 
            so we will validate that the message is present in the payload.
        '''
    if not payload.get('message'):
        errors.append("'Message' is required!")
    
    # Validate the level of notification. User can send a message without a level, but if they do send a level, it must be valid.
    level = payload.get('level')
    if level and level not in VALID_LEVELS:
        errors.append(f"'level' must be one of {list(VALID_LEVELS)}")
    # Return all the errors found in the payload
    return errors