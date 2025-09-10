from core.osrs_client import RuneLiteClient, ToolplaneTab
from PIL import Image
from core import tools
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
        if not planks_in_inventory():
            get_new_planks()

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

        for _ in range(20):
            propose_break()
            if terminate: break
            sleep(abs(random.normalvariate(.25,.1)))
            if not planks_in_inventory(): 
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
                        
            sleep(abs(random.normalvariate(.5,.1)))
            if not planks_in_inventory():
                use_plank_sack("Empty")
            
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
            #client.click(match)
            keyboard.press('2')
            sleep(.1)
    except ValueError as e:
        # should say confidence wasnt high enough i think
        print(e)
        print('couldnt build. removing instead')
        try:
            while client.is_moving(): continue
            keyboard.press('1')
            # chat_text_clicker(
            #     'Yes',
            #     'Waiting for larder'
            # )
        except Exception as e:
            print(e)
            print('couldnt click yes either. rip')


def get_new_planks():
    print("getting the first set of planks")
    unnote_planks()
    print("filling the plank sack")
    use_plank_sack("Fill")
    print("getting the second set of planks")
    unnote_planks()


def unnote_planks(recurse=0):
    if recurse >= 5:
        raise ValueError('WTF Phails??')
    done = False
    for _ in range(4):
        # seems overkill but im getting weird behavior
        if planks_in_inventory():
            return
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
            
        except:
            print('phials match miss')
            # unselect plank
            client.click_toolplane(ToolplaneTab.SKILLS)
            client.move_off_window()
            time.sleep(random.normalvariate(2,.5))
            
            continue
        while client.is_moving(): continue
        keyboard.press('3')
        done = True
        break
    if not done:
        raise RuntimeError('Phials evaded us :(')
    time.sleep(random.normalvariate(1,.1))
    if not planks_in_inventory():
        print('Apparently i didnt get planks :(')
        unnote_planks(recurse+1)

def use_plank_sack(action):
    if action == "Fill":
        try:
            print("filling sack")
            client.click_item(
                PLANK_SACK,
                crop=(0,13,0,0), # crop top off plank sack (count)
                min_confidence=.90
            )
        except:
            print("couldn't find plank sack to fill")
    elif action == "Empty": 
        try:
            print("emptying sack")
            keyboard.press('shift')
            client.click_item(
                PLANK_SACK,
                crop=(0,13,0,0), # crop top off plank sack (count)
                min_confidence=.90
            )
            keyboard.release('shift')
        except:
            keyboard.release('shift') #because we pressed it at the start and then it failed before it got released
    if keyboard.is_pressed('shift'): keyboard.release('shift')
    time.sleep(random.normalvariate(.5,.05)) # wait for plank update
    return

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
    
def get_plank_count() -> int:
    matches = client.get_inv_items([PLANKS], min_confidence=.95)
    return len(matches)

def propose_break():
    if random.random() < SLEEP_CHANCE:
        t = random.randint(*SLEEP_RANGE)
        print(f'sleeping for {tools.seconds_to_hms(t)}')
        client.move_off_window()
        time.sleep(t)

def sleep(base_time):
    mult = random.uniform(1.0,1.3)
    time.sleep(base_time*mult)
    
def planks_in_inventory() -> bool:
    time.sleep(.25)
    try:
        cnt = get_plank_count()
        print(f'{cnt} planks in inventory')
        return cnt >= PLANK_BUILD_MIN
    except:
        print("not enough planks found in inventory")
        return False
    
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