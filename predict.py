import sys
from PIL import Image
from ultralytics import YOLO
import math

classes = {
    '0': 'pmos',
    '1': 'nmos',
    '2': 'voltage',
    '3': 'current',
    '4': 'npn',
    '5': 'pnp',
    '6': 'diode',
    '7': 'diff-amp',
    '8': 'single-input-single-end-amp',
    '9': 'dido-amp',
    '10': 'capacitor',
    '11': 'gnd',
    '12': 'inductor',
    '13': 'resistor',
    '14': 'port',
    '15': 'cross-line-curved',
    '16': 'vdd',
    '17': 'switch',
    '18': 'switch-3',
    '19': 'antenna',
    '20': 'cross'
}

model = YOLO("best.pt")
model = model.to('cpu')
def predict(image_path):
    img = Image.open(image_path)
    results = model.predict(source=img, conf=0.3, save=False, save_txt=False, verbose=False)
    resultsDict = []

    for cpn in range(len(results[0].boxes.xyxy)):
        fCoordinates = results[0].boxes.xyxy[cpn].numpy().tolist()
        iCoordinates = [math.floor(num) for num in fCoordinates]
        iClass = math.floor(results[0].boxes.cls[cpn].numpy().tolist())

        cpnDict = {
            'label': classes[str(iClass)],
            'points': [[iCoordinates[0], iCoordinates[1]], [iCoordinates[2], iCoordinates[3]]]
        }

        resultsDict.append(cpnDict)
        # print(iCoordinates, classes[str(iClass)])
        # print(results[0].boxes.xyxy[cpn].numpy().tolist(), results[0].boxes.cls[cpn].numpy().tolist())

    return resultsDict

if __name__ == '__main__':
    if len(sys.argv) > 1:
        try:
            predict(sys.argv[1])
        # except file does not exist
        except FileNotFoundError:
            print("Error opening file " + sys.argv[1])
        # except other errors
        except Exception as e:
            print("Error: " + str(e))
    else:
        print("Usage: python predict.py <image_path>")