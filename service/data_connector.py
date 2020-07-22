import os
import io
import json
import time
import zipfile
import requests
import pandas

from service.db import MongoDB
from service.annotation import get_annotation_data
from service.feature_extractor import FeatureExtractor

DB_FIND_LIMIT = 100
MONGO_DB_URI = 'mongodb://localhost:27017/'
MONGO_DB_USERNAME = ''
MONGO_DB_PASSWORD = ''
MONGO_XRAY_COLLECTION = 'xray'
MONGO_HOPS_DB = 'hops'

DICOM_SERVER_IP = '202.131.107.187'
DICOM_SERVER_PORT = '5007'
DICOM_SERVER_STUDY_PORT = '5006'
DICOM_THIRD_PARTY_LOGIN_ENDPOINT = 'hmis-web/dicomAIEngine/thirdPartyLogin'
DICOM_GET_DICOM_INSTANCES_ENDPOINT = 'hmis-web/dicomAIEngine/patientDicomDetailsSearch'
DICOM_GET_DICOM_STUDY_INSTANCES_ENDPOINT = 'dcm4chee-arc/aets/DCM4CHEE/rs/studies'
DICOM_SERVER_USERID_PARAM = 'userId'
DICOM_SERVER_PASSWD_PARAM = 'password'


class DataConnector:

    def __init__(self, un, pw):
        self.__un = un
        self.__pw = pw
        self.__login_url = 'http://' + DICOM_SERVER_IP + ':' + DICOM_SERVER_PORT + '/' + \
                           DICOM_THIRD_PARTY_LOGIN_ENDPOINT
        self.__get_instances_url = 'http://' + DICOM_SERVER_IP + ':' + DICOM_SERVER_PORT + '/' + \
                                   DICOM_GET_DICOM_INSTANCES_ENDPOINT
        self.__get_study_instances_url = 'http://' + DICOM_SERVER_IP + ':' + DICOM_SERVER_STUDY_PORT + '/' + \
                                         DICOM_GET_DICOM_STUDY_INSTANCES_ENDPOINT
        self.__token_id = ''

    def __login(self):
        raw_data = '{"' + DICOM_SERVER_USERID_PARAM + '":"admin","' + DICOM_SERVER_PASSWD_PARAM + '":"Hops@123"}'
        x = requests.post(self.__login_url,
                          data=raw_data,
                          headers={'Content-Type': 'application/json'})
        resp = json.loads(x.text)
        self.__token_id = resp['data']['userDetail']['token_id']

    def __get_dicom_instances_ids_by_date(self, from_date, to_date):
        raw_data = '{"from":"' + str(from_date) + '","to":"' + str(to_date) + '"}'
        x = requests.post(self.__get_instances_url,
                          data=raw_data,
                          headers={'Content-Type': 'application/json', 'Authorization': str(self.__token_id)})
        resp = json.loads(x.text)
        patients = resp['data']
        return patients

    def __get_study_instance(self, study_instance_id):
        download_dir = 'studies/' + str(study_instance_id) + '/'
        if os.path.exists(download_dir):
            return download_dir
        else:
            url = self.__get_study_instances_url + '/' + study_instance_id + '?accept=application/zip'
            resp = requests.get(url,
                             headers={'Content-Type': 'application/zip', 'Authorization': str(self.__token_id)})
            if resp.status_code == 200:
                os.makedirs(download_dir)
                zip_handle = zipfile.ZipFile(io.BytesIO(resp.content), "r")
                zip_handle.extractall(path=download_dir)
                zip_handle.close()
                return download_dir
            else:
                return ''

    @staticmethod
    def __set_fast_data(img_file_path, lbl):
        payload = list()
        db_handle = MongoDB()
        feature_vector = FeatureExtractor().get_features(img_file_path)
        feature_map = dict()
        key_p = os.path.splitext(os.path.basename(img_file_path))
        key = key_p[0] + '_' + key_p[1][1:] + '_' + str(int(time.time() * 1000.0))
        key = key.replace('.', '_')
        feature_map['file'] = key
        feature_map['label'] = lbl
        feature_map['feature'] = feature_vector
        payload.append(feature_map)
        try:
            db_handle.to_db(payload=payload, key=None, db=MONGO_HOPS_DB, collection=MONGO_XRAY_COLLECTION)
            payload.clear()
            db_handle.close()
        except Exception as e:
            db_handle.close()
            print(img_file_path)
            print("Ignoring Exception : " + str(e))

    def get_data(self, from_date, to_date, index):
        self.__login()
        patients = self.__get_dicom_instances_ids_by_date(from_date, to_date)
        df = pandas.DataFrame(columns=['StudyInstanceUID', 'PatientID', 'PatientName', 'PatientAge', 'PatientSex',
                                       'StudyDescription', 'StudyDate', 'StudyTime', 'BoundingBoxAnnotationUnits',
                                       'UnformattedTextValue', 'BoundingBoxTopLeftHandCorner',
                                       'BoundingBoxBottomRightHandCorner', 'AnchorPoint', 'AnchorPointVisibility',
                                       'TextLineColor', 'GraphicAnnotationUnits', 'GraphicType', 'GraphicData',
                                       'GraphicFilled', 'GraphicLineColor'])
        idx = 0
        for p in patients:
            studies = p['dicomFileDetails']
            for s in studies:
                path = self.__get_study_instance(s['studyInstanceUID'])
                if path == '':
                    continue
                rows, img_file_path, lbl = get_annotation_data(path)
                DataConnector.__set_fast_data(img_file_path, lbl)
                for row in rows:
                    df.loc[idx] = row
                    idx += 1
        if df.shape[0] > 0:
            csv_dir = os.path.dirname(__file__) + '/data/'
            if os.path.exists(csv_dir) is False:
                os.mkdir(csv_dir)
            csv_path = csv_dir + 'annotated_' + str(index) + '.csv'
            df.to_csv(csv_path)
        return df
