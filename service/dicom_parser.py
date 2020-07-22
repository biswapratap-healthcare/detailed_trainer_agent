def to_dictionary(ds):
    output = dict()
    for elem in ds:
        if elem.VR != 'SQ':
            output[elem.keyword] = elem.value
        else:
            output[elem.keyword] = [to_dictionary(item) for item in elem]
    return output


def dictify(ds):
    output = to_dictionary(ds)
    return output
