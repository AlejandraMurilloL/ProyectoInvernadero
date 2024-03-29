'''
**********************************************************************
* Filename    : dht11.py
* Description : test for SunFoudner DHT11 humiture & temperature module
* Author      : Dream
* Brand       : SunFounder
* E-mail      : service@sunfounder.com
* Website     : www.sunfounder.com
* Update      : Dream    2016-09-30    New release
**********************************************************************
'''
import RPi.GPIO as GPIO
import time, datetime
import Conexion, threading, Duracion
import GiroArriba,ActivarElectrovalvula
import GiroAbajo,DesactivarElectrovalvula

DHTPIN = 17

GPIO.setmode(GPIO.BCM)

MAX_UNCHANGE_COUNT = 100

STATE_INIT_PULL_DOWN = 1
STATE_INIT_PULL_UP = 2
STATE_DATA_FIRST_PULL_DOWN = 3
STATE_DATA_PULL_UP = 4
STATE_DATA_PULL_DOWN = 5

def read_dht11_dat():
        GPIO.setmode(GPIO.BCM)
	GPIO.setup(DHTPIN, GPIO.OUT)
	GPIO.output(DHTPIN, GPIO.HIGH)
	time.sleep(0.05)
	GPIO.output(DHTPIN, GPIO.LOW)
	time.sleep(0.02)
	GPIO.setup(DHTPIN, GPIO.IN, GPIO.PUD_UP)

	unchanged_count = 0
	last = -1
	data = []
	while True:
		current = GPIO.input(DHTPIN)
		data.append(current)
		if last != current:
			unchanged_count = 0
			last = current
		else:
			unchanged_count += 1
			if unchanged_count > MAX_UNCHANGE_COUNT:
				break

	state = STATE_INIT_PULL_DOWN

	lengths = []
	current_length = 0

	for current in data:
		current_length += 1

		if state == STATE_INIT_PULL_DOWN:
			if current == GPIO.LOW:
				state = STATE_INIT_PULL_UP
			else:
				continue
		if state == STATE_INIT_PULL_UP:
			if current == GPIO.HIGH:
				state = STATE_DATA_FIRST_PULL_DOWN
			else:
				continue
		if state == STATE_DATA_FIRST_PULL_DOWN:
			if current == GPIO.LOW:
				state = STATE_DATA_PULL_UP
			else:
				continue
		if state == STATE_DATA_PULL_UP:
			if current == GPIO.HIGH:
				current_length = 0
				state = STATE_DATA_PULL_DOWN
			else:
				continue
		if state == STATE_DATA_PULL_DOWN:
			if current == GPIO.LOW:
				lengths.append(current_length)
				state = STATE_DATA_PULL_UP
			else:
				continue
	if len(lengths) != 40:
		print "Data not good, skip"
		return False

	shortest_pull_up = min(lengths)
	longest_pull_up = max(lengths)
	halfway = (longest_pull_up + shortest_pull_up) / 2
	bits = []
	the_bytes = []
	byte = 0

	for length in lengths:
		bit = 0
		if length > halfway:
			bit = 1
		bits.append(bit)
	#print "bits: %s, length: %d" % (bits, len(bits))
	for i in range(0, len(bits)):
		byte = byte << 1
		if (bits[i]):
			byte = byte | 1
		else:
			byte = byte | 0
		if ((i + 1) % 8 == 0):
			the_bytes.append(byte)
			byte = 0
	#print the_bytes
	checksum = (the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3]) & 0xFF
	if the_bytes[4] != checksum:
		print "Data not good, skip"
		return False

	return the_bytes[0], the_bytes[2]


datoSenHume = 0
hlDuracion = threading.Thread()
hlDuracionRiego = threading.Thread()

def consultarEstado():
    global hlDuracion
    estadoMovil = True
    while estadoMovil == True:
        try:
                resultado = Conexion.mtdConsultarModificacion()
                if resultado:
                    Tiempo = True
                    hlDuracion = threading.Thread(target=Duracion.cuentaRegresiva,args=(resultado[0][2],))
                    hlDuracion.start()
                    if resultado[0][0] == "Bajar":
                         print "Bajando..."
                         result = Conexion.mtdConsultarEstado()                         
                         if result[0][0] == "Off":
                                 print("Las cortinas ya estan abajo")
                                 Conexion.mtdActualizarEstadoModi(resultado[0][1])
                         else:
                                 GiroAbajo.mtdActivarMotorAbajo()
                                 Conexion.mtdActualizarEstado("Off")
                                 Conexion.mtdActualizarEstadoModi(resultado[0][1])
                    elif resultado[0][0] == "Subir":
                         print "Subiendo..."
                         result = Conexion.mtdConsultarEstado()
                         if result[0][0] == "On":
                                 print("Las cortinas ya estan arriba")
                                 Conexion.mtdActualizarEstadoModi(resultado[0][1])
                         else:
                                 GiroArriba.mtdActivarMotorArriba()
                                 Conexion.mtdActualizarEstadoModi(resultado[0][1])
                                 Conexion.mtdActualizarEstado("On")
                        
                        
               
                time.sleep(3)
        except Exception as e:
                        estadoMovil = False
                        print(e)


def consultarEstadoRiego():
    global hlDuracionRiego
    estadoMovil = True
    while estadoMovil == True:
        try:
                resultado = Conexion.mtdConsultarModificacionR()
                if resultado:
                    Tiempo = True
                    hlDuracionRiego = threading.Thread(target=Duracion.cuentaRegresiva,args=(resultado[0][2],))
                    hlDuracionRiego.start()
                    if resultado[0][0] == "Cerrar":
                         print "Cerrando..."
                         result = Conexion.mtdConsultarEstadoR()                         
                         if result[0][0] == "Off":
                                 print("El sistema de riego ya esta desactivado")
                                 Conexion.mtdActualizarEstadoModi(resultado[0][1])
                         else:
                                 DesactivarElectrovalvula.desactivar()
                                 Conexion.mtdActualizarEstadoR("Off")
                                 Conexion.mtdActualizarEstadoModi(resultado[0][1])
                    elif resultado[0][0] == "Abrir":
                         print "Abriendo..."
                         result = Conexion.mtdConsultarEstadoR()
                         if result[0][0] == "On":
                                 print("El sistema de riego ya esta activado")
                                 Conexion.mtdActualizarEstadoModi(resultado[0][1])
                         else:
                                 ActivarElectrovalvula.activar()
                                 Conexion.mtdActualizarEstadoModi(resultado[0][1])
                                 Conexion.mtdActualizarEstadoR("On")
                        
                        
               
                time.sleep(3)
        except Exception as e:
                        estadoMovil = False
                        print(e)


def tomarDatos():
        #GPIO SETUP
        try:
                channel = 21
                global datoSenHume 
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(channel, GPIO.IN)
                
                actual = datetime.datetime.now()
                fecha =  actual.strftime("%Y-%m-%d")
                if GPIO.input(channel)==GPIO.HIGH:
                        
                                
                        print "NO se ha detectado AGUA"
                        datoSenHume = 0
                        Conexion.mtdGuardarDatosH(0,fecha,time.strftime("%X"))
                else:
                        print "Se ha detectado AGUA"
                        datoSenHume = 100
                        Conexion.mtdGuardarDatosH(100,fecha,time.strftime("%X"))
                
                
        except KeyboardInterrupt:
                GPIO.cleanup()

        
def main():
        global hlDuracion, datoSenHume
        estadoNormal = True
        print '''
        **********************************************************************
        * Filename    : GREENHOUSE 
        * Description : Tomar valores de sensores y actuar segun estos
        * Author      : ADSI-1365211, Alejandra,Ana,Dixon,Juan
        * Update      : 12-09-2018 
        **********************************************************************
        \n'''
	hilo1 = threading.Thread(target=consultarEstado)
        hilo1.start()
        
	while estadoNormal == True:
                try:
                        print "**********************************************************"
                        tomarDatos()
                        if datoSenHume == 0:
                                ActivarElectrovalvula.activar()
                        else:
                                DesactivarElectrovalvula.desactivar()
                        
                        result = read_dht11_dat()
                        if result:
                                humidity, temperature = result
                                actual = datetime.datetime.now()
                                fecha =  actual.strftime("%Y-%m-%d")
                                print "Temperatura: %s C`" % (temperature)
                                Conexion.mtdGuardarDatos(temperature,fecha,time.strftime("%X"))
                                
                                if hlDuracion.isAlive() == False:
                                        
                                        resultado = Conexion.mtdConsultarEstado()
                                        if temperature < 22:                                
                                                if resultado[0][0] == "Off":
                                                        print("Las cortinas ya estan abajo")
                                                else:
                                                        
                                                        GiroAbajo.mtdActivarMotorAbajo()
                                                        Conexion.mtdActualizarEstado("Off")
                                        else:
                                                if resultado[0][0] == "On":
                                                        print("Las cortinas ya estan arriba")
                                                else:
                                                        
                                                        GiroArriba.mtdActivarMotorArriba()
                                                        Conexion.mtdActualizarEstado("On")
                                else:
                                        print("La duracion de la modificacion realizada desde el movil aun no se ha terminado")
                        print "**********************************************************"
                        time.sleep(120)
		except Exception as e:
                        estadoNormal = False
                        print(e)

def destroy():
	GPIO.cleanup()

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		destroy() 
