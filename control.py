from inputs import get_gamepad
import socket
import time

'''
CONTROLS:

LEFT STICK: up/down is altitude, left/right is yaw
RIGHT STICK:  up/down is forward/back, left/right is left/right

Cross: Land
Triange: Takeoff
Square: Account for X/Y drift
Circle: Emergency Stop

R1 + L1: Recalibrate Gyro

'''

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
payload = "036680808080000099"

lastcheck = 0.0
button_states = { "BTN_TR": 0, "BTN_TL": 0}
buttons_held = False

fixing_drift = False

RECALIBRATE_PAYLOAD = "0101"
DRONE_IP = "192.168.1.1"
DRONE_PORT = 7099

def xor_bytes(bytes1, bytes2):
    length = min(len(bytes1), len(bytes2))
    result = bytes(b1 ^ b2 for b1, b2 in zip(bytes1[:length], bytes2[:length]))
    return result

def checksumbyte(payload):
	x = bytes.fromhex(payload[4:6])
	y = bytes.fromhex(payload[6:8])
	a = bytes.fromhex(payload[8:10])
	t = bytes.fromhex(payload[10:12])
	s = bytes.fromhex(payload[12:14])

	result = xor_bytes(xor_bytes(x,y), xor_bytes(a,t))
	result = xor_bytes(result, s)

	payload = payload[:14] + result.hex() + payload[16:]
	return payload


try:
	while True:
		events = get_gamepad()
		for event in events:

			if event.ev_type == "Key":
				button_states[event.code] = event.state

			if event.code == "ABS_RX":
				rx = format(event.state, '02x')
				payload = payload[:4] + rx + payload[6:]
			elif event.code == "ABS_RY":
				ry = format(abs(event.state-255), '02x')
				payload = payload[:6] + ry + payload[8:]
			elif event.code == "ABS_Y":
				ly = format(abs(event.state-255), '02x')
				payload = payload[:8] + ly + payload[10:]
			elif event.code == "ABS_X":
				lx = format(event.state, '02x')
				payload = payload[:10] + lx + payload[12:]

			elif event.code == "BTN_SOUTH" and event.state == 0:
				payload = payload[:12] + '02' + payload[14:]
				lastcheck = 0.0
			elif event.code == "BTN_NORTH" and event.state == 0:
				payload = payload[:12] + '01' + payload[14:]
				lastcheck = 0.0
			elif event.code == "BTN_EAST" and event.state == 0:
				payload = payload[:12] + '04' + payload[14:]
				lastcheck = 0.0
			elif (event.code == "BTN_WEST" and event.state == 0):
				payload = payload[:12] + '10' + payload[14:]
				lastcheck = 0.0
				fixing_drift = not fixing_drift

			if button_states.get("BTN_TR", 0) and button_states.get("BTN_TL", 0) and not buttons_held:
				lastcheck = 0.0
				buttons_held = True
			elif (not button_states.get("BTN_TR", 0) or not button_states.get("BTN_TL", 0)) and buttons_held:
				buttons_held = False

		payload = checksumbyte(payload)
		timenow = time.time()


		if timenow - lastcheck >= 0.1:
			if buttons_held:
				print(RECALIBRATE_PAYLOAD)
				sock.sendto(bytes.fromhex(RECALIBRATE_PAYLOAD), (DRONE_IP, DRONE_PORT))
			else:
				print(payload)
				sock.sendto(bytes.fromhex(payload), (DRONE_IP, DRONE_PORT))
				if lastcheck == 0.0 and not fixing_drift:
					payload = payload[:12] + '00' + payload[14:]

			lastcheck = timenow

except KeyboardInterrupt:
	print("Stopped.")
	sock.close()
