import board
import digitalio
import usb_hid
import time
import neopixel
import math # Used for sine wave calculation for pulsing LEDs
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# --- Configuration Section ---

# NeoPixel Setup:
# Connect the Data In (DI) pin of your WS2812B LED strip to GP0 on the Pico.
PIXEL_PIN = board.GP0
NUM_PIXELS = 10  # Total number of WS2812B LEDs in your strip/chain
BRIGHTNESS = 0.3 # Global brightness for all NeoPixels (0.0 to 1.0, 0.3 is a good starting point)

# Button Setup:
# Map each button's GPIO pin to its corresponding keyboard Keycode.
# Connect one leg of each button to the specified GP pin, and the other leg to a GND pin.
# The internal pull-up resistors will ensure the pin is HIGH when the button is not pressed.
BUTTON_CONFIG = {
    board.GP16: Keycode.W, # Updated W pin
    board.GP17: Keycode.A, # Updated A pin
    board.GP18: Keycode.S, # Updated S pin
    board.GP19: Keycode.D, # Updated D pin
    board.GP4: Keycode.Q,  # Updated Q pin
    board.GP5: Keycode.E,  # Updated E pin
    board.GP21: Keycode.ESCAPE, # Updated Escape pin
    board.GP20: Keycode.ENTER,  # Updated Enter pin
}

# LED Base Colors (RGB tuples):
# These are the static colors when the LEDs are not actively pulsing or overridden.
COLOR_GREEN = (0, 255, 0)
COLOR_PINK = (255, 0, 255)
COLOR_BLUE = (0, 0, 255)
COLOR_RED = (255, 0, 0)
COLOR_YELLOW = (255, 255, 0)
COLOR_OFF = (0, 0, 0) # Represents an LED being off

# Pulsing Animation Configuration:
PULSE_DURATION = 0.5  # Time in seconds for one full pulse cycle (e.g., from dimmest to brightest and back)
PULSE_MAGNITUDE_FACTOR = 0.6 # How much the brightness varies during the pulse (0.0 = no change, 1.0 = dims significantly)

# --- Initialization Section ---

# Initialize the HID Keyboard device for USB communication.
keyboard = Keyboard(usb_hid.devices)

# Initialize the NeoPixel strip.
# `auto_write=False` means we manually call `pixels.show()` to update the LEDs.
pixels = neopixel.NeoPixel(PIXEL_PIN, NUM_PIXELS, brightness=BRIGHTNESS, auto_write=False)

# Prepare button objects and their states.
# This dictionary will store the DigitalInOut object, keycode, and current pressed state for each button.
buttons = {}
for pin, keycode in BUTTON_CONFIG.items():
    button = digitalio.DigitalInOut(pin)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP  # Enable internal pull-up resistor for button input
    buttons[pin] = {"object": button, "keycode": keycode, "is_pressed": False}

# Store the `time.monotonic()` timestamp when a relevant button was last pressed.
# This helps in calculating the phase of the pulsing animation.
pulse_start_times = {
    Keycode.W: 0.0, # Initialize with 0.0 (or any non-zero value to indicate not pulsing)
    Keycode.A: 0.0,
    Keycode.S: 0.0,
    Keycode.D: 0.0,
}

# --- Helper Functions Section ---

def wheel(pos):
    """
    Generates a color from a rainbow wheel.
    Input `pos` is an integer from 0 to 255, representing a position in the color spectrum.
    Returns an RGB tuple (R, G, B).
    The colors transition smoothly from red -> green -> blue -> back to red.
    """
    if pos < 0 or pos > 255:
        return (0, 0, 0) # Return black if position is out of range
    if pos < 85:  # Red to Green
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170: # Green to Blue
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    # Blue to Red
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)

def apply_pulse(base_color, keycode, pulse_duration, pulse_magnitude_factor):
    """
    Applies a smooth pulsing effect to a given base color.
    The LED's brightness will smoothly cycle from `(1.0 - pulse_magnitude_factor)`
    of its original brightness up to `1.0` of its original brightness.
    
    Args:
        base_color (tuple): The original RGB color (e.g., (0, 255, 0)).
        keycode (Keycode): The keycode associated with the button that triggers this pulse.
                           Used to retrieve the pulse start time.
        pulse_duration (float): The time in seconds for one complete pulse cycle.
        pulse_magnitude_factor (float): How much the brightness varies (0.0 to 1.0).
                                        0.0 means no pulse (constant brightness), 1.0 means it dims significantly.
                                        
    Returns:
        tuple: The adjusted RGB color with the pulsing effect applied.
    """
    start_time = pulse_start_times[keycode]
    if start_time == 0.0:
        # If start_time is 0.0, it means the button is not pressed, so no pulse.
        return base_color

    elapsed_time = time.monotonic() - start_time
    
    # Calculate a sine wave value that smoothly oscillates between 0.0 and 1.0.
    # `elapsed_time * 2 * math.pi / pulse_duration` ensures one full cycle over `pulse_duration`.
    # `(math.sin(...) + 1) / 2` transforms the sine wave from [-1, 1] to [0, 1].
    pulse_val = (math.sin(elapsed_time * 2 * math.pi / pulse_duration) + 1) / 2

    # Calculate the current brightness multiplier.
    # This multiplier ranges from (1.0 - pulse_magnitude_factor) (dimmest) to 1.0 (brightest).
    current_brightness_factor = (1.0 - pulse_magnitude_factor) + (pulse_val * pulse_magnitude_factor)
    
    # Apply the calculated brightness multiplier to each color component (R, G, B).
    adjusted_color = tuple(int(c * current_brightness_factor) for c in base_color)
    return adjusted_color

# --- Main Program Loop ---

rainbow_offset = 0  # Used to animate the rainbow spectrum for LEDs 5-10

while True:
    current_time = time.monotonic() # Get current time for precise pulsing calculations

    # --- 1. Process Button States ---
    for pin, button_data in buttons.items():
        button_obj = button_data["object"]
        keycode = button_data["keycode"]

        # Check if the button is currently pressed (pin reads LOW)
        # and if its state has changed from not pressed to pressed.
        if not button_obj.value and not button_data["is_pressed"]:
            buttons[pin]["is_pressed"] = True  # Update internal state
            keyboard.press(keycode)            # Send 'press' HID event to the computer
            
            # If this button is one of the ones that triggers an LED pulse,
            # record the current time as the start of its pulse.
            if keycode in pulse_start_times:
                pulse_start_times[keycode] = current_time

        # Check if the button is currently released (pin reads HIGH)
        # and if its state has changed from pressed to released.
        elif button_obj.value and button_data["is_pressed"]:
            buttons[pin]["is_pressed"] = False # Update internal state
            keyboard.release(keycode)          # Send 'release' HID event to the computer
            
            # If this button was pulsing, reset its pulse timer.
            # Setting it to 0.0 tells `apply_pulse` to stop pulsing.
            if keycode in pulse_start_times:
                pulse_start_times[keycode] = 0.0

    # --- 2. Update LED States ---

    # LED 1 (Index 0): Constant Green, Pulse when W is pressed.
    if buttons[board.GP16]["is_pressed"]: # Check if W key is currently held down
        pixels[0] = apply_pulse(COLOR_GREEN, Keycode.W, PULSE_DURATION, PULSE_MAGNITUDE_FACTOR)
    else:
        pixels[0] = COLOR_GREEN # Static green when W is not pressed

    # LED 2 (Index 1): Constant Pink, Pulse when A is pressed.
    if buttons[board.GP17]["is_pressed"]: # Check if A key is currently held down
        pixels[1] = apply_pulse(COLOR_PINK, Keycode.A, PULSE_DURATION, PULSE_MAGNITUDE_FACTOR)
    else:
        pixels[1] = COLOR_PINK

    # LED 3 (Index 2): Constant Blue, Pulse when S is pressed.
    if buttons[board.GP18]["is_pressed"]: # Check if S key is currently held down
        pixels[2] = apply_pulse(COLOR_BLUE, Keycode.S, PULSE_DURATION, PULSE_MAGNITUDE_FACTOR)
    else:
        pixels[2] = COLOR_BLUE

    # LED 4 (Index 3): Constant Red, Pulse when D is pressed.
    if buttons[board.GP19]["is_pressed"]: # Check if D key is currently held down
        pixels[3] = apply_pulse(COLOR_RED, Keycode.D, PULSE_DURATION, PULSE_MAGNITUDE_FACTOR)
    else:
        pixels[3] = COLOR_RED

    # LEDs 5-10 (Indices 4-9): Rainbow Spectrum, Glow Yellow when Q or E is pressed.
    # Check if either Q or E key is currently held down.
    is_qe_pressed = buttons[board.GP4]["is_pressed"] or buttons[board.GP5]["is_pressed"]

    for i in range(4, NUM_PIXELS): # Loop through LEDs from index 4 up to NUM_PIXELS-1
        if is_qe_pressed:
            pixels[i] = COLOR_YELLOW # Override to static yellow if Q or E is pressed
        else:
            # Apply the rainbow cycling effect.
            # `i * (256 // NUM_PIXELS)` spreads the colors nicely across the LEDs.
            # `rainbow_offset` shifts the entire rainbow for animation.
            pixel_color_pos = (i * (256 // NUM_PIXELS) + rainbow_offset) % 256
            pixels[i] = wheel(pixel_color_pos)

    # Advance the rainbow animation for the next loop iteration.
    rainbow_offset = (rainbow_offset + 1) % 256 # Cycle offset from 0 to 255

    pixels.show() # Send the updated color data to the NeoPixels. This makes the changes visible.

    time.sleep(0.01) # Small delay to prevent busy-waiting and allow other processes to run smoothly.
