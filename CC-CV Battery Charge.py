# CC-CV battery charge profile with li-ion and lead acid presets

from eez import scpi, getI, getU, dlogTraceData
from utime import sleep

# default values
charge_voltage = 13.8
datalog_filename = 'chargeLog'
charge_current = 1.0
termination_current = 0.05
total_seconds = 0

channel = 1

def input_float(unit, minimum, maximum, default):
    value = scpi('DISP:INPut? "",NUMBER,'+unit+','+str(minimum)+','+str(maximum)+','+str(default))
    if value != None:
        return float(value)
    else:
        return float(default)

def input_int(minimum, maximum, default):
    value = scpi('DISP:INPut? "",INT,'+str(minimum)+','+str(maximum)+','+str(default))
    if value != None:
        return int(value)
    else:
        return int(default)

def input_text(minimum, maximum, default):
    value = scpi('DISP:INPut? "", TEXT,'+str(minimum)+','+str(maximum)+','+default)
    if value != None:
        return value
    else:
        return default

def set_charge_param():
    scpi('INST ch1')
    scpi('VOLT ' + str(charge_voltage))
    scpi('CURR ' + str(charge_current))
    scpi('OUTP 1')

def startDatalogging():
    global charge_voltage, charge_current, datalog_filename
    scpi('SENS:DLOG:TRAC:X:UNIT SECOND')
    scpi('SENS:DLOG:TRAC:X:STEP 1')
    scpi('SENS:DLOG:TRAC:X:RANG:MAX 10')
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

def display_charge_pane():
    scpi('DISP:DIAL:DATA "disp_state", INT, 2')
    scpi('DISP:DIALog:DATA "charge_voltage",FLOAT,VOLT,' + str(charge_voltage))
    scpi('DISP:DIALog:DATA "charge_current",FLOAT,AMPER,' + str(charge_current))
    scpi('DISP:DIALog:DATA "termination_current",FLOAT,AMPER,' + str(termination_current))
    scpi('DISP:DIAL:DATA "Vmeas", FLOAT, VOLT, 0')
    scpi('DISP:DIAL:DATA "Imeas", FLOAT, AMPER, 0')
    scpi('DISP:DIAL:DATA "elapsed_amp_hour", FLOAT, AMPER, 0')
    scpi('DISP:DIAL:DATA "total_seconds", FLOAT, SECOnd, 0')

def charge():
    global total_amp_hour, total_seconds
    display_charge_pane()

    try:
        set_charge_param()
        startDatalogging()

        uMon = getU(channel)
        iMon = getI(channel)

        total_amp_seconds = 0
        total_amp_hour = 0
        total_seconds = 0
        time_step = 1 #seconds

        action = ''

        while True:
            if action == 'stop':
               break
            elif action == 'view_datalog':
                scpi('DISP:WINDOW:DLOG')
            elif action == 'close' or action == 0:
                # TODO this won't actually exit...
                break;

            uMon = getU(channel)
            iMon = getI(channel)

            amp_seconds = iMon * time_step
            total_amp_seconds += amp_seconds
            total_amp_hour = total_amp_seconds/3600

            dlogTraceData(uMon, iMon, total_amp_hour)

            scpi('DISP:DIAL:DATA "Vmeas", FLOAT, VOLT, ' + str(uMon))
            scpi('DISP:DIAL:DATA "Imeas", FLOAT, AMPER, ' + str(iMon))
            scpi('DISP:DIAL:DATA "elapsed_amp_hour", FLOAT, AMPER, ' + str(total_amp_hour))
            scpi('DISP:DIAL:DATA "total_seconds", FLOAT, SECOnd, ' + str(total_seconds))

            if iMon < termination_current:
                break

            action = scpi('DISP:DIALog:ACTIon? ' + str(time_step))
            total_seconds += time_step

    finally:
        scpi('OUTP 0')
        scpi('ABOR:DLOG')

def display_setup_pane():
    scpi('DISP:DIAL:DATA "disp_state", INT, 0')
    scpi('DISP:DIALog:DATA "charge_voltage",FLOAT,VOLT,' + str(charge_voltage))
    scpi('DISP:DIALog:DATA "charge_current",FLOAT,AMPER,' + str(charge_current))
    scpi('DISP:DIALog:DATA "termination_current",FLOAT,AMPER,' + str(termination_current))
    scpi('DISP:DIAL:DATA "datalog_filename",STR,' + str(datalog_filename))

class calculator():
    cell_count
    cell_charge_voltage
    battery_capacity
    c_rate_charge
    c_rate_term
    calc_chemistry

    def __init__(self):
        self.battery_capacity = 1
        self.preset_lead_acid()

    def preset_lead_acid(self):
        self.calc_chemistry = 0 # lead acid in display
        self.cell_count = 6
        self.cell_charge_voltage = 2.3
        self.c_rate_charge = 0.3
        self.c_rate_term = 0.05

    def preset_li_ion(self):
        self.calc_chemistry = 1 # li-ion in  display
        self.cell_count = 1
        self.cell_charge_voltage = 4.2
        self.c_rate_charge = 0.5
        self.c_rate_term = 0.05

    def write_display(self):
        scpi('DISP:DIAL:DATA "disp_state", INT, 1')
        scpi('DISP:DIALog:DATA "cell_count",INT,' + str(self.cell_count))
        scpi('DISP:DIALog:DATA "cell_charge_voltage",FLOAT,VOLT,' + str(self.cell_charge_voltage))
        scpi('DISP:DIALog:DATA "battery_capacity",FLOAT,AMPER,' + str(self.battery_capacity))
        scpi('DISP:DIALog:DATA "charge_voltage",FLOAT,VOLT,' + str(charge_voltage))
        scpi('DISP:DIALog:DATA "charge_current",FLOAT,AMPER,' + str(charge_current))
        scpi('DISP:DIALog:DATA "termination_current",FLOAT,AMPER,' + str(termination_current))
        scpi('DISP:DIALog:DATA "c_rate_charge",FLOAT,UNKN,' + str(self.c_rate_charge))
        scpi('DISP:DIALog:DATA "c_rate_term",FLOAT,UNKN,' + str(self.c_rate_term))
        scpi('DISP:DIALog:DATA "calc_chemistry",INT,' + str(self.calc_chemistry))

    def calculate(self):
        global charge_voltage, charge_current, termination_current
        charge_voltage = self.cell_count * self.cell_charge_voltage
        charge_current = self.battery_capacity * self.c_rate_charge
        termination_current = self.battery_capacity * self.c_rate_term

    def loop(self):
        while True:
            self.calculate()
            self.write_display()

            action = scpi('DISP:DIALog:ACTIon?')
            if action == 'input_cell_count':
                self.cell_count = input_int(0, 10, self.cell_count)
                self.calculate()
            elif action == 'input_cell_voltage':
                self.cell_charge_voltage = input_float('VOLT', 0, 10, self.cell_charge_voltage)
                self.calculate()
            elif action == 'input_battery_capacity':
                self.battery_capacity = input_float('AMPER', 0, 50, self.battery_capacity)
                self.calculate()
            elif action == 'input_c_rate_charge':
                self.c_rate_charge = input_float('UNKN', 0, 50, self.c_rate_charge)
                self.calculate()
            elif action == 'input_c_rate_term':
                self.c_rate_term = input_float('UNKN', 0, 50, self.c_rate_term)
                self.calculate()
            elif action == 'select_next_chemistry':
                self.calc_chemistry += 1
                if self.calc_chemistry > 1:
                    self.calc_chemistry = 0

                if self.calc_chemistry == 0: # lead acid
                    self.preset_lead_acid()
                elif self.calc_chemistry == 1: # li-ion
                    self.preset_li_ion()

                self.calculate()
            elif action == 'view_setup':
                break
            elif action == 'close' or action == 0:
                # TODO this wont actually exit...
                break

def display_done_pane():
    scpi('DISP:DIAL:DATA "disp_state", INT, 3')
    scpi('DISP:DIALog:DATA "charge_voltage",FLOAT,VOLT,' + str(charge_voltage))
    scpi('DISP:DIALog:DATA "charge_current",FLOAT,AMPER,' + str(charge_current))
    scpi('DISP:DIAL:DATA "elapsed_amp_hour", FLOAT, AMPER, ' + str(total_amp_hour))
    scpi('DISP:DIALog:DATA "termination_current",FLOAT,AMPER,' + str(termination_current))
    scpi('DISP:DIAL:DATA "total_seconds", FLOAT, SECOnd, ' + str(total_seconds))

def done_loop():
    while True:
        display_done_pane()

        action = scpi('DISP:DIALog:ACTIon?')
        if action == 'start':
            break
        elif action == 'view_datalog':
            scpi('DISP:WINDOW:DLOG')
        elif action == 'close' or action == 0:
            # TODO this wont actually exit...
            break

def main():
    global charge_voltage
    global charge_current
    global termination_current
    global datalog_filename

    calc = calculator()

    scpi('DISP:DIAL:OPEN "/Scripts/CC-CV Battery Charge.res"')

    try:
        while True:
            display_setup_pane()
            action = scpi('DISP:DIALog:ACTIon?')
            if action == 'input_charge_current':
                charge_current = input_float('AMPER', 0, 5, charge_current)
            elif action == 'input_charge_voltage':
                charge_voltage = input_float('VOLT', 0, 40, charge_voltage)
            elif action == 'input_termination_current':
                termination_current = input_float('AMPER', 0, 5, charge_current)
            elif action == 'input_filename':
                datalog_filename = input_text(2, 30, datalog_filename)
            elif action == 'view_calculator':
                calc.loop()
            elif action == 'start':
                charge()
                done_loop()
            elif action == 'close' or action == 0:
                break
        
    finally:
        scpi('DISP:DIAL:CLOS')

main()
