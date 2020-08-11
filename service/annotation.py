import os
import re
import cv2
import pydicom
from shapely.geometry import Polygon

from service.dicom_parser import dictify


def is_overlap(text, poly):
    p1 = Polygon(text)
    p2 = Polygon(poly)
    return p1.intersects(p2)


def get_shortest_distance(text, poly):
    pass


def get_common_data(instance, ds_0):
    ds = dictify(ds_0)
    instance['series_instance_uid'] = ds['SeriesInstanceUID']
    instance['modality'] = ds['Modality']
    instance['patient_id'] = ds['PatientID']
    name_age = '' + ds['PatientName'].family_name
    name_age_split = name_age.split()
    name = name_age_split[0] + ' ' + name_age_split[1]
    instance['patient_name'] = name
    try:
        age = name_age_split[2][:-3]
        age = int(re.sub("[^0-9]", "", age))
    except Exception as e1:
        try:
            age = int(ds['PatientAge'][1:-1])
        except Exception as e2:
            age = 0
    instance['patient_age'] = age
    instance['patient_sex'] = ds['PatientSex']
    instance['study_description'] = ds['StudyDescription']
    instance['study_date'] = ds['StudyDate']
    instance['study_time'] = ds['StudyTime']
    try:
        instance['body_part_examined'] = ds['BodyPartExamined']
        if instance['modality'] == 'DX' or instance['modality'] == 'PR':
            instance['view_position'] = ds['ViewPosition']
    except Exception as e:
        print('Exception : ' + str(e))
    return instance


def get_annotation_data(ds_0):
    ds = dictify(ds_0)
    graphic_annotation_sequence = ds['GraphicAnnotationSequence']
    texts = list()
    graphics = list()
    for graphic_annotation in graphic_annotation_sequence:
        text_object_sequence = graphic_annotation['TextObjectSequence']
        graphic_object_sequence = graphic_annotation['GraphicObjectSequence']
        for text_object in text_object_sequence:
            text_dict = dict()
            text_dict['bounding_box_annotation_units'] = text_object['BoundingBoxAnnotationUnits']
            text_dict['unformatted_text_value'] = text_object['UnformattedTextValue']
            text_dict['bounding_box_top_left_hand_corner'] = text_object['BoundingBoxTopLeftHandCorner']
            text_dict['bounding_box_bottom_right_hand_corner'] = text_object['BoundingBoxBottomRightHandCorner']
            text_dict['anchor_point'] = text_object['AnchorPoint']
            text_dict['anchor_point_visibility'] = text_object['AnchorPointVisibility']
            text_dict['text_pattern_on_color_cie_lab_value'] = \
                text_object['LineStyleSequence'][0]['PatternOnColorCIELabValue']
            texts.append(text_dict)
        for graphic_object in graphic_object_sequence:
            graphic_dict = dict()
            graphic_dict['graphic_annotation_units'] = graphic_object['GraphicAnnotationUnits']
            graphic_dict['graphic_type'] = graphic_object['GraphicType']
            graphic_dict['graphic_data'] = graphic_object['GraphicData']
            graphic_dict['graphic_filled'] = graphic_object['GraphicFilled']
            graphic_dict['graphic_pattern_on_color_cie_lab_value'] = \
                graphic_object['LineStyleSequence'][0]['PatternOnColorCIELabValue']
            graphics.append(graphic_dict)
    return texts, graphics


def get_valid_annotation_data(instance, texts, graphics):
    instance['annotation'] = list()
    for idx_txt, text_r in enumerate(texts):
        for idx_grp, graphic_r in enumerate(graphics):
            text_r['associated_graphic_index'] = list()
            graphic_r['associated_text_index'] = list()
            bbox_top_left_corner = text_r['bounding_box_top_left_hand_corner']
            bbox_bottom_right_corner = text_r['bounding_box_bottom_right_hand_corner']
            top_left_corner = (bbox_top_left_corner[0], bbox_top_left_corner[1])
            bottom_right_corner = (bbox_bottom_right_corner[0], bbox_bottom_right_corner[1])
            top_right_corner = (bbox_top_left_corner[0], bbox_bottom_right_corner[1])
            bottom_left_corner = (bbox_bottom_right_corner[0], bbox_top_left_corner[1])
            graphic_text = [bottom_left_corner, top_left_corner, top_right_corner, bottom_right_corner]
            graphic_poly_raw = graphic_r['graphic_data']
            graphic_poly = list()
            idx = 0
            while idx < len(graphic_poly_raw):
                graphic_poly.append((graphic_poly_raw[idx], graphic_poly_raw[idx + 1]))
                idx += 2
            if len(graphic_poly) < 3:
                continue
            if is_overlap(text=graphic_text, poly=graphic_poly):
                d = (graphic_r['graphic_type'], graphic_r['graphic_data'], text_r['unformatted_text_value'])
                instance['annotation'].append(d)
    if len(instance['annotation']) > 0:
        return instance
    else:
        return None


def get_instance_data(path):
    study_data = dict()
    study_id = os.path.basename(os.path.normpath(path))
    study_data['study_id'] = study_id
    instances = list()
    for root, directories, filenames in os.walk(path):
        for filename in filenames:
            if '.DS' not in filename:
                fpath = os.path.join(root, filename)
                instance = dict()
                try:
                    ds_image = pydicom.dcmread(fpath)
                    pixel_array_numpy = ds_image.pixel_array
                    img_file = os.path.basename(filename) + '.jpg'
                    dir_path = os.path.dirname(__file__) + '/organized_data/' + str(study_id) + '/'
                    if os.path.exists(dir_path) is False:
                        os.mkdir(dir_path)
                    img_file_path = os.path.join(dir_path, img_file)
                    cv2.imwrite(img_file_path, pixel_array_numpy)
                    instance['is_a'] = 'image'
                    instance['image_path'] = img_file_path
                    instance = get_common_data(instance, ds_image)
                except Exception as e:
                    try:
                        ds_0 = pydicom.filereader.dcmread(fpath)
                        instance['is_a'] = 'annotation'
                        instance = get_common_data(instance, ds_0)
                        texts, graphics = get_annotation_data(ds_0)
                        instance = get_valid_annotation_data(instance, texts, graphics)
                    except Exception as e:
                        instance['is_a'] = 'unknown'
                if instance is not None:
                    instances.append(instance)
    study_data['instances'] = instances
    return study_data
