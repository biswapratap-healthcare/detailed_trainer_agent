from tensorflow.keras import Model
from tensorflow.keras.applications import VGG16
from tensorflow.keras.preprocessing.image import load_img
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.applications.vgg16 import preprocess_input


class FeatureExtractor:

    def __init__(self):
        self.__model = VGG16(include_top=False, weights='./vgg16_notop.h5')
        #self.__model.layers.pop()
        self.__model = Model(inputs=self.__model.inputs, outputs=self.__model.layers[-1].output)

    def get_features(self, img):
        image = load_img(img, target_size=(224, 224))
        image = img_to_array(image)
        image = image.reshape((1, image.shape[0], image.shape[1], image.shape[2]))
        image = preprocess_input(image)
        features = self.__model.predict(image)
        features = features.flatten().tolist()
        return features
