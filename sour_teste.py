#Definindo e calculandos as variáveis

#Escolha a tensão inicial, final e o passo
voltage_inicial = 0
voltage_final = 1
passo = 0.01

#Delays e estabilização:

#Delay entre a aplicação e a medida (padrão)!
delay_sm = 0.02

#Delay entre as aplicações (Trigger) (Define a velocidade de varredura)
delay_t = 0.05

#tempo estabilização(s) padrão!
estab = 1

#Cálculos dos parametros utilizados na medida

taxa_varredura = float(passo/delay_t)
#numero de pontos, pra contagem de trigger
num_pontos = float((voltage_final - voltage_inicial)/passo)
num_pontos2 = (num_pontos + 1)

#Definindo os parametros do gate
voltage_inicial_gate = 0
voltage_final_gate = 1
passo_gate = 0.1


import time
import os
import numpy as np
import pyvisa as visa
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm

com_keithley = 'GPIB0::15::INSTR'
com_agilent = 'GPIB0::10::INSTR'


class keithley:
    def keithley(com_keithley):
        import pyvisa as visa
        rm = visa.ResourceManager()
        sourcemeter = rm.open_resource(str(com_keithley))
        sourcemeter.timeout = 2500000
        return sourcemeter


class agilent:
    def agilent(com_agilent):
        import pyvisa as visa
        rm = visa.ResourceManager()
        gatesource = rm.open_resource(str(com_agilent))
        return gatesource


gate_potentials = np.arange(voltage_inicial_gate, voltage_final_gate, passo_gate)

gatesource = agilent.agilent(com_agilent)
gatesource.write('disp off')
gatesource.write('outp on')

output_data = pd.DataFrame()

for n in tqdm(list(range(len(gate_potentials)))):

    gatesource.write('volt:offs ' + str(gate_potentials[n] / 2))

    sourcemeter = keithley.keithley(com_keithley)

    sourcemeter.write('*RST')
    sourcemeter.write(':SOUR:FUNC CONC OFF')
    sourcemeter.write(':ARM:COUN 1')
    sourcemeter.write(':SOUR:FUNC VOLT')
    sourcemeter.write(':SENS:FUNC "CURR:DC"')
    sourcemeter.write(':SYST:RCM MULT')

    sourcemeter.write(':SOUR:SOAK ' + str(estab))
    sourcemeter.write(':SOUR:VOLT:STAR ' + str(voltage_inicial))
    sourcemeter.write(':SOUR:VOLT:STOP ' + str(voltage_final))
    sourcemeter.write(':SOUR:VOLT:STEP ' + str(passo))
    sourcemeter.write(':SOUR:SWE:RANG AUTO\n')

    sourcemeter.write(':SENS:CURR:PROT 1')
    sourcemeter.write(':SOUR:SWE:SPAC LIN')
    sourcemeter.write(':SOUR:SWE:POIN ' + str(int(num_pontos2)))
    sourcemeter.write(':SOUR:SWE:DIR UP')
    sourcemeter.write(':TRIG:DEL ' + str(delay_t))
    sourcemeter.write(':TRIG:COUN ' + str(int(num_pontos)))
    sourcemeter.write(':FORM:ELEM CURR')

    sourcemeter.write(':SOUR:VOLT:MODE SWE')
    sourcemeter.write(':SOUR:DEL ' + str(delay_sm))
    sourcemeter.write(':OUTP ON')
    sourcemeter.query(':READ?')
    y_value = sourcemeter.query_ascii_values(':FETC?')
    sourcemeter.write(':OUTP OFF')
    sourcemeter.write(':SOUR:VOLT 0')

    current = {'y_value': y_value}
    y_value = current.get('y_value')
    y_value2 = np.array(y_value) * 1000
    potential_values = [value for value in np.arange(voltage_inicial, voltage_final, passo)]
    output_data = pd.concat(
            [output_data, pd.DataFrame([potential_values, y_value2]).transpose()],
            axis=1,
            ignore_index=False,
            copy=True
        )

gatesource.write('outp off')

meas_conditions = pd.DataFrame([voltage_inicial, voltage_final, passo, delay_t, delay_sm, estab, taxa_varredura])\
    .set_axis(
        [
            'Voltage Inicial (V)',
            'Voltage Final (V)',
            'passo (V)',
            'delay potential change (s)',
            'application time (s)',
            'stabilization_time (s)',
            'meas rate (V/s)'
        ],
    axis=0)


voltage_array = output_data.iloc[:, ::2].to_numpy()
current_array = output_data.iloc[:, 1::2].to_numpy()

#output_data.to_csv('test.txt', sep='\t', index=False, header=['V (V)', 'current (mA)'])

for key, values in enumerate(current_array):
    plt.plot(voltage_array[key][:], current_array[key][:], 'd')
    plt.show()
