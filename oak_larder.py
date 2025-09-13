from core.osrs_client import RuneLiteClient, ToolplaneTab
from core.minigames.plank_sack_reader import plank_sack_cnt
from PIL import Image
from core import tools, cv_debug
import time
import random
import threading
import keyboard

# a better version of mikey's mahogany tables

client = RuneLiteClient('')
PLANKS = 8778
PLANKS_NOTE = 8779 # oak plank (noted)
PLANK_SACK = 25629 
PHIALS_TILE = (0,255,255) 
PORTAL_TILE = (255,55,255)
LARDER_TILE = (255,55,100)
OAK_LARDER = Image.open('data/ui/oak-larder-build.png')
PLANK_BUILD_MIN = 8
SLEEP_CHANCE = .01 #actually higher b/c this is referenced multiple times
SLEEP_RANGE = (25,122)
MAX_TIME_MIN = random.normalvariate(180, 30) 
terminate = False
cv_debug.enable()

"""
Plugins: [ 'Better NPC Highlight', 'Ground Markers' ]
Setup:
 right click map icon, import tiles:
  [
	{"regionId":7513,"regionX":3,"regionY":11,"z":0,"color":"#FFFF37FF"},
	{"regionId":7513,"regionX":36,"regionY":60,"z":0,"color":"#FFFF3764"},
	{"regionId":11826,"regionX":8,"regionY":24,"z":0,"color":"#FFFF37FF"}
  ]
 NPC highlight: 
  NPC Highlight > Tile > Tile Names > "Phials"

exactly 4 slots of inv should be not unnoted planks (saw, gold, notes, plank sack)
and the plank sack should start either empty or with 24 oak logs in it
and imcando hammer in hand (and carpenters outfit)

also left click of home should be set to build mode, 
same with left click of larder space,
and left click of actual larder should be remove
"""

def main():
    start_time = time.time()
    init()

    while not terminate:
        timeout_check(start_time)
        unnoted_planks = len(client.get_inv_items([PLANKS], min_confidence=.95))
        if unnoted_planks < 20:
            unnote_planks()

        try:
            client.smart_click_tile(
                PORTAL_TILE,
                'Build'
            )
        except:
            print('dont use an item on the portal, silly')
            client.click_toolplane(ToolplaneTab.SKILLS)
            client.click_toolplane(ToolplaneTab.INVENTORY)
            client.smart_click_tile(
                PORTAL_TILE,
                'Build'
            )
    
        propose_break()
        while client.is_moving(): continue
        sleep(abs(random.normalvariate(.75,.1)))

        for _ in range(20):
            propose_break()
            if terminate: break
            sleep(abs(random.normalvariate(.25,.1)))
            total_planks = get_total_plank_count()
            if total_planks < PLANK_BUILD_MIN: 
                break

            try:
                print('trying to build or remove larder')
                client.smart_click_tile(
                    LARDER_TILE,
                    'Larder'
                )
                build_or_remove_larder()
            except: 
                print('couldnt find larder space at all. maybe build options are blocking?')
                try: build_or_remove_larder()
                except: print('lmao guess not')
            
        propose_break()
        sleep(abs(random.normalvariate(.25,.1)))
        try:
            client.smart_click_tile(
                PORTAL_TILE,
                'Enter'
            )
        except:
            print('dont use an item on the portal, silly')
            client.click_toolplane(ToolplaneTab.SKILLS)
            client.click_toolplane(ToolplaneTab.INVENTORY)
            client.smart_click_tile(
                PORTAL_TILE,
                'Enter'
            )
        while client.is_moving(): continue
        sleep(abs(random.normalvariate(.5,.1)))
    total_time = tools.seconds_to_hms(time.time() - start_time)
    print(f'Grinded for {total_time}')
    
def build_or_remove_larder():
    if terminate: return
    while client.is_moving(): continue
    # assuming building first
    time.sleep(abs(random.normalvariate(.25,.1)))
    match = None
    print('trying to build rq')
    try:
        match = client.find_in_window(
            OAK_LARDER,
            min_confidence=.95
        )
        if match:
            keyboard.press('2')
            sleep(.1)
    except ValueError as e:
        print(e)
        print('couldnt build. removing instead')
        while client.is_moving(): continue
        keyboard.press('1')

def unnote_planks(recurse=0):
    if recurse >= 5:
        raise ValueError('WTF Phails??')
    total_planks = get_total_plank_count()
    if total_planks > 40:
        return
    success = False
    for _ in range(4):
        if terminate: break
        try:
            client.click_item(
                PLANKS_NOTE,
                crop=(0,16,0,0), # crop top off planks (count)
                min_confidence=.90
            )
        except Exception as e:
            print(e)
            print('wheres the noted planks')
            client.click_toolplane(ToolplaneTab.SKILLS)
            client.move_off_window()
            time.sleep(random.normalvariate(3,.5))
            continue
        
        if terminate: break
        try:
            client.smart_click_tile(
                PHIALS_TILE,
                ['Phials', 'Pvals'], #sometimes it's hard to read his name
                retry_hover=2,
                retry_match=10
            )
            while client.is_moving(): continue
            keyboard.press('3')
            planks_in_sack = plank_sack_cnt(client.get_screenshot())
            if planks_in_sack == 0:
                client.click_item(
                    PLANK_SACK,
                    crop=(0,13,0,0), # crop top off plank sack (count)
                    min_confidence=.90
                )
            success = True
            break
        except:
            print('phials match miss')
            # unselect plank
            client.click_toolplane(ToolplaneTab.SKILLS)
            client.move_off_window()
            time.sleep(random.normalvariate(2,.5))
            continue
    time.sleep(random.normalvariate(1,.1))
    if success: unnote_planks(0)
    else: unnote_planks(recurse+1)

def chat_text_clicker(text,wait_msg,wait=.5,tries=8):
    done = False
    for _ in range(tries):
        if terminate: break
        try:
            time.sleep(wait)
            client.click_chat_text(text)
            done = True
            break
        except Exception as e:
            print(wait_msg)
    if not done:
        raise RuntimeError(f'Could not find chat text {text}')
    
def get_total_plank_count() -> int:
    sleep(.1)
    unnoted = len(client.get_inv_items([PLANKS], min_confidence=.95))
    print(f'{unnoted} unnoted planks')
    planks_in_sack = plank_sack_cnt(client.get_screenshot())
    print(f'{planks_in_sack} planks in sack')
    total = unnoted + planks_in_sack
    print(f'{total} total planks')
    return total

def propose_break():
    if random.random() < SLEEP_CHANCE:
        t = random.randint(*SLEEP_RANGE)
        print(f'sleeping for {tools.seconds_to_hms(t)}')
        client.move_off_window()
        time.sleep(t)

def sleep(base_time):
    mult = random.uniform(1.0,1.3)
    time.sleep(base_time*mult)
    
def timeout_check(start):
    runtime = time.time() - start
    if runtime/60 > MAX_TIME_MIN:
        raise RuntimeError('MAX TIME LIMIT EXCEEDED')

def init():
    print(f'initializing bot {__file__}')
    threading.Thread(target=listen_for_escape, daemon=True).start()


def listen_for_escape():
    """Thread function to listen for the Esc key."""
    global terminate
    while True:
        if keyboard.is_pressed('esc'):
            print("Terminating...")
            terminate = True
            return
        if keyboard.is_pressed('`'):
            client.debug_sectors().show()
        time.sleep(0.1)
try:
    main()
except Exception as e:
    print(f'CRITICAL ERROR {e}')
    client.debug_sectors().show()