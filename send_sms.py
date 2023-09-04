import json
import threading
import time
from copy import deepcopy
from os.path import isfile
from shutil import copyfile
from typing import Type, Union

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client


class TelephonesStorage:
    """Class for monitoring and updating telephone states."""

    telephones = {}
    path_to_json = None

    @staticmethod
    def set_telephones(path_to_json: str) -> None:
        """
        Set the path to the JSON file containing telephone states and load the data into the telephones dictionary.

        Args:
            path_to_json (str): The path to the JSON file containing telephone states.
        """

        TelephonesStorage.path_to_json = path_to_json

        with open(path_to_json, 'r', encoding='utf-8') as f:
            TelephonesStorage.telephones = json.loads(f.read())
        
        if isfile(path_to_json + '.bak') is False:
            copyfile(path_to_json, path_to_json + '.bak')

    @classmethod
    def watch_telephones_state(cls) -> None:
        """
        Start watching and updating telephone states in a separate thread.
        """

        if not hasattr(cls, 'thread') or not cls.thread.is_alive():
            cls.thread = threading.Thread(target=cls._watch_thread)
            cls.thread.start()

    @classmethod
    def _watch_thread(cls) -> None:
        """
        Internal thread function for monitoring and updating telephone states.

        This method runs in a separate thread and periodically checks for changes in telephone states
        and saves them to the JSON file if changes occur.
        """

        previous_state = deepcopy(cls.telephones)

        while True:
            if previous_state != cls.telephones:
                previous_state = deepcopy(cls.telephones)
                cls._save_state_to_file()

            time.sleep(0.25)

    @classmethod
    def _save_state_to_file(cls) -> None:
        """
        Save telephone states to a JSON file.

        This method saves the current state of telephone states in the `telephones` dictionary to the
        JSON file specified by `path_to_json`.
        """

        with open(TelephonesStorage.path_to_json, 'w', encoding='utf-8') as f:
            json.dump(cls.telephones, f, indent=4)

class SMSMarketing:
    """A class for managing SMS marketing campaigns using Twilio."""

    class _SMS:
        """A private inner class for representing individual SMS messages."""
        
        def __init__(self, body: str, from_: str, to: str, nofN: tuple = None) -> None:
            """
            Initialize an SMS object.
            
            Args:
                body (str): The SMS message content.
                from_ (str): The sender's mobile number or alphanumeric sender ID.
                to (str): The recipient's mobile number.
                nofN (tuple, optional): A tuple representing the position and total number of SMS messages in a campaign.

            """
            
            self.body = body
            self.from_ = from_
            self.to = to
            self.nofN = nofN

        def __repr__(self) -> str:
            """
            Get a string representation of the SMS object.
            
            Returns:
                str: A string containing SMS details (From, To, Body).
            """

            return f'From: {self.from_}, To: {self.to}, Body: {self.body}'

    class _Campaign:
        """A private inner class for managing SMS marketing campaigns."""

        def __init__(self, campaign_name: str, storage: Type['TelephonesStorage'], manager: Type['SMSMarketing'], sms_body: str) -> None:
            """
            Initialize a campaign.
            
            Args:
                campaign_name (str): The name of the campaign.
                storage (Type['TelephonesStorage']): The storage object for managing telephone numbers.
                manager (Type['SMSMarketing']): The SMSMarketing manager responsible for the campaign.
                sms_body (str): The content of the SMS message for the campaign.
            """

            self.campaign_name = campaign_name
            self.storage = storage
            self.manager = manager
            self.sms = SMSMarketing._SMS(body=sms_body, from_=self.manager.mobile_number, to=None)
            self.storage.watch_telephones_state()

        def run_campaign(self) -> None:
            """
            Run the SMS marketing campaign, sending messages to eligible recipients.
            """

            numbers_to_send = {mobile_number: state for mobile_number, state in self.storage.telephones.items() if state is False}
            length_of_numbers = len(numbers_to_send)

            for n, mobile_number in enumerate(numbers_to_send):
                self.sms.to = mobile_number
                self.sms.nofN = (n + 1, length_of_numbers)
                self._send_sms(self.sms)

        def _send_sms(self, sms: Type['SMSMarketing._SMS']) -> Union[str, None]:
            """
            Send an SMS message.

            Args:
                sms (Type['SMSMarketing._SMS']): The SMS message to send.

            Returns:
                Union[str, None]: The SID (Service Identifier) of the sent SMS or None if there was an error.
            """

            try:
                sent_sms = self.manager.client.messages.create(
                    body=sms.body,
                    from_=sms.from_,
                    to=sms.to
                )

                if sent_sms.sid is None:
                    raise Exception('Something went wrong. SMS sid not received')
                
                print(f'{sms.nofN[0]}/{sms.nofN[1]} Successfully sent SMS with data:\n{self.sms}\n')
                
                self.storage.telephones[sms.to] = True
            except TwilioRestException as e:
                print(f"{e}\nError raised during sending the SMS {sms.__dict__}")
                return None

            return sent_sms.sid

    def __init__(self, account_sid: str, auth_token: str) -> None:
        """
        Initialize the SMSMarketing manager.

        Args:
            account_sid (str): Twilio account SID.
            auth_token (str): Twilio authentication token.
        """

        self.account_sid = account_sid
        self.auth_token = auth_token
        self.client = self._initialize_twilio_client()
        self.mobile_number = None
        self.campaign = None

    def set_mobile_number(self, mobile_number: str = None, alphanumeric_sender_id: str = None) -> None:
        """
        Set the mobile number or alphanumeric sender ID to be used for sending SMS messages.

        Args:
            mobile_number (str, optional): The sender's mobile number.
            alphanumeric_sender_id (str, optional): The alphanumeric sender ID.

        Raises:
            Exception: If both mobile_number and alphanumeric_sender_id are provided or if neither is provided.
        """

        if mobile_number is None and alphanumeric_sender_id is None:
            raise Exception('You have to specify mobile_number or alphanumeric_sender_id arg')
        
        if mobile_number is not None and alphanumeric_sender_id is not None:
            raise Exception('You cannot use mobile_number and alphanumeric_sender_id args at the same time')
        
        self.mobile_number = mobile_number if mobile_number else alphanumeric_sender_id

    def create_campaign(self, campaign_name: str, storage: Type['TelephonesStorage'], sms_body: str) -> None:
        """
        Create an SMS marketing campaign.

        Args:
            campaign_name (str): The name of the campaign.
            storage (Type['TelephonesStorage']): The storage object for managing telephone numbers.
            sms_body (str): The content of the SMS message for the campaign.

        Raises:
            Exception: If the mobile_number has not been set using set_mobile_number.
        """

        if self.mobile_number is None:
            raise Exception('Before you create a campaign, you have to use the set_mobile_number function')
        
        self.campaign = SMSMarketing._Campaign(
            campaign_name=campaign_name, storage=storage, manager=self, sms_body=sms_body
        )

    def run_campaign(self):
        """
        Run the SMS marketing campaign.
        """

        self.campaign.run_campaign()

    def _initialize_twilio_client(self):
        """
        Initialize the Twilio client.

        Returns:
            Client: The initialized Twilio client.
        """

        return Client(self.account_sid, self.auth_token)

if __name__ == "__main__:
	internal = SMSMarketing(account_sid='XXXXXX', auth_token='XXXXX')
	internal.set_mobile_number(alphanumeric_sender_id='XXXXX')
	
	storage = TelephonesStorage.set_telephones(path_to_json='XXXX.json')
	
	internal.create_campaign(campaign_name='XXXX', storage=TelephonesStorage, sms_body='XXXX')
	
	internal.run_campaign()
