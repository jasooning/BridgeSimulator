import json

list = [[50.0, 0.64, 80.0, 1.27], [10.63, 33.52, 1.27, 64.49], [89.37, 33.52, 1.27, 64.49], None, None, None, None]

data = []
for i in range(len(list)):
    if list[i] == None:
        continue
    dic = {
        "type": "rectangle",
        "name": "Rectangle",
        "pos": [
        0.0,
        0.0
        ],
        "rotation": 0.0,
        "w": 0,
        "h": 0
    }
    dic['pos'][0] = round(list[i][0] - list[i][2] / 2, 2)
    dic['pos'][1] = round(list[i][1] - list[i][3] / 2, 2)
    dic['w'] = round(list[i][2], 2)
    dic['h'] = round(list[i][3], 2)
    data.append(dic)

    with open("try.json", 'w') as f:
        json.dump(data, f, indent=2)