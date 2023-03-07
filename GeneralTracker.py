from audioop import add
import os
import sys
import smtplib
import ssl

from enum import Enum, auto
from email.mime.text import MIMEText
from importlib.resources import path
from tabnanny import check
from xmlrpc.client import boolean
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC


class CheckType(Enum):
    """
        This is a kind of check we're doing ENUM
    """
    LESS_THAN = auto()
    GREATER_THAN = auto()
    EQUAL = auto()
    NOT_EQUAL = auto()
    

class Notification_Type(Enum):
    """
        This is a notification type that is currently accepted
    """
    EMAIL = 'email'
    SMS = 'sms'
 

class Notification(object):
    def __init__(self, notification_type: Notification_Type, address: str, carrier: str=None):
        if carrier is None:
            self.notification_type = notification_type
            self.address = address
            self.carrier = carrier
        else:
            self.notification_type = notification_type
            self.address = address
    
    def notify(self, url: str, check: CheckType, check_aginst: any):
        # Read env variables to make sure that smtp server, from address, and sender email and password is set
        sender_email = os.getenv("EmailAddress")
        password = os.getenv("Password")
        smtp_server = os.getenv("SMTPServer")

        if sender_email is None or password is None or smtp_server is None:
            print("Your system variables is not set properly. Please refer to the documentation to set up smtp server properly")
            return

        str_check = None
        if check==1:
            str_check = "less than"
        elif check==2:
            str_check = "greater than"
        elif check==3:
            str_check = "equal to"
        elif check==4:
            str_check = "not equal to"
        msg = MIMEText("{0}\nData on the website you're tracking Changed. Value is {1} {2}".format(url, str_check, check_aginst))

        # Set the message sender and receiver
        msg["Subject"] = "Tracker Notification"
        if (self.notification_type=="sms"):
            msg['To'] = self.get_smsaddress(self.address)
        elif(self.notification_type=="email"):
            msg["To"] = self.address
        else:
            print("Only sms and email notification type is supported. Please make sure that your notification type is set correctly")
            sys.exit(1)

        # Send the message
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(
                [sender_email], [self.address], msg.as_string()
            )

    def get_smsaddress(self, address: str, carrier:str) -> str:
        # clean up the carrier and address
        address = address.replace('-','').replace(' ','').replace('.','')
        carrier = carrier.lower

        if 'at&t' in carrier:
            return '{0}@txt.att.net'.format(address)
        elif 'tmobile' in carrier or 't-mobile' in carrier:
            return '{0}@tmomail.net'.format(address)
        elif 'verizon' in carrier:
            return '{0}@vtext.com'.format(address)
        elif 'sprint' in carrier:
            return '{0}@messaging.sprintpcs.com'.format(address)
        elif 'virgin' in carrier:
            return '{0}@vmobl.com'.format(address)
        elif 'tracfone' in carrier:
            return '{0}@mmst5.tracfone.com'.format(address)
        else:
            print("Your carrier isn't supported yet.")
            sys.exit(1)

    @staticmethod
    def from_json(json_dct):
        try:
            if json_dct["notification_type"] == 'email':
                return Notification(json_dct['notification_type'], json_dct['address'])
            else:
                return Notification(json_dct['notification_type'], json_dct['address'], json_dct["carrier"])
        except KeyError as e:
            print("Make sure that you have proper json with appropriate keys. For Example: Carrier is set if you have sms as a notification")
            sys.exit()

class GeneralItem(object):
    """
        This is a general item which we can use to track
    """
    def __init__(self, url: str, check: CheckType, check_against: any, htmlId: str, check_period: int, notification: Notification_Type):
        self.url = url
        self.check = check
        self.check_against = check_against
        self.htmlId = htmlId
        self.check_period = check_period
        self.notification = notification


    # Custom Deserilize method
    @staticmethod
    def from_json(json_dct):
        try:
            return GeneralItem(json_dct["url"], json_dct["check"], json_dct["check_against"], json_dct["htmlId"], json_dct["check_period"], json_dct["notify"])
        except KeyError:
            return Notification.from_json(json_dct)

    def track(self) -> boolean:
        # Get the attribute
        value = self.__getattribute()

        # We if fail to get the proper value
        if value is False:
            return False

        # Check to see if the returned attribute requires notification
        if self.check == 1:
            return value < self.check_against
        elif self.check == 2:
            return value > self.check_against
        elif self.check == 3:
            return value == self.check_against
        elif self.check == 4:
            return value != self.check_against
        else:
            return False



    def __getattribute(self) -> any:
        # Setup selenium
        options = Options()
        options.headless = True
        dr = webdriver.Chrome("./chromedriver", options=options)

        # request the webpage
        dr.get(self.url)
        dr.implicitly_wait(5)

        # create beautiful soup object to parse the html page
        soup = bs(dr.page_source, 'html.parser')
        dr.quit()

        # return the attribute
        # Since Amazon wants to do things differntly, had to do this manually
        if "amazon.com" in self.url:
            attr = soup.find('span', {'class': self.htmlId})
        elif "ebay.com" in self.url:
            attr = soup.find('span', {'id': self.htmlId})
        elif "coinmarketcap.com" in self.url:
            attr = soup.find('div', {'class': self.htmlId})
        else:
            attr = soup.find(id=self.htmlId)

        if attr is None:
            print("There was a error with trying to find the htmlId with {0}. Please Try Again!! ".format(
                self.url
            ))
            dr.quit()
            return False
        # Get the attributes text and convert it into into if we're comparing with <  or >
        # Clean up the string
        attr_str = attr.get_text().replace('.', '').replace('$', '').replace('US', '').replace(',','').strip()

        # if comparing with < or >
        if self.check == 1 or self.check == 2:
            return int(attr_str)
        else:
            return attr_str


    def valid_check(self) -> bool:
        if self.check == 1 or self.check == 2:
            if type(self.check_against) is str:
                return False
            return True
        return True
            
