### This code was taken from https://github.com/Smartling/api-sdk-python/blob/master/example/SmartlingApiExample.py
###

import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)  # allow to import ../smartlingApiSdk/SmartlingFileApi

from smartlingApiSdk.SmartlingFileApi import SmartlingFileApiFactory
from smartlingApiSdk.SmartlingDirective import SmartlingDirective
from smartlingApiSdk.UploadData import UploadData
import settings


class SmartlingApi:
    MY_API_KEY = settings.SMARTLING_API_KEY
    MY_PROJECT_ID = settings.SMARTLING_PROJECT_ID

    def __init__(self, useSandbox, uploadData, locale, new_name):
        self.getCredentials()
        if useSandbox:
            self.fapi = SmartlingFileApiFactory().getSmartlingTranslationApi(False, self.MY_API_KEY, self.MY_PROJECT_ID)
        else:
            self.fapi = SmartlingFileApiFactory().getSmartlingTranslationApiProd(self.MY_API_KEY, self.MY_PROJECT_ID)
        self.uploadData = uploadData
        self.locale = locale
        self.new_name = new_name

    def getCredentials(self):
        """ get api key and project id from environment variables
            to set environment variables use command : export SL_API_KEY=******* ; export SL_PROJECT_ID=****** """
        self.MY_API_KEY = os.environ.get('SL_API_KEY', self.MY_API_KEY)
        self.MY_PROJECT_ID = os.environ.get('SL_PROJECT_ID', self.MY_PROJECT_ID)


def get_smartling_file(fname, locale='de-DE'):
    useSandbox = False
    example = SmartlingApi(useSandbox, None, locale, '')
    content = example.fapi.get(fname, locale)
    return content


def upload_smartling_file(filepath, filename, locale='de-DE', file_type='json'):
    uploadDataUtf16 = UploadData(filepath, filename, file_type)
    uploadDataUtf16.setApproveContent("true")
    uploadDataUtf16.setCallbackUrl(settings.SMARTLING_CALLBACK_URL)
    useSandbox = False
    example = SmartlingApi(useSandbox, uploadDataUtf16, locale, filename)
    example.fapi.upload(example.uploadData)

