#!/usr/bin/env python3

# What are the specifications of the robots?
# Are we allowed four motors?
# How will we need to change our code if we use a omni wheel instead?

# If you are not me and you are reading this, you are expected to understand this.
from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C,OUTPUT_D, SpeedPercent
from ev3sim.code_helpers import wait_for_tick
from ev3dev2.sensor import INPUT_2, INPUT_3, Sensor, INPUT_1
from ev3dev2.sensor.lego import ColorSensor, UltrasonicSensor, InfraredSensor
import time

# Sensors and motors.
# Fairly uselss at the moment
cs = ColorSensor(INPUT_2)
us = UltrasonicSensor(INPUT_3)

# The four motors.
# 'motor1' and 'motor2' are the horizontal motors.
# 'motor3' and 'motor4' are the vertical motors.
motor1 = LargeMotor(OUTPUT_A)
motor2 = LargeMotor(OUTPUT_B)
motor3 = LargeMotor(OUTPUT_C)
motor4 = LargeMotor(OUTPUT_D)

# Enums but not really.
INF_DIR_NO_SIG = 0
INF_DIR_FAR_LEFT = 1
INF_DIR_MED_LEFT = 2
INF_DIR_LEFT = 3
INF_DIR_CEN_LEFT = 4
INF_DIR_CEN = 5
INF_DIR_CEN_RIGHT = 6
INF_DIR_RIGHT = 7
INF_DIR_MED_RIGHT = 8
INF_DIR_FAR_RIGHT = 9

# TODO: Use the compass to determine where we are facing relative to our original direction.
# Use this to help us locate where the goals is.
off_direction = 0

# percent 87 time 0.4 sec for 90 deg rotation left
rotate_magic_p = 97
rotate_magic_t = 0.4
motor_magic_t = 0.4
def rotate_left(deg, Block):
    motor1.on_for_seconds(SpeedPercent(rotate_magic_p * deg / 90), rotate_magic_t, block=Block)
    global off_direction
    off_direction -= deg

def rotate_right(deg, Block):
    motor1.on_for_seconds(SpeedPercent(rotate_magic_p * -deg / 90), rotate_magic_t, block=Block)
    global off_direction
    off_direction += deg

# Don't use 'left' and 'right' to get to the ball - go directly to it using
# 'rotate_left' and 'rotate_right'
def forward(p, sec, Block):
    motor3.on_for_seconds(SpeedPercent(p), sec,block=Block)
    motor4.on_for_seconds(SpeedPercent(p), sec)

def backward(p, sec, Block):
    motor3.on_for_seconds(SpeedPercent(-p), sec, block=Block)
    motor4.on_for_seconds(SpeedPercent(-p), sec)

def left(p, sec, Block):
    motor1.on_for_seconds(SpeedPercent(p), sec, block=Block)
    motor2.on_for_seconds(SpeedPercent(p), sec)

def right(p, sec, Block):
    motor1.on_for_seconds(SpeedPercent(-p), sec, block=Block)
    motor2.on_for_seconds(SpeedPercent(-p), sec)
    
# The first element of the tuple returned is the general direction,
# the second element is the strength.
def inf_direction_strength(inf):
    INF_DIRECTION = 0
    INF_STRENGTH = 6
    return (inf.value(INF_DIRECTION), inf.value(INF_STRENGTH))

def inf_subsensors(inf):
    return (inf.value(i) for i in range(1, 6))

def go_for_goal(inf):
    data = inf_direction_strength(inf)
    while data[0] == INF_DIR_CEN:
        forward(100, motor_time, False)
        data = inf_direction_strength(inf)

# TODO: Implement a function that will determine where the ball
# is in terms of a relative angle of rotation. DONE
def determine_direction(inf):
    GRANULARITY = 20
    data = inf_direction_strength(inf)
    if data[1] < 4:
        if data[0] < INF_DIR_CEN:
            rotate_left(GRANULARITY, False)
        elif data[0] > INF_DIR_CEN:
            rotate_right(GRANULARITY, False)
    else:
        global off_direction
        if off_direction > 0:
            rotate_left(off_direction)
        else:
            rotate_right(off_direction)
        go_for_goal(inf)

# Instantiate the ultrasonic sensor
us = UltrasonicSensor(INPUT_3)

# Bit late for the initialisation of the infrared sensor, but...
inf = Sensor(INPUT_1, driver_name="ht-nxt-ir-seek-v2") 

FREQ = 1
# Uncomment time stuff to do scheduling
# last_time = time.time()
# TODO: Implement scheduling to run a check on the colour underneat the bot.
# If it is white (#FFFFFF) go back immediately (this is out of bounds).
# Use the colour sensor for this.

motor_time = 0.2

last_us = us.distance_centimeters
# TODO: Use rotation instead of going left/right and then forward (more efficient)
while True:
    wait_for_tick() # All loops in the simulator must start with wait_for_tick

    data = inf_direction_strength(inf)

    if data[0] == 0:
        forward(100, motor_time, False)
        continue
    if data[0] < INF_DIR_CEN:
        left(100, motor_time, False)
    elif data[0] > INF_DIR_RIGHT:
        right(100, motor_time, False)
    else:
        while data[0] == INF_DIR_CEN:
            forward(100, motor_time, False)
            data = inf_direction_strength(inf)