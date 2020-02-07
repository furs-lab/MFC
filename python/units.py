# -*- coding: utf-8 -*-
from numpy import clip,rint
from scipy.optimize import root_scalar 
#модуль перевода между единицами измерения
#если надо добавить единицу измерения
#1. добавить ее название в unitsfm, если единица для расходомера или в unitsvalve если для клапана
#2. добавить маску ввода в  maskfm или maskvalve, соответственно (см. документацию PyQt на QLineEdit.setInputMask)
#3. добавить формулу перевода из единиц 0-1023 в новые единицы измерения в функцию pwm2unit (см. инструкцию в функции)
unitsfm = ['PWM', '%PWM', 'l/min']	#единицы измерения расходомера (PWM  единицы ШИМ 0-1023)
unitsvalve = ['PWM', '%PWM']		#единицы измерения клапана
maskfm = ['0000', '000.0', '00.0']	#маски ввода в соответствующих единицах измерения для расходомера
maskvalve = ['0000', '000.0']		#для клапана

#функция перевода величины pwm из единиц 0-1023 в единицы измерения units для расходомера (dev='fm') и клапана (dev='valve')
def pwm2unit(pwm, unit, dev='fm'):  #dev = 'fm' for flow meter and 'valve' for valve
    pwm = clip(pwm,0,1023)
    
    if unit == 'PWM':
        return pwm
    
    if unit == '%PWM':
        return pwm*100./1023.
    
    if unit == 'l/min' and dev == 'fm':
        return clip((pwm - 200)*50./(1023-200), 0, 50)
    
    #добавить функцию для пересчета новых единиц здесь
    #if unit == 'new_unit' and dev == 'fm':     #'new_unit' - название новой единицы, dev - устройство 'fm' для расходомера 'valve' клапан
    #    добавить тут функцию для пересчета pwm  в новые единицы
    #    return результат

    return -1

def pwm2unitEq(pwm, pwm0, unit, dev='fm'):
    return pwm2unit(pwm,unit,dev) - pwm0

def unit2pwm(val, unit, dev='fm'):
    try:
        sol = root_scalar(pwm2unitEq, args=(val,unit,dev),method='bisect',bracket=[0, 1023])  
        return int(rint(sol.root))
    except:
        return -1

#print unit2pwm(10.1,'l/min')
