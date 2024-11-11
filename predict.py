import sys
from PIL import Image
from ultralytics import YOLO
import math

classes = {
    '0': 'pmos',
    '1': 'NMOS',
    '2': 'Voltage',
    '3': 'Current',
    '4': 'NPN',
    '5': 'PNP',
    '6': 'Diode',
    '7': 'Diso_amp',
    '8': 'Siso_amp',
    '9': 'dido_amp',
    '10': 'Cap',
    '11': 'port', # 'Gnd,port,vdd',
    '12': 'Ind',
    '13': 'Res',
    '14': 'cross-line-curved',
    '15': 'switch',
    '16': 'switch-3',
    '17': 'antenna',
}

model = YOLO("best.pt")
model = model.to('cpu')
def predict(image_path):
    img = Image.open(image_path)
    results = model.predict(source=img, conf=0.3, save=True, save_txt=True)
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