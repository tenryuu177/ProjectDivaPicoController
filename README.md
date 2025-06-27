# Project Diva Controller

## Main features:
- Cheap (about 10€)
- Compact (fits 250x250 Print beds)
- 4 Main buttons
- Fake Slide pad using buttons
- Enter/Escape Keys


## What you need:
- 1x Raspberry Pi Pico (with USB-C)
- 8x Kailh Choc switches
- 10x WS2812B 5050SMD LEDs
- 3D Printer
- Clear Filament and any other color you might want
- Soldering Iron
- Wires
- Protoboard/Perfboard for easier wiring (optional but highly recommended)

# How to build:
Choose between the press fit and the M3 threaded version and print all parts.
The buttons don't require any post-processing when printed with 0.1mm layers they are smooth enough as is.
Print the buttons with low infill so that they stay lightweight and more transparent. I choose to give them all different infill patterns similar to their symbol.

## Wiring
### Buttons
I choose the following GPIO Pins

Triangle/W GP16

Square/A GP17

Cross/S: GP18 

Circle/D: GP19 

Enter: GP20 

Escape: GP21 

Slide Left/Q: GP4 

Slide Right/E: GP5

However, you can wire these any way you want and then alter the assigned GPIO Pins starting from line 23 in the code.

### LEDs
The first 4 LEDs are Triangle, Square, Cross, and Circle in that order and light up along with button presses.

The last 6 LEDs can be placed in any order underneath the slide pad. They light up when either side is pressed.

The Data In of the first LED has to be connected with GP0 after that, they are wired in series.
![LED-Pinout](/Pictures/WS2812B-Addressable-RGB-LED-pinout-diagram.jpg)
![LED-Order](/Pictures/LED-Order.png)

# Raspberry setup

First, flash your Raspberry with the latest Circuit Python version available: https://circuitpython.org/board/raspberry_pi_pico/

Then drop the content of the Raspberry folder onto your Raspberry.

The 'lib' folder and 'code.py' should be in root.

After disconnecting and reconnecting your Raspberry, the board should light up after a few seconds





# Disclaimer
The code was entirely written by Google Gemini.
I only changed some values for the LEDs
