import os
import re
import cv2
import pydicom
from shapely.geometry import Polygon

from service.dicom_parser import dictify


def is_intersecting(l1, l2):
    p1 = Polygon(l1)
    p2 = Polygon(l2)
    return p1.intersects(p2)


def get_annotation_data(path):
    instances = list()
    for root, directories, filenames in os.walk(path):
        for filename in filenames:
            if '.DS' not in filename:
                instances.append(os.path.join(root, filename))
    files = dict()
    for instance in instances:
        files[instance] = os.path.getsize(instance)
    files_sorted = sorted(files.items(), key=lambda item: item[1])
    annotation_file = files_sorted[0][0]
    image_file = files_sorted[1][0]

    ds = pydicom.dcmread(image_file)
    pixel_array_numpy = ds.pixel_array
    img_file = os.path.basename(image_file) + '.jpg'
    dir_path = os.path.dirname(__file__) + '/organized_data/'
    if os.path.exists(dir_path) is False:
        os.mkdir(dir_path)
    img_file_path = os.path.join(dir_path, img_file)
    cv2.imwrite(img_file_path, pixel_array_numpy)

    ds_0 = pydicom.filereader.dcmread(annotation_file)
    ds = dictify(ds_0)

    study_id = ds['StudyInstanceUID']
    patient_id = ds['PatientID']
    name_age = '' + ds['PatientName'].family_name
    name_age_split = name_age.split()
    name = name_age_split[0] + ' ' + name_age_split[1]
    age = name_age_split[2][:-3]
    age = re.sub("[^0-9]", "", age)
    sex = ds['PatientSex']
    study_description = ds['StudyDescription']
    study_date = ds['StudyDate']
    study_time = ds['StudyTime']

    pneumonia = 0
    covid = 0
    normal = 0

    graphic_annotation_sequence = ds['GraphicAnnotationSequence']

    text_rows = list()
    graphic_rows = list()

    for graphic_annotation in graphic_annotation_sequence:

        text_object_sequence = graphic_annotation['TextObjectSequence']
        graphic_object_sequence = graphic_annotation['GraphicObjectSequence']

        for text_object in text_object_sequence:
            bounding_box_annotation_units = text_object['BoundingBoxAnnotationUnits']
            unformatted_text_value = text_object['UnformattedTextValue']
            if 'pneumo' in unformatted_text_value:
                pneumonia += 1
            elif 'covid' in unformatted_text_value:
                covid +=1
            else:
                normal += 1
            bounding_box_top_left_hand_corner = text_object['BoundingBoxTopLeftHandCorner']
            bounding_box_bottom_right_hand_corner = text_object['BoundingBoxBottomRightHandCorner']
            anchor_point = text_object['AnchorPoint']
            anchor_point_visibility = text_object['AnchorPointVisibility']
            text_pattern_on_color_cie_lab_value = text_object['LineStyleSequence'][0][
                'PatternOnColorCIELabValue']

            text_row = list()

            text_row.append(bounding_box_annotation_units)
            text_row.append(unformatted_text_value)
            text_row.append(bounding_box_top_left_hand_corner)
            text_row.append(bounding_box_bottom_right_hand_corner)
            text_row.append(anchor_point)
            text_row.append(anchor_point_visibility)
            text_row.append(text_pattern_on_color_cie_lab_value)

            text_rows.append(text_row)

        for graphic_object in graphic_object_sequence:
            graphic_annotation_units = graphic_object['GraphicAnnotationUnits']
            graphic_type = graphic_object['GraphicType']
            graphic_data = graphic_object['GraphicData']
            graphic_filled = graphic_object['GraphicFilled']
            graphic_pattern_on_color_cie_lab_value = graphic_object['LineStyleSequence'][0][
                'PatternOnColorCIELabValue']

            graphic_row = list()

            graphic_row.append(graphic_annotation_units)
            graphic_row.append(graphic_type)
            graphic_row.append(graphic_data)
            graphic_row.append(graphic_filled)
            graphic_row.append(graphic_pattern_on_color_cie_lab_value)

            graphic_rows.append(graphic_row)

    rows = list()

    for text_r in text_rows:
        for graphic_r in graphic_rows:
            row = list()
            text_box_raw = text_r[2:4]
            top_left_corner = (text_box_raw[0][0], text_box_raw[0][1])
            bottom_right_corner = (text_box_raw[1][0], text_box_raw[1][1])
            top_right_corner = (text_box_raw[0][0], text_box_raw[1][1])
            bottom_left_corner = (text_box_raw[1][0], text_box_raw[0][1])
            graphic_poly_raw = graphic_r[2]
            graphic_poly = list()
            idx = 0
            while idx < len(graphic_poly_raw):
                graphic_poly.append((graphic_poly_raw[idx], graphic_poly_raw[idx + 1]))
                idx += 2
            if len(graphic_poly) < 3:
                continue
            p1 = Polygon([bottom_left_corner, top_left_corner, top_right_corner, bottom_right_corner])
            print(graphic_poly)
            p2 = Polygon(graphic_poly)
            if p1.intersects(p2) is False:
                row.append(study_id)
                row.append(patient_id)
                row.append(name)
                row.append(age)
                row.append(sex)
                row.append(study_description)
                row.append(study_date)
                row.append(study_time)

                row.extend(text_r)
                row.extend(graphic_r)

                rows.append(row)
                break

    #df.to_csv('organized_data/annotation.csv')
    max_v = max([pneumonia, covid, normal])
    if max_v == pneumonia:
        lbl = 'pneumonia'
    elif max_v == covid:
        lbl = 'covid'
    else:
        lbl = 'normal'
    return rows, img_file_path, lbl
