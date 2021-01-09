# 12V Lead Acid Battery Charger

from eez import scpi, getI, getU, dlogTraceData
from utime import sleep

# default values
cell_count = 6
cell_charge_voltage = 2.3
charge_voltage = cell_count * cell_charge_voltage
charge_current = 0.1
datalog_filename = "chargeLog"

channel = 1

def input_cell_count():
    global cell_count
    global charge_voltage
    global cell_charge_voltage
    value = scpi('DISP:INPut? "",INT, 0, 10, 6')
    if value != None:
        cell_count = int(value)
        charge_voltage = cell_count * cell_charge_voltage
        scpi('DISP:DIALog:DATA "cell_count",INT,' + str(cell_count))
        scpi('DISP:DIALog:DATA "charge_voltage",FLOAT,VOLT,' + str(charge_voltage))

def input_cell_voltage():
    global cell_count
    global cell_charge_voltage
    global charge_voltage
    value = scpi('DISP:INPut? "",NUMBER,VOLT, 0.0, 5.0, 2.3')
    if value != None:
        cell_charge_voltage = float(value)
        charge_voltage = cell_count * cell_charge_voltage
        scpi('DISP:DIALog:DATA "cell_charge_voltage",FLOAT,VOLT,' + str(cell_charge_voltage))
        scpi('DISP:DIALog:DATA "charge_voltage",FLOAT,VOLT,' + str(charge_voltage))

def input_charge_current():
    global charge_current
    value = scpi('DISP:INPut? "",NUMBER,AMPER, 0.0, 5.0, 1.0')
    if value != None:
        charge_current = float(value)
        scpi('DISP:DIALog:DATA "charge_current",FLOAT,AMPER,' + str(charge_current))

def input_filename():
    global datalog_filename
    value = scpi('DISP:INPut? "", TEXT, 2, 20, "chargeLog"')
    if value != None:
        datalog_filename = value
        scpi('DISP:DIAL:DATA "datalog_filename",STR, ' + datalog_filename)

def set_charge_param():
    scpi("INST ch1")
    scpi("VOLT " + str(charge_voltage))
    scpi("CURR " + str(charge_current))
    scpi("OUTP 1")

def startDatalogging():
    global charge_voltage, charge_current, datalog_filename
    scpi('SENS:DLOG:TRAC:X:UNIT SECOND')
    scpi('SENS:DLOG:TRAC:X:STEP 1')
    scpi("SENS:DLOG:TRAC:X:RANG:MAX 10")
    scpi('SENS:DLOG:TRAC:X:LABel "Time"')

    scpi('SENS:DLOG:TRAC:Y1:LABel "V"')
    scpi('SENS:DLOG:TRAC:Y1:UNIT VOLT')
    scpi('SENS:DLOG:TRAC:Y1:RANG:MIN 0')
    scpi('SENS:DLOG:TRAC:Y1:RANG:MAX ' + str(charge_voltage*1.1))

    scpi('SENS:DLOG:TRAC:Y2:LABel "I"')
    scpi('SENS:DLOG:TRAC:Y2:UNIT AMPER')
    scpi('SENS:DLOG:TRAC:Y2:RANG:MIN 0')
    scpi('SENS:DLOG:TRAC:Y2:RANG:MAX ' + str(charge_current*1.1))

    scpi('SENS:DLOG:TRAC:X:SCAL LIN')
    scpi('SENS:DLOG:TRAC:Y:SCAL LIN')

    scpi('SENS:DLOG:TRAC:Y3:LABel "Cumulative Capacity (Ahr)"')
    scpi('SENS:DLOG:TRAC:Y3:UNIT AMPER')
    scpi('SENS:DLOG:TRAC:Y3:RANG:MIN 0')
    scpi('SENS:DLOG:TRAC:Y3:RANG:MAX 10')

    filename = '/Recordings/' + datalog_filename + '.dlog'
    scpi('INIT:DLOG:TRACE "' + filename + '"')

def charge():
    try:
        set_charge_param()
        startDatalogging()

        uMon = getU(channel)
        iMon = getI(channel)

        total_amp_seconds = 0
        total_amp_hour = 0

        scpi('DISP:DIAL:DATA "Vmeas", FLOAT, VOLT, ' + str(uMon))
        scpi('DISP:DIAL:DATA "Imeas", FLOAT, AMPER, ' + str(iMon))
        scpi('DISP:DIAL:DATA "elapsed_amp_hour", FLOAT, AMPER, ' + str(total_amp_hour))

        action = ""

        while True:
            if action == "stop":
               break

            uMon = getU(channel)
            iMon = getI(channel)

            amp_seconds = iMon * 1 # 1 second time step
            total_amp_seconds += amp_seconds
            total_amp_hour = total_amp_seconds/3600

            dlogTraceData(uMon, iMon, total_amp_hour)
            #dlogTraceData(uMon, iMon)

            scpi('DISP:DIAL:DATA "Vmeas", FLOAT, VOLT, ' + str(uMon))
            scpi('DISP:DIAL:DATA "Imeas", FLOAT, AMPER, ' + str(iMon))
            scpi('DISP:DIAL:DATA "elapsed_amp_hour", FLOAT, AMPER, ' + str(total_amp_hour))

            action = scpi("DISP:DIALog:ACTIon? 1000ms")

    finally:
        scpi("OUTP 0")
        scpi('ABOR:DLOG')

def main():
    global cell_count
    global cell_charge_voltage
    global charge_voltage
    global charge_current
    global datalog_filename

    scpi("DISP:DIAL:OPEN \"/Scripts/leadacid_charger.res\"")

    # initialize display
    scpi('DISP:DIALog:DATA "cell_count",INT,' + str(cell_count))
    scpi('DISP:DIALog:DATA "cell_charge_voltage",FLOAT,VOLT,' + str(cell_charge_voltage))
    scpi('DISP:DIALog:DATA "charge_voltage",FLOAT,VOLT,' + str(charge_voltage))
    scpi('DISP:DIALog:DATA "charge_current",FLOAT,AMPER,' + str(charge_current))
    scpi('DISP:DIAL:DATA "datalog_filename",STR,' + str(datalog_filename))
    scpi('DISP:DIAL:DATA "disp_state", INT, 0')

    try:
        while True:
            action = scpi("DISP:DIALog:ACTIon?")
            if action == "input_cell_count":
                input_cell_count()
            if action == "input_cell_voltage":
                input_cell_voltage()
            if action == "input_charge_current":
                input_charge_current()
            if action == "input_filename":
                input_filename()
            if action == "view_setup":
                scpi('DISP:DIAL:DATA "disp_state", INT, 0')
            if action == "view_calculator":
                scpi('DISP:DIAL:DATA "disp_state", INT, 1')
            elif action == "start":
                scpi('DISP:DIAL:DATA "disp_state", INT, 2')
                charge()
                scpi('DISP:DIAL:DATA "disp_state", INT, 0')
            elif action == "close" or action == 0:
                break
        
    finally:
        scpi("DISP:DIAL:CLOS")

main()
