3/19
- so i've started the shift from OCR to a closed classifier system. i just now begun taking screenshots using the dump system created earlier and now i am cropping images for enhance one by one.... theres no escaping doing some manual work i suppose
- i didnt realize/forgot the dumps happened even if recognition failed so i had to ask chatgpt to explain that part of the code to me again
- im just doing template creation... is this really the right way to learn about this pipeline?
- took most of the day's productivity, but i have finished all sets, rarity, and enhance templates. they are good confidence and work across multiple items. itemlevel might be hard since items can be locked and block most of the itemlevel display,  but perhaps it can be procured with another method by calculating mainstat vs enhancement level with a chart
- created templates for all digits, but ran into a downstream problem: there are 2 gear screens so the program must be able to detect which one it is on to use the correct capture regions. not only that, need to check if the resolution is correct to allow templates to recognize both capture regions, otherwise will have to double up on the templates in case the size of the symbols change.
- decided to use an 'anchor' template to differentiate between profiles before continuing: created a new rectangle for the anchor region by adding a new line to regions_config, as well as setting up for the creation of a second region profile
- created srs/profile_detect.py separately to import later
- modified upstream to import new regions and detect_profile
- now reads anchor rectangle and chooses profile, region map of detail enhance screen not created yet

3/20
goals:
1. finish region profile and capture pipeline for BOTH gear pages
2. implement digit parsing+stitching for substats and mainstats
3. decide what to do with equipment score: either calculate it by deriving it from substats, mainstats, and enhance level, or just capture it
4. create a current source of truth once the upstream data contracts are clean
ended up not working on it today outside of early morning hours from yesterday

3/21
continuing from 3/20
- refactored calibrate_regions to have visible rectangles while working, as well as printing out the dictionary format of the new coordinates. removed dependency on importing from upstream.py
- uninstalled opencv headless which was pulled in while installing easyOCR dependencies

3/28
haven't worked on this project in a week, and got news of an incoming update that will add 'mass enhancements'. in essence it will be a screen with 16 equipments... which means 16 cropping regions. templates will need to be adjusted in case the text size is different. however, since the project is already compartmentalized, it should be fine to fit into the pipeline. for now i will continue and refine the image recognition and tokenization process, before exploring downstream logic.

4/16 
restarting the project in full force. will implement 16 equipment reading.
to-do list
- finish regions_detail
- make templates split by profile since the icons are different sized depending on screen
- confirm things work on different screens
- separation of 'one item recognition' from screen layout. the recognizer needs to read one item given a specific region, regardless of the item came from.
- 16 item screen should give 16 item boxes, parsing through the recognizer.
- define the new 16-item bulk enhancement as a new profile, so 3 profiles total

progress
- added auto detection for adb ports instead of using hard coded 5555 port
- added an exception for recognizing weapon enhancements, since the weapon arts cuts into the crop region
- correctly linked profile type to prevent returning none
- begun creation of new detail specific templates; iterating by running the program over and over again to capture the new crops with the correct sets

problems
- maxed out equipment lead to a 'substat modification page' instead, which the detail profile does not reliably capture. need to reliably identify the detail page with 2 different crops
- missing unity, rage, revenge, injury, reversal, riposte sets for detail. 22 sets total, have 16.