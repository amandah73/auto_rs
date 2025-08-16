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

        client.smart_click_tile(
            PORTAL_TILE,
            'Build'
        )
    
        propose_break()
        while client.is_moving(): continue

        for _ in range(10): #doing more than 6 bc if it fails then it doesnt use the planks so do it again
            if not planks_in_inventory():
                print("emptying plank sack")
                use_plank_sack("Empty")
                print("looking for planks after emptying")
                if not planks_in_inventory(): # if the sack was already empty
                    print ("no planks in sack or inv")
                    break
            propose_break()
            if terminate: break
            sleep(random.normalvariate(1,.1))
            try:
                print('trying to remove larder')
                client.smart_click_tile(
                    LARDER_TILE,
                    'Remove'
                )
                if terminate: break
                while client.is_moving(): continue
                chat_text_clicker(
                    'Yes',
                    'Waiting for larder'
                )
            except: print('larder already missing? aight')
            time.sleep(random.normalvariate(1,.1))

            
            try:
                print('trying to build larder')
                client.smart_click_tile(
                    LARDER_TILE,
                    'Build'
                )
                while client.is_moving(): continue
            except Exception as e:
                print(e)
                print('couldnt find build button, lets assume it got pressed')

            time.sleep(random.normalvariate(1,.1))
            match = None
            for _ in range(3):
                if terminate: break
                try:
                    match = client.find_in_window(
                        OAK_LARDER,
                        min_confidence=.98
                    )
                    break
                except Exception as e:
                    print(e)
                    print('missed oak larder build btn')

            if match:
                client.click(match)
            sleep(.4)
            
        propose_break()
        sleep(2)
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
            time.sleep(random.normalvariate(3,.5))
            
            continue
        while client.is_moving(): continue
        try:
            if terminate: break
            chat_text_clicker(
                'Exchange All: 120 coins', 
                'Waiting for Phials',
                tries=4
            )
            done = True
            break
        except Exception as e: 
            print(e)
            print('Phials is an elusive boi')
    if not done:
        raise RuntimeError('Phials evaded us :(')
    time.sleep(random.normalvariate(1,.1))
    if not planks_in_inventory():
        print('Apparently i didnt get planks :(')
        unnote_planks(recurse+1)

def use_plank_sack(action):
    if action == "Fill":
        try:
            client.click_item(
                PLANK_SACK,
                crop=(0,13,0,0), # crop top off plank sack (count)
                min_confidence=.90
            )
        except:
            print("couldn't find plank sack to fill")
    elif action == "Empty": 
        try:
            print("pressing shift to empty sack")
            keyboard.press('shift')
            client.click_item(
                PLANK_SACK,
                crop=(0,13,0,0), # crop top off plank sack (count)
                min_confidence=.90
            )
            print("releasing shift")
            keyboard.release('shift')
        except:
            print("couldn't find plank sack to empty. releasing shift")
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
        print("no planks found in inventory")
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