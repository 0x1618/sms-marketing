# SMS Marketing with Twilio

This Python script allows you to manage SMS marketing campaigns using the Twilio API. It provides a convenient way to send SMS messages to a list of phone numbers while keeping track of the campaign's progress.

> :warning: **This code is used for the author's own purposes and may not be flexible to the user's needs :)**

## Prerequisites

Before using this script, make sure you have the following prerequisites:

- Twilio Account SID and Auth Token. You can obtain these by signing up for a Twilio account at [https://www.twilio.com/](https://www.twilio.com/).
- Python 3.x installed on your system.
- The `twilio` Python library. You can install it using `pip`:

```bash
pip install twilio
```

```python
from sms_marketing import TelephonesStorage, SMSMarketing

storage = TelephonesStorage()
storage.set_telephones(path_to_json='path/to/telephone_states.json')

sms_marketing = SMSMarketing(account_sid='YOUR_TWILIO_ACCOUNT_SID', auth_token='YOUR_TWILIO_AUTH_TOKEN')
sms_marketing.set_mobile_number(alphanumeric_sender_id='YOUR_SENDER_ID')
sms_marketing.create_campaign(campaign_name='YourCampaignName', storage=storage, sms_body='Your SMS message body')
sms_marketing.run_campaign()
```

## Example of telephone.states.json

```json
{
  "1234567890": false,
  "9876543210": true,
  "5555555555": false
}
```
