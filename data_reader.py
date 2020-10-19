import pandas as pd
import sys
import os
from os.path import join as join_path
import datetime
import numpy as np

# Root Directory of the Project
ROOT_DIR = os.path.abspath("./")

# Add ROOT_DIR to $PATH
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)


def isNaN(num):
    """
    It cheks if num is NaN
    :param num: number to check
    :return: True if NaN, False if not.
    """
    return num != num


def decimal_doy(do: int, ho: int, mi: int, se: int):
    """
    Converts DOY and time integers to floating point DOY.
    :param do: Day Of the Year
    :param ho: Hours
    :param mi: Minutes
    :param se: Seconds
    :return: Doy of the year with time in DOY decimals.
    """
    mi += se/60.
    ho += mi/60.
    return do + ho/24.


def rom2arab(roman: str):
    """
    Converts roman numbers to arabic numbers
    :param roman: String roman number
    :return: Integer arabic number
    """
    equiv = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    arabic = 0
    for i in range(len(roman)):
        try:
            sentence = equiv[roman[i]] < equiv[roman[i + 1]]
        except IndexError:
            sentence = False
        if sentence:
            arabic -= equiv[roman[i]]
        else:
            arabic += equiv[roman[i]]
    return arabic


def get_doy(doc_name: str, sheet_name: str):
    """
    Specific function that returns the Day Of the Year (DOY) by passing document
    and sheet names from the files with extension .xlsx from Rafael Hermida 2019.
    :param doc_name: (String) Name of the document
    :param sheet_name: (String) Name of the sheet
    :return: (Integer) DOY
    """
    months = {
        "Enero": 1,
        "Febrero": 2,
        "Marzo": 3,
        "Abril": 4,
        "Mayo": 5,
        "Junio": 6,
        "Julio": 7,
        "Agosto": 8,
        "Septiembre": 9,
        "Octubre": 10,
        "Noviembre": 11,
        "Diciembre": 12
    }
    y, m = doc_name[-4:], doc_name[2:-5]  # strings
    year = int(y)
    month = months[m]  # integer
    d = sheet_name[-2:]  # string
    try:
        day = int(d)
    except ValueError:
        print(f"Low Warning: Sheet named '{sheet_name}' is not a day number.")
        return None
    try:
        doy = int(datetime.datetime(year, month, day).strftime('%j'))
    except ValueError:
        doy = int(datetime.datetime(year, month, day - 1).strftime('%j')) + 1
        month += 1
        day = 1
    # print(f"DOY {doy:03d} :: DATE {day:02d}-{month:02d}-{year:02d}")
    return doy


meteo_codes = {
    "Visibility": {
        90: "< 50 m",
        91: 50,
        92: 200,
        93: 500,
        94: 1000,
        95: 2000,
        96: 4000,
        97: 10000,
        98: 20000,
        99: "> 50000 m"
    },
    "Time": {
        0: "Despejado",
        3: "Nubosidad variable",
        5: "Calma",
        18: "Chuvascos de viento",
        41: "Niebla",
        58: "Llovizna",
        65: "Lluvia",
        72: "Nevada",
        81: "Chuvascos de lluvia",
        86: "Chuvascos de nieve",
        97: "Tormenta"
    }
}

# dfs = pd.read_excel("hesp_rafaelhermida_2019/2.Noviembre 2019.xlsx", sheet_name=None)

data_dir = join_path(ROOT_DIR, "hesp_rafaelhermida_2019")

raw_data = {}
for file in os.listdir(data_dir):
    if file.endswith(".xlsx") and not file.startswith("._"):
        file_path = join_path(data_dir, file)
        raw_data[f"{file[:-5]}"] = pd.read_excel(file_path, sheet_name=None, usecols="A:O")

# print(raw_data["2.Noviembre 2019"]["Dia 15"])

'''
try:
    x = 1 / 0
except Exception as e:
    print(f"Something was wrong: {e.__doc__}")
    print(f"{e}")  # Message
'''
print("doyhhmmss\tdoy.ddd\tPress.\tTemp.\tHum.")

final_data = np.zeros([0, 5])
for i in raw_data:
    for j in raw_data[i]:
        doy = get_doy(i, j)
        if doy is None:
            continue
        for k, p, t, h in zip(raw_data[i][j][" Horario U.T.C."],
                              raw_data[i][j]["Barómetro en mb."],
                              raw_data[i][j]["Temperatura bola Humeda"],
                              raw_data[i][j]["Humedad"]):
            # ==== Date and Time ==== #
            if isNaN(k):
                continue
            try:
                hour = int(k)
            except ValueError:
                try:
                    hour = rom2arab(k)
                except Exception as e:  # Except all the rest of the trash
                    print(f"{e.__doc__}")
                    continue
            minute, second = 0, 0
            doyhhmmss = int(f"{doy:03d}{hour:02d}{minute:02d}{second:02d}")
            doy_ddd = decimal_doy(doy, hour, minute, second)

            # === Date/time, Pressure, Temperature, Humidity ==== #
            # print(f"{doyhhmmss}\t{doy_ddd:.3f}\t{p}\t{t}\t{h}")
            try:
                pressure = float(p)
            except ValueError:
                pressure = float(p.replace(",", ".")[:-1])
            try:
                temperature = float(t.split("º")[0])
            except AttributeError:  # if t == NaN
                temperature = t
            humidity = float(h)
            row = np.hstack((doyhhmmss, doy_ddd, pressure, temperature, humidity))
            final_data = np.vstack((final_data, row))


np.savetxt(fname="doyhhmmss-doy_ddd-pressure-temperature-humidity.txt", X=final_data, fmt='%09d %03.5f %.2f %02.2f %.3f')

