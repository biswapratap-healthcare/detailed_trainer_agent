import os
import re
import cv2
import pydicom

from dicom_parser import dictify


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

    rows = list()

    pneumonia = 0
    covid = 0
    normal = 0

    graphic_annotation_sequence = ds['GraphicAnnotationSequence']
    for graphic_annotation in graphic_annotation_sequence:
        text_object_sequence = graphic_annotation['TextObjectSequence']
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
            row = list()
            row.append(study_id)
            row.append(patient_id)
            row.append(name)
            row.append(age)
            row.append(sex)
            row.append(study_description)
            row.append(study_date)
            row.append(study_time)
            row.append(bounding_box_annotation_units)
            row.append(unformatted_text_value)
            row.append(bounding_box_top_left_hand_corner)
            row.append(bounding_box_bottom_right_hand_corner)
            row.append(anchor_point)
            row.append(anchor_point_visibility)
            row.append(text_pattern_on_color_cie_lab_value)
            row.append('')
            row.append('')
            row.append('')
            row.append('')
            row.append('')
            rows.append(row)
        graphic_object_sequence = graphic_annotation['GraphicObjectSequence']
        for graphic_object in graphic_object_sequence:
            graphic_annotation_units = graphic_object['GraphicAnnotationUnits']
            graphic_type = graphic_object['GraphicType']
            graphic_data = graphic_object['GraphicData']
            graphic_filled = graphic_object['GraphicFilled']
            graphic_pattern_on_color_cie_lab_value = graphic_object['LineStyleSequence'][0][
                'PatternOnColorCIELabValue']
            row = list()
            row.append(study_id)
            row.append(patient_id)
            row.append(name)
            row.append(age)
            row.append(sex)
            row.append(study_description)
            row.append(study_date)
            row.append(study_time)
            row.append('')
            row.append('')
            row.append('')
            row.append('')
            row.append('')
            row.append('')
            row.append('')
            row.append(graphic_annotation_units)
            row.append(graphic_type)
            row.append(graphic_data)
            row.append(graphic_filled)
            row.append(graphic_pattern_on_color_cie_lab_value)
            rows.append(row)
    #df.to_csv('organized_data/annotation.csv')
    max_v = max([pneumonia, covid, normal])
    if max_v == pneumonia:
        lbl = 'pneumonia'
    elif max_v == covid:
        lbl = 'covid'
    else:
        lbl = 'normal'
    return rows, img_file_path, lbl
