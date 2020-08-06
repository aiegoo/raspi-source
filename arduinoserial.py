import serial
import mysql.connector
from datetime import datetime
import threading
import time

ser = serial.Serial('/dev/ttyACM0',115200)

mydb = mysql.connector.connect(
	host ="localhost",
	user ="root",
	password="pass",
	database="sensor_data"
)

mycursor = mydb.cursor()	
sql = "insert into Sensor_Detections(Server_Name, Detect_Time) values(%s, %s)"

def readarduino(ServerName):
	while True:
		try:
			data=ser.readline()
			
			data2 = data.strip()
			print(data2)
			if data=="<D>":
				now = datetime.now()
				val = (ServerName, now.strftime("%Y-%m-%d %H:%M:%S"))
				mycursor.execute(sql,val)
				mydb.commit()
			print(mycursor.rowcount,"record inserted")
		except KeyboardInterrupt:
			break
		time.sleep(0.05)
	port.close()
	
def startread():
	thread = threading.Thread(target=readarduino, args=("RPI_1",))
	thread.start()


def main():
	startread()
	

if __name__ == '__main__':
    main()
