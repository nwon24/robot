#!/usr/bin/env python3
# Don't worry about the above (don't change it though) - it's for when we have a physical robot
# to work with.

# READ ALL COMMENTS VERY CAREFULLY.

# At the moment, the robot simply responds to the ball by moving left/right
# and then forward. It DOES NOT know what to do if the ball is behind it.
# It DOES NOT know how to get the ball to the goal once it actually reaches the ball.
# However, getting the ball to the backboard suffices for the training exercises.

# I have put TODO: tags on places where there is something to do and hopefully
# you can at least have a think about it.

# Just some general questions, mostly for me.
# What are the specifications of the robots?
# Are we allowed four motors?
# How will we need to change our code if we use a omni wheel instead?

# If you are not me and you are reading this, you are expected to understand this.
# These are just all the imports, don't worry too much about it.
# However, if you need to import anything else for whatever reason, add it here;
# don't sprinkle it throughout the code. That is plain ugly.
from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C,OUTPUT_D, SpeedPercent
from ev3sim.code_helpers import wait_for_tick
from ev3dev2.sensor import INPUT_2, INPUT_3, Sensor, INPUT_1, INPUT_4
from ev3dev2.sensor.lego import ColorSensor, UltrasonicSensor, InfraredSensor
import time
import math

def congruent(a, m):
    tmp = a %m
    if tmp > m/2:
        tmp = tmp - m
    return tmp

MEDIUM_MOTOR = 0
LARGE_MOTOR = 1
class Robot():
    # The colour sensor is fairly uselss at the moment.
    # TODO: Use the colour sensor to determine if we are on the boundary of the playing field;
    # if that is the case, go back immediately, as the robot is not allowed outside of the playing area.
    cs = ColorSensor(INPUT_2)

    # Motor time units - adjust accordingly depending on what happens for different values.
    # Use trial and error.
    MED_MOTOR_TIME = 0.4
    LARGE_MOTOR_TIME = 0.2
    # How much power/time to go left/right?
    # If you make this too high, the granularity is of each movement is too big.
    # If you make this too low, the robot moves really slowly.
    # Adjust so that the robot movement isn't too high when it is near to the ball
    LARGE_SIDEWAYS_POW = 100
    MED_SIDEWAYS_POW = 100
    LARGE_SIDEWAYS_TIME = 0.1
    MED_SIDEWAYS_TIME = 0.4

    off_direction = 0

    def __init__(self, motor_type):
        self.motor_type = motor_type
        if motor_type == MEDIUM_MOTOR:
            self.motor_time = self.MED_MOTOR_TIME
            self.motor_sideways_pow = self.MED_SIDEWAYS_POW
            self.motor_sideways_time = self.MED_SIDEWAYS_TIME
        else:
            self.motor_time = self.LARGE_MOTOR_TIME
            self.motor_sideways_pow = self.LARGE_SIDEWAYS_POW
            self.motor_sideways_time = self.LARGE_SIDEWAYS_TIME

        # The four motors.
        # 'motor1' and 'motor2' are the horizontal motors.
        # 'motor3' and 'motor4' are the vertical motors.
        if motor_type == MEDIUM_MOTOR:
            self.motor1 = MediumMotor(OUTPUT_A)
            self.motor2 = MediumMotor(OUTPUT_B)
            self.motor3 = MediumMotor(OUTPUT_C)
            self.motor4 = MediumMotor(OUTPUT_D)
        else:
            self.motor1 = LargeMotor(OUTPUT_A)
            self.motor2 = LargeMotor(OUTPUT_B)
            self.motor3 = LargeMotor(OUTPUT_C)
            self.motor4 = LargeMotor(OUTPUT_D)
        # This is where we use the compass to actually do stuff.
        # If the robot rotates for whatever reason (like if it hits the corner of a goal)
        # we want to reotate the right way.
        self.compass = Sensor(INPUT_4, driver_name='ht-nxt-compass')
        # Calibrate the compass sensor.
        self.compass.command = "BEGIN-CAL"
        self.compass.command = "END-CAL"


    # Enums but not really.
    # These are just the values returned from the infrared sensor that tell
    # us in which the direction the ball is.
    # Hopefully the variable names are self explanatory.
    # They are in all caps because they are constants; the infrared sensor
    # will always return numbers that correspond to these values.
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

    # These are a bunch of magic numbers that allow for the robot to turn in an exact number
    # of degrees expressed in terms of motor power and time.
    # These values were found using trial and error, DO NOT CHANGE. I shall know.
    # percent 87 time 0.4 sec for 90 deg rotation left
    rotate_magic_p = 97
    rotate_magic_t = 0.4
    motor_magic_t = 0.4

    # The following routines are general motor functions.
    # The rotatate functions aren't really that helpful at the moment until you figure out
    # how to determine how much to rotate to face the ball.
    # If you do figure this out but cannot write the code, just put it in English somewhere.
    # Don't worry too much about the 'Block' argument; it determines whether the call
    # to 'on' blocks (suspends executation) until it is done or not.
    def rotate_left(self):
        cur_time = time.time()
        self.motor2.off()
        self.motor3.off()
        self.motor4.off()
        self.motor1.on(SpeedPercent(self.rotate_magic_p))

    def rotate_right(self):
        self.motor1.off()
        self.motor3.off()
        self.motor4.off()
        self.motor2.on(SpeedPercent(self.rotate_magic_p))

    # The following routines are fairly self-explanatory and can be easily understood
    # if the comment about which motors are which is understood.
    # In the future, we want to not use 'left' and 'right' to get to the ball -  instead we should go directly to it using
    # 'rotate_left' and 'rotate_right'
    def forward(self, p):
        self.motor1.off()
        self.motor2.off()
        self.motor3.on(SpeedPercent(p))
        self.motor4.on(SpeedPercent(p))

    def backward(self,p):
        self.motor1.off()
        self.motor2.off()
        self.motor3.on(SpeedPercent(-p))
        self.motor4.on(SpeedPercent(-p))

    def left(self,p):
        self.motor3.off()
        self.motor4.off()
        self.motor1.on(SpeedPercent(p))
        self.motor2.on(SpeedPercent(p))

    def right(self, p):
        self.motor3.off()
        self.motor4.off()
        self.motor1.on(SpeedPercent(-p))
        self.motor2.on(SpeedPercent(-p))
 
    # The following routines get information from the infrared sensor.
    # If you read the documentation on Canvas, you will know that the
    # infrared sensor's 0th and 6th values are the average direction
    # strength respectively.
    # Subsensor values are values 1 through 5.
    # You needn't worry about the subsensor values for the moment, until
    # we need more fine-tuned positioning of the robot in relation to the ball.
    # The first element of the tuple returned is the general direction,
    # the second element is the strength.
    # The higher the strength, the closer the ball is.
    # The function returns a tuple - you must cast it into a list using 'list()'
    # as illustrated later.
    def inf_direction_strength(self):
        return (self.inf.value(0), self.inf.value(6))

    def inf_subsensors(self, inf):
        return (self.inf.value(i) for i in range(1, 6))

    # Get the values of the colour sensor.
    def colour_sensor(self):
        return (self.rgb)

    # Get the bearing from the compass
    def bearing(self):
        return self.compass.value()
    # Instantiate the ultrasonic sensor
    # This will be used to determine how far we are away from a wall or something like that.
    us = UltrasonicSensor(INPUT_3)

    # Bit late for the initialisation of the infrared sensor, but...
    inf = Sensor(INPUT_1, driver_name="ht-nxt-ir-seek-v2") 

    # Move at a specific angle
    # CAUTION: BLACK MAGIC AHEAD
    # You are not expected to understand this.
    # TODO: Adapt it to our robot.
    # Currently spins around instead of moving at the proper angle.
    def radial_move(self, angle, speed = 100):
        theta = math.radians(angle)
        values = [0, 0, 0, 0]
        for i in range(4):
            # ????
            values[i] = math.sin(theta - (((2 * i) + 1) * math.pi / 4))
            # ????
            values[i] = round(values[i], 4)
        amp_ratio = speed / max(values)
        values = [min(100, max(-100, amp_ratio)) * x for x in values]

        self.motor1.on(values[0])
        self.motor2.on(values[1])
        self.motor3.on(values[2])
        self.motor4.on(values[3])
   
# Robot moves in square if you call this fucntion
# Just use it to test stuff.
def test_robot(robot):
    while True:
        robot.right(100, 1, False)
        robot.forward(100, 1, False)
        robot.left(100, 1, False)
        robot.backward(100, 1, False)

our_robot = Robot(MEDIUM_MOTOR)
# DON'T WORRY ABOUT THE FOLLOWING FOR NOW.
FREQ = 1
# Uncomment time stuff to do scheduling
# last_time = time.time()
# TODO: Implement scheduling to run a check on the colour underneat the bot.
# If it is white (#FFFFFF) go back immediately (this is out of bounds).
# Use the colour sensor for this.

# NOTE: If testing on a physical robot just to see whether the robot does
# anything remotely useful call 'test_robot' to see if it works.
# In the simulator the robot should move in a square pattern but on
# a physical robot where the motors are not positioned in the same way
# the robot might (probably) do something else, perhaps a little more bizarre.
#test_robot(our_robot)

# This is how close to the ball we deem the infrared sensor to be irrelevant.
# You can change this to see what happens.
close_thresh = 3

# BIG NOTE THAT MUST BE READ:
# The following code is the only part of the code that is only for our bot that
# will actually be on the field.
# If we use another bot as a goal keeper, we can use the all the code written
# above to make it work.
# We just need to import this file.

# Right now, all we are doing is finding out which way the ball is,
# moving horizontally so that we're in line with it, and moving forward.
# It should be enough for a few of the basic soccer exercises, which consist
# of only getting the ball to the backboard.
# TODO: Use rotation instead of going left/right and then forward (more efficient)
# See if you can figure out how to do this.
angle_threshold = 10

# Testing for 'radial_move' method. Uncomment.
# Currently doesn't work. Spins around forever.
#our_robot.radial_move(45)
#while True:
#    pass
while True:
    wait_for_tick() # All loops in the simulator must start with wait_for_tick

    current_time = time.time()
    
    data = our_robot.inf_direction_strength()
#    usdata = our_robot.us.distance_centimeters
    usdata = our_robot.us.distance_centimeters
    angle = our_robot.bearing()

    if congruent(angle, 360) < -angle_threshold:
        our_robot.rotate_left()
        continue
    elif congruent(angle, 360) > angle_threshold:
        our_robot.rotate_right()
        continue
   # If we get no signal then perhaps the ball is behind us.
    if data[0] == our_robot.INF_DIR_NO_SIG:
        our_robot.backward(100)
    # If we are close enough to the ball or it is directly in the centre
    # just head towards it in a straight line.
    elif usdata < close_thresh or data[0] == our_robot.INF_DIR_CEN:
        our_robot.forward(100)
    # Go left or right depending where the ball is.
    # Since we test for 'close_thresh' value in the data collected
    # the ball shouldn't be so close to the robot that the left and
    # right movements result in a perpetual shifting back and forth
    # because a single movement takes the ball from one side of the robot
    # to the other, bypassing the centre.
    elif data[0] < our_robot.INF_DIR_CEN:
        our_robot.left(our_robot.motor_sideways_pow)
    elif data[0] > our_robot.INF_DIR_CEN:
        our_robot.right(our_robot.motor_sideways_pow)