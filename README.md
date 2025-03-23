# SquidGame
A self tuning motorcycle ECM project.

The goal is to be optimized for plug and play performance. Starting with support for up to 4 cylinders, and any sensors you can throw at it. 
Dyno support is included.

From installation to a fully self-tuned, high resolution, Fuel Map will take about 90 hours of riding with current parameters, this can be cut down to about 8 hours on a dyno.
There is currently implemented support for drag/drop map sharing.

Code will be optimized for single cylinder engines, despite the name of the project. This should, however, translate nicely to per-cylinder maps on different motors.

The parts list is hovering around 650 dollars right now, but you already have most of these modules, which significantly lowers that price of entry.

It's pretty close to just "wire it up and go." A quick peek at the code shows where you need to make your own changes.


# Currently implemented

Single cylinder

Fully self-tuning fuel map, with 3 stages of increasing resolution

Cold Start optimization

Fuel Efficiency / High performance toggle

HUD

Dyno Mode

Drag and Drop fuel maps in json format

# In Progress

Auto-detection of additional cylinders

Handling loss of cylinder / Limp mode

Individual maps for respective cylinders

Quickshift (up only)

# Long-Term Goals

Flipper zero style HUD with a squid encouraging you to get out and ride to fill out that map

Recommendations for you to ride a certain way to teach the needed cells in the fuel map

Bluetooth enabled app
