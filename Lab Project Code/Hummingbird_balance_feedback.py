#  ###NOTE: SEE EEG TRIGGER VALUES AT THE END OF THIS FILE
# ### IMPORT LIBRARIES AND FUNCTIONS FOR STIMULI, EYE TRACKING, AND EEG
from __future__ import absolute_import, division

from psychopy import prefs
from psychopy import locale_setup
from psychopy import gui, visual, core, data, event, logging, clock
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED,
                                STOPPED, FINISHED, PRESSED, RELEASED, FOREVER)


import numpy as np  # whole numpy lib is available, prepend 'np.'
from numpy import (sin, cos, tan, pi, average,
                   sqrt, std, deg2rad, rad2deg, linspace, asarray)
from numpy.random import random, randint, normal, shuffle
import math
from math import log
import os  # handy system and path functions
import sys  # to get file system encoding

from psychopy.hardware import keyboard
import time, shutil

import pylink 

from psychopy import core, event, visual, gui, monitors, parallel 
from psychopy import data
from string import ascii_letters, digits 
from EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy

from psychopy.hardware import keyboard

import random
import csv


# ### DIALOGUE WINDOW AT THE BEGINNING OF EXPERIMENT

# NOTE: Don't forget to remove the native dialogue window in the CODER MODE

# Ensure that relative paths start from the same directory as this script
_thisDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(_thisDir)

# Store info about the experiment session
psychopyVersion = '3.2.4'
expName = 'SWAN4b' # from the Builder filename that created this script
expInfo = {'participant': '', 'session': '001'}
#dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False, title=expName)
#if dlg.OK == False:
#    core.quit()  # user pressed cancel
expDate = data.getDateStr()  # add a simple timestamp
#expInfo['expName'] = expName
#expInfo['psychopyVersion'] = psychopyVersion

#THIS IS NEEDED FOR the VALID NAME (see below) 
gui_title = 'Enter Participant Basic Data'
gui_prompt = 'Subject ID should have 8 or fewer characters\n' + \
             '[letters, numbers, and underscore].'

# LOOP FOR VALID NAME
while True:
    dlg_obj = gui.Dlg(gui_title)
    gui = dlg_obj
    gui.addField('Subject ID:')
    gui.addText(gui_prompt)
    gui.addField('Age:')
    gui.addField('Gender:')
    gui.addField('Handedness:')
    gui.addField('Sequence (1/2/3/4):')
    gui.addField('balancevar (1/2):') #Variable to balance blocks between block sets (so that all long blocks never fall into one set of blocks)
    # show dialog and wait for OK or Cancel
    ok_data = gui.show()
    print(gui.data)
    # get the string entered by the experimenter
    tmp_str = gui.data[0]
    # strip trailing characters, ignore the ".edf" extension
    edf_fname = tmp_str.rstrip().split('.')[0]

    # check if the filename is valid (length <= 8 & no special char)
    allowed_char = ascii_letters + digits + '_'
    if not all([c in allowed_char for c in edf_fname]):
        print('ERROR: Invalid Subject ID')
    elif len(edf_fname) > 8:
        print('ERROR: Subject ID should not exceed 8 characters')
    else:
        break


# Data file name stem = absolute path + name; later add .psyexp, .csv, .log, etc
filename = _thisDir + os.sep + u'data/%s_%s_%s' % (gui.data[0], expName, expDate)  

#add at the beginning to check that the condition sequence number is 1 or 2 (after GUI settings)
if (gui.data[4] in ['1','2','3','4']):
    seqcheck='OK' 
seqcheck_pass=seqcheck #will stop experiment if invalid window value in the list of sequences


# ### EYE-TRACKING ####
# Set up a folder to store the EDF data files and the associated resources
# e.g., files defining the interest areas used in each trial
results_folder = 'ET_data'
if not os.path.exists(results_folder):
    os.makedirs(results_folder)

# We download EDF data file from the EyeLink Host PC to the local hard
# drive at the end of each testing session, here we rename the EDF to
# include session start date/time
time_str = time.strftime("_%Y_%m_%d_%H_%M", time.localtime())
session_identifier = edf_fname + time_str

# create a folder for the current testing session in the "ET_data" folder
session_folder = os.path.join(results_folder, session_identifier)
if not os.path.exists(session_folder):
    os.makedirs(session_folder)

# Connect to the EyeLink Host PC
el_tracker = pylink.EyeLink("100.1.1.1")

# Open an EDF data file on the Host PC
edf_file = edf_fname + ".EDF"

el_tracker.openDataFile(edf_file)
# Add a header text to the EDF file to identify the current experiment name
# This is OPTIONAL. If your text starts with "RECORDED BY " it will be
# available in DataViewer's Inspector window by clicking
# the EDF session node in the top panel and looking for the "Recorded By:"
# field in the bottom panel of the Inspector.
preamble_text = 'RECORDED BY %s' % os.path.basename(__file__)
el_tracker.sendCommand("add_file_preamble_text '%s'" % preamble_text)


# CONFIGURE THE EYETRACKER
# Put the tracker in offline mode before we change tracking parameters
el_tracker.setOfflineMode()

# Get the software version:  1-EyeLink I, 2-EyeLink II, 3/4-EyeLink 1000,
# 5-EyeLink 1000 Plus, 6-Portable DUO
vstr = el_tracker.getTrackerVersionString()
eyelink_ver = int(vstr.split()[-1].split('.')[0])

# File and Link data control
# what eye events to save in the EDF file, include everything by default
file_event_flags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT'
# what eye events to make available over the link, include everything by default
link_event_flags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,BUTTON,FIXUPDATE,INPUT'
# what sample data to save in the EDF data file and to make available
# over the link
# I ASSUME THE VERSION IS HIGHER THAN #3
file_sample_flags = 'LEFT,RIGHT,GAZE,HREF,RAW,AREA,HTARGET,GAZERES,BUTTON,STATUS,INPUT'
link_sample_flags = 'LEFT,RIGHT,GAZE,GAZERES,AREA,HTARGET,STATUS,INPUT'

el_tracker.sendCommand("file_event_filter = %s" % file_event_flags)
el_tracker.sendCommand("file_sample_data = %s" % file_sample_flags)
el_tracker.sendCommand("link_event_filter = %s" % link_event_flags)
el_tracker.sendCommand("link_sample_data = %s" % link_sample_flags)

# Optional tracking parameters
# Sample rate, 250, 500, 1000, or 2000, check your tracker specification
el_tracker.sendCommand("sample_rate 500")
# Choose a calibration type, H3, HV3, HV5, HV13 (HV = horizontal/vertical),
el_tracker.sendCommand("calibration_type = HV5")
# Set a gamepad button to accept calibration/drift check target
# You need a supported gamepad/button box that is connected to the Host PC
el_tracker.sendCommand("button_function 5 'accept_target_fixation'")


# Setup the Window
win = visual.Window(
    size=[1920, 1080], fullscr=True, screen=0, 
    winType='pyglet', allowGUI=False, allowStencil=False,
    monitor='testMonitor', color=[0.1,0.1,0.1], colorSpace='rgb',
    blendMode='avg', useFBO=True, 
    units='pix')
# store frame rate of monitor if we can measure it
expInfo['frameRate'] = win.getActualFrameRate()
if expInfo['frameRate'] != None:
    frameDur = 1.0 / round(expInfo['frameRate'])
else:
    frameDur = 1.0 / 60.0  # could not measure, so guess

# create a default keyboard (e.g. to check for escape)
defaultKeyboard = keyboard.Keyboard()

# Initialize components for Routine "ExpSettings"
ExpSettingsClock = core.Clock()

# Set up a graphics environment for calibration
# Open a window, be sure to specify monitor parameters
mon = monitors.Monitor('myMonitor', width=53.0, distance=75.0)


# get the native screen resolution used by PsychoPy
scn_width, scn_height = win.size

# Pass the display pixel coordinates (left, top, right, bottom) to the tracker
# see the EyeLink Installation Guide, "Customizing Screen Settings"
el_coords = "screen_pixel_coords = 0 0 %d %d" % (scn_width - 1, scn_height - 1)
el_tracker.sendCommand(el_coords)

# Write a DISPLAY_COORDS message to the EDF file
# Data Viewer needs this piece of info for proper visualization, see Data
# Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
dv_coords = "DISPLAY_COORDS  0 0 %d %d" % (scn_width - 1, scn_height - 1)
el_tracker.sendMessage(dv_coords)

# Configure a graphics environment (genv) for tracker calibration
genv = EyeLinkCoreGraphicsPsychoPy(el_tracker, win)
genv.setCalibrationSounds('off', 'off', 'off')
print(genv)  # print out the version number of the CoreGraphics library

# Set background and foreground colors for the calibration target
# in PsychoPy, (-1, -1, -1)=black, (1, 1, 1)=white, (0, 0, 0)=mid-gray
foreground_color = (-1, -1, -1)
background_color = win.color
genv.setCalibrationColors(foreground_color, background_color)

# Set up the calibration target
genv.setTargetType('circle')

# Request Pylink to use the PsychoPy window we opened above for calibration
pylink.openGraphicsEx(genv)

# CALIBRATE THE TRACKER
el_tracker.doTrackerSetup()

# put tracker in idle/offline mode before recording
el_tracker.setOfflineMode()

# START RECORDING
# arguments: sample_to_file, events_to_file, sample_over_link, # event_over_link (1-yes, 0-no)
#el_tracker.startRecording(1, 1, 1, 1)


# terminate recording function
def terminate_recording():
    """ Terminate the task and retrieve the EDF data file

    file_to_retrieve: The EDF on the Host that we would like to download
    win: the current window used by the experimental script
    """

    el_tracker = pylink.getEYELINK()

    # Put tracker in Offline mode
    el_tracker.setOfflineMode()

    # Clear the Host PC screen and wait for 500 ms
    el_tracker.sendCommand('clear_screen 0')
    pylink.msecDelay(500)

    # Close the edf data file on the Host
    el_tracker.closeDataFile()

    # Download the EDF data file from the Host PC to a local data folder
    # parameters: source_file_on_the_host, destination_file_on_local_drive
    local_edf = os.path.join(session_folder, session_identifier + '.EDF')
    el_tracker.receiveDataFile(edf_file, local_edf)

    # Close the link to the tracker.
    el_tracker.close()


# ####### setting the parallel port addres for EEG triggers
parallel.setPortAddress(16376)


# An ExperimentHandler isn't essential but helps with data saving
thisExp = data.ExperimentHandler(name=expName, version='',
    extraInfo=expInfo, runtimeInfo=None,
    originPath="C:\\Users\\Eds Lab\\Desktop\\Zixu\\",
    savePickle=True, saveWideText=True,
    dataFileName=filename)
# save a log file for detail verbose info
logFile = logging.LogFile(filename+'.log', level=logging.EXP)
logging.console.setLevel(logging.WARNING)  # this outputs to the screen, not a file

endExpNow = False  # flag for 'escape' or other condition => quit the exp
frameTolerance = 0.001  # how close to onset before 'same' frame





# ####### BEHAVIORAL EXPERIMENT STARTS HERE ###########
# ### EXPERIMENT SETTINGS
setsizes=[20,20] #always should be multiple of 2
blocks_per_cond=[15,3]

nPracticeblocks=2 # maximum number of practice blocks before each main session type

durations=[1,0.2,0.4,0.816,0.816,4] #ITI (study stage), prefixation (test stage), fixation duration, study item duration, test item before response window, test max response window
imagesize=306 # image size in pixels
boxsize=(340,340) #color box size in the 2-AFC
pos_shift=200 # horizontal shift of testing options
blanksize=(400,70) #common blank screen size for 2-AFC test
color_val = [[0,-1,-1],[-1,-1,0]] # Python RGB values for colors RED and BLUE used for color boxes at the test phase



# SIMPLE BALANCING CHANGE 1: four main sessions, eight 20-image blocks each.
bsets = [[20] * 8 for _ in range(4)]


# ## Convert stimulus durations from seconds to frames
framesec=120 #expInfo['frameRate'] #frame duration in seconds
#framecount=[0]*len(durations) #create an empty list (fill with 0) for the frame count variable
#for i in range(len(durations)): #for each item in the list of durations...
#    framecount[i]=int(durations[i]*framesec) #convert time to integer framecount
#NOTE: Use "framecount" as time variable throughout the experiment!!!
framecount=[120, 24, 48, 97, 97, 480]

# Time durations in frames
ITI=120 # 1000ms
fixtime=[120,60] #1000ms for the first trial in a block, 500ms for the rest
studytime=98 #800ms (+16 ms to make sure dropped frames don't make it too short)
testtime=98 #800ms (+16 ms to make sure dropped frames don't make it too short)
respwait=480 #4000ms 


#CONDITION SETTINGS FOR THE EXP DEPENDING ON HAND CHOICE FOR RESPONSES
if (gui.data[4] in ['1','3']):
    conditions=['find_Old','find_Old','find_Old','find_Old','find_Old','find_Old','find_Old','find_Old']
    conditions_c = ['find_Indoor', 'find_Indoor', 'find_Outdoor', 'find_Outdoor', 'find_Outdoor', 'find_Outdoor', 'find_Indoor', 'find_Indoor']
if (gui.data[4] in ['2','4']):
    conditions=['find_Old','find_Old','find_Old','find_Old','find_Old','find_Old','find_Old','find_Old']
    conditions_c = ['find_Outdoor', 'find_Outdoor', 'find_Indoor', 'find_Indoor', 'find_Indoor', 'find_Indoor', 'find_Outdoor', 'find_Outdoor']
if (gui.data[4] in ['1','2']):
    handtext=['RIGHT','RIGHT','RIGHT','RIGHT','LEFT','LEFT','LEFT','LEFT']
if (gui.data[4] in ['3','4']):
    handtext=['LEFT','LEFT','LEFT','LEFT','RIGHT','RIGHT','RIGHT','RIGHT']

# Each session's length
blocks_per_session=[nPracticeblocks,len(bsets[0]),nPracticeblocks,len(bsets[1]),nPracticeblocks,len(bsets[2]),nPracticeblocks,len(bsets[3])]
# session type alternation
sessions=['practice','main','practice','main','practice','main','practice','main']

buttons=['h','j']

# Load and randomize stimuli
# path='C:\\Users\\Awh Vogel Lab\\Desktop\\IgorUtochkin\\MemSearch\\OBJECTSALL\\' #general path
# path_prac='C:\\Users\\Awh Vogel Lab\\Desktop\\IgorUtochkin\\MemSearch\\Obj_BOSS_Konkle\\' #path to additional stimuli for practice blocks

path = "C:\\Users\\Eds Lab\\Desktop\\Zixu\\OBJECTSALL\\"
path1 = "C:\\Users\\Eds Lab\\Desktop\\Zixu\\Random_2200_Images\\indoor_merged_1000\\"
path2 = "C:\\Users\\Eds Lab\\Desktop\\Zixu\\Random_2200_Images\\outdoor_merged_1000\\"
path_prac1 = "C:\\Users\\Eds Lab\\Desktop\\Zixu\\Random_720_Images\\indoor\\"
path_prac2 = "C:\\Users\\Eds Lab\\Desktop\\Zixu\\Random_720_Images\\outdoor\\"

# SIMPLE BALANCING CHANGE 2: participant-specific order of the main images.
# Keep each block's 30 images in the ORIGINAL order expected by this script:
# first 10 old, next 10 recognition-new, final 10 categorization-new.
# Images within each of those three sets are balanced over score thirds.
SCORES_CSV = os.path.join(_thisDir, 'memorability_scores.csv')
with open(SCORES_CSV, newline='', encoding='utf-8-sig') as f:
    score_rows = list(csv.DictReader(f))


def balance_main_images(folder, folder_label):
    rng = random.Random(str(gui.data[0]) + '_' + folder_label)
    available = set(os.listdir(folder))
    scores = {r['filename']: r for r in score_rows if r['Folder'] == folder_label}
    names = [name for name in scores if name in available]
    if len(names) < 960:
        raise ValueError('Need at least 960 scored ' + folder_label + ' images; found ' + str(len(names)))

    # Randomize assignment to old / recognition foil / categorization foil FIRST.
    # This avoids systematically selecting high or low scores for a particular role.
    rng.shuffle(names)
    old, recognition_new, categorization_new = (
        names[:320], names[320:640], names[640:960]
    )

    def spread_across_blocks(files, score_column):
        ordered = sorted(files, key=lambda name: float(scores[name][score_column]))
        thirds = [ordered[:107], ordered[107:214], ordered[214:]]
        for third in thirds:
            rng.shuffle(third)
        blocks = []
        for block in range(32):
            counts = [3, 3, 3]
            counts[block % 3] += 1  # 3/3/4, rotating the extra image
            selected = []
            for third, count in zip(thirds, counts):
                selected.extend(third.pop() for _ in range(count))
            rng.shuffle(selected)
            blocks.append(selected)
        return blocks

    old_blocks = spread_across_blocks(old, 'ResMem_Score')
    rec_blocks = spread_across_blocks(recognition_new, 'FalseResMem_Score')
    cat_blocks = spread_across_blocks(categorization_new, 'FalseResMem_Score')
    return [name for block in range(32)
            for name in old_blocks[block] + rec_blocks[block] + cat_blocks[block]]


allimages1 = balance_main_images(path1, 'Indoor_Set')
allimages2 = balance_main_images(path2, 'Outdoor_Set')
images_prac1 = os.listdir(path_prac1)
images_prac2 = os.listdir(path_prac2)


#Mix files one more time, this time in the new pathallimages=os.listdir(path) # massive memory stimulus set from Brady et al (2008)
# for i in ['BlueCue.jpg','blank.jpg','fixationpoint.png','fixationpoint_sm.png','RedCue.jpg','questionmark.png']:
    # allimages.remove(i) #exclude the blank screen and fixation point from the image list
# Double the list of practice pictures to reuse it in case many practice blocks are required
npool1 = (len(images_prac1) // 30) * 30   # 123 -> 120
npool2 = (len(images_prac2) // 30) * 30   # 288 -> 270
img_prac1 = random.sample(images_prac1, npool1) + random.sample(images_prac1, npool1)
img_prac2 = random.sample(images_prac2, npool2) + random.sample(images_prac2, npool2)
# stop early with a clear message instead of crashing mid-experiment
if nPracticeblocks * 4 > min(len(img_prac1), len(img_prac2)) // 30:
    raise ValueError('Not enough practice images for ' + str(nPracticeblocks * 4) + ' practice blocks')

#create path to the file to record the information about stimulus randomization:
path_inddat='C:\\Users\\Eds Lab\\Desktop\\Zixu\\'+gui.data[0]+'_stiminfo\\'
#create a folder
if os.path.exists(path_inddat)==False: #create stimdata folder if it doesn't exist
    os.mkdir(path_inddat)
    

#create file name to save stimulus data
#create file name to save stimulus data
file_wholeseq=path_inddat+gui.data[0]+'_allstim.csv' #all randomized images
file_currentseq=path_inddat+gui.data[0]+'_SWAN2_4_stim.csv' #image sequence for practice

# SIMPLE BALANCING CHANGE 3: save a copy of the full main-image assignment.
with open(file_wholeseq, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['block', 'scene', 'role', 'filename', 'ResMem', 'FalseResMem'])
    for block in range(32):
        for scene, names, label in [('indoor', allimages1, 'Indoor_Set'),
                                    ('outdoor', allimages2, 'Outdoor_Set')]:
            lookup = {r['filename']: r for r in score_rows if r['Folder'] == label}
            for slot, name in enumerate(names[block * 30:(block + 1) * 30]):
                role = ('old' if slot < 10 else
                        'recognition_new' if slot < 20 else 'categorization_new')
                row = lookup[name]
                writer.writerow([block + 1, scene, role, name,
                                 row['ResMem_Score'], row['FalseResMem_Score']])


# Variable texts to change response hands
# ##for initial instruction
t00='This experiment aims to study brain activity when people memorize and retrieve images of places. The experiment will consist of a number of blocks.\n\nEach block consists of three stages. The first stage is memorization. You will be sequentially shown a set of images of places that you have to memorize. The second stage will be a recognition test that will start in a few seconds after memorization. You will be shown another set of images of places. In every trial, you will see two images at a time. One of these two images is always a place from the memorized set (OLD) and another is NEW. Your task is to answer where the old place image is by pressing one of the response buttons. You can answer when a question mark (?) appears at the center of the screen. After each recognition trial, you will receive feedback on whether your answer was correct or incorrect. The correct OLD image will remain visible in its original position during feedback, regardless of your answer. The third stage will be a categorization test that will start in a few seconds after the recognition test. You will be shown a set of images of places. In every trial, you will see two images at a time. Your task is to answer where the indoor or outdoor place image is by pressing one of the response buttons. You can answer when a question mark (?) appears at the center of the screen.\nPress H to select the LEFT image and J to select the RIGHT image.\n\nBe aware that place images from any of the previous blocks will be never tested in a current block.\nWe also ask you to respond as accurately as possible and only when the question mark appears.\n\nAt the beginning of each trial, a black fixation cross will appear. Fixate your gaze on the small dot at the very center of that cross and try not to move your eyes or blink until it disappears. When the cross changes to the question mark in the test trials and categorization trials please keep your eyes on it before you press a response button. You can move your eyes and blink between trials and during breaks between blocks and stages.\n\nPress SPACE to continue'
t01 = (
    'Memory test will start right now\n\n'
    'Answer where the {} image is\n\n'
    'Answer with your {} hand\n\n'
    'After each trial, the correct OLD image will be shown '
    'in its original position, along with feedback indicating '
    'whether your answer was correct or incorrect.\n\n'
    'Please keep your eyes fixated at the center of the screen.'
)
t02 = 'Categorization test will start right now \n\nAnswer which image is {}\n\nAnswer with your {} hand'

#Generate absolute number counter for trials, including practice sessionType
absnum=0
# Counter for recordable epoch number (total counter of main trials)
epochnum=0
#Add cumulative recognition and categorization phase trial number and accuracy
recognition_correct = 0
recognition_trials = 0
categorization_correct = 0
categorization_trials = 0

InstrExp = visual.TextStim(win=win, name='InstrExp',
    text= t00, #substitute button names in text 't00'
    font='Arial',
    units='pix', pos=(0, 0), height=20, wrapWidth=1000, ori=0, 
    color='black', colorSpace='rgb', opacity=1, 
    languageStyle='LTR',
    depth=-4.0);
ExpStart = keyboard.Keyboard()

# Initialize components for Routine "StartRecording"
StartRecordingClock = core.Clock()
ReminderMessage = visual.TextStim(win=win, name='ReminderMessage',
    text='Experimenter: Make sure you started recording!!!',
    font='Arial',
    units='pix', pos=(0, -250), height=30, wrapWidth=800, ori=0, 
    color='red', colorSpace='rgb', opacity=1, 
    languageStyle='LTR',
    depth=-1.0);
RecConfirm = keyboard.Keyboard()

# Initialize components for Routine "StartStudy"
StartStudyClock = core.Clock()
StudyInstr = visual.TextStim(win=win, name='StudyInstr',
    text='default text',
    font='Arial',
    units='pix', pos=(0, 0), height=20, wrapWidth=800, ori=0, 
    color='black', colorSpace='rgb', opacity=1, 
    languageStyle='LTR',
    depth=-1.0);
GotoStudy = keyboard.Keyboard()

# Initialize components for Routine "StudyPhase"
StudyPhaseClock = core.Clock()
StudyImage = visual.ImageStim(
    win=win,
    name='StudyImage', units='pix', 
    image='sin', mask=None,
    ori=0, pos=(0, 0), size=1.0,
    color=[1,1,1], colorSpace='rgb', opacity=1,
    flipHoriz=False, flipVert=False,
    texRes=128, interpolate=True, depth=-1.0)
FixImage1 = visual.ImageStim(
    win=win,
    name='FixImage1', units='pix', 
    image='sin', mask=None,
    ori=0, pos=(0, 0), size=36.0,
    color=[1,1,1], colorSpace='rgb', opacity=1,
    flipHoriz=False, flipVert=False,
    texRes=128, interpolate=True, depth=-1.0)
stimtrak1 = visual.Polygon(
    win=win, name='stimtrak1',units='pix', 
    edges=90, size=(20,20),
    ori=0, pos=(930, 510),
    lineWidth=1, lineColor=[1,1,1], lineColorSpace='rgb',
    fillColor=[1,1,1], fillColorSpace='rgb',
    opacity=1, depth=-3.0, interpolate=True)

# Initialize components for Routine "StartTest"
StartTestClock = core.Clock()
TestInstruction = visual.TextStim(win=win, name='TestInstruction',
    text='The memorization stage is finished',
    font='Arial',
    units='pix', pos=(0, 150), height=20, wrapWidth=800, ori=0, 
    color='black', colorSpace='rgb', opacity=1, 
    languageStyle='LTR', 
    depth=-1.0);
TestInstr_Add = visual.TextStim(win=win, name='TestInstr_Add',
    text=t01, #substitute target type in text 't01'
    font='Arial',
    pos=(0, 0), height=20, wrapWidth=800, ori=0, 
    color='black', colorSpace='rgb', opacity=1, 
    languageStyle='LTR',
    depth=-2.0);

# Initialize components for Routine "TestPhase"
TestPhaseClock = core.Clock()
blankfield=path+'blank.jpg'
Blank_L = visual.ImageStim(
    win=win,
    name='Blank_R', units='pix',
    image=blankfield, mask=None,
    ori=0, pos=(-pos_shift, 0), size=imagesize,
    color=[1,1,1], colorSpace='rgb', opacity=1,
    flipHoriz=False, flipVert=False,
    texRes=128, interpolate=True, depth=-1.0)
Blank_R = visual.ImageStim(
    win=win,
    name='Blank_R', units='pix',
    image=blankfield, mask=None,
    ori=0, pos=(pos_shift, 0), size=imagesize,
    color=[1,1,1], colorSpace='rgb', opacity=1,
    flipHoriz=False, flipVert=False,
    texRes=128, interpolate=True, depth=-1.0)
FixImage2 = visual.ImageStim(
    win=win,
    name='FixImage2', units='pix', 
    image=path+'fixationpoint_sm.png', mask=None,
    ori=0, pos=(0, 0), size=36.0,
    color=[1,1,1], colorSpace='rgb', opacity=1,
    flipHoriz=False, flipVert=False,
    texRes=128, interpolate=True, depth=-1.0)
qmark = visual.ImageStim(
    win=win,
    name='qmark', units='pix', 
    image=path+'questionmark.png', mask=None,
    ori=0, pos=(0, 0), size=36.0,
    color=[1,1,1], colorSpace='rgb', opacity=1,
    flipHoriz=False, flipVert=False,
    texRes=128, interpolate=True, depth=-1.0)
stimtrak2 = visual.Polygon(
    win=win, name='stimtrak2',units='pix', 
    edges=90, size=(20,20),
    ori=0, pos=(930,510),
    lineWidth=1, lineColor='white', lineColorSpace='rgb',
    fillColor='white', fillColorSpace='rgb',
    opacity=1, depth=-4.0, interpolate=True)
Resp = keyboard.Keyboard()

# Initialize components for Routine "NextTrial"
NextTrialClock = core.Clock()
BlankScreen_L = visual.ImageStim(
    win=win,
    name='BlankScreen_L', units='pix', 
    image=path+'blank.jpg', mask=None,
    ori=0, pos=(-pos_shift, 0), size=imagesize,
    color=[1,1,1], colorSpace='rgb', opacity=1,
    flipHoriz=False, flipVert=False,
    texRes=128, interpolate=True, depth=-1.0)
BlankScreen_R = visual.ImageStim(
    win=win,
    name='BlankScreen_R', units='pix', 
    image=path+'blank.jpg', mask=None,
    ori=0, pos=(pos_shift, 0), size=imagesize,
    color=[1,1,1], colorSpace='rgb', opacity=1,
    flipHoriz=False, flipVert=False,
    texRes=128, interpolate=True, depth=-1.0)
fbFrame = visual.ImageStim(
    win=win,
    name='fbFrame', units='pix', 
    image=path+'blank.jpg', mask=None,
    ori=0, pos=(0, 0), size=blanksize,
    color=[0.8,0.8,0.8], colorSpace='rgb', opacity=1,
    flipHoriz=False, flipVert=False,
    texRes=128, interpolate=True, depth=-1.0)
feedback = visual.TextStim(win=win, name='feedback',
    text='default text',
    font='Arial',
    units='pix', pos=(0, 0), height=40, wrapWidth=None, ori=0, 
    color='black', colorSpace='rgb', opacity=1, 
    languageStyle='LTR',
    depth=-2.0);
gotoTrial = keyboard.Keyboard()

# Initialize components for Routine "TechnicalBreak"
TechnicalBreakClock = core.Clock()
blockclear = visual.TextStim(win=win, name='blockclear',
    text='default text',
    font='Arial',
    units='pix', pos=(0, 0), height=20, wrapWidth=None, ori=0, 
    color='white', colorSpace='rgb', opacity=1, 
    languageStyle='LTR',
    depth=-1.0);
AllowContinue = keyboard.Keyboard()

# Initialize components for Routine "switchblock"
switchblockClock = core.Clock()

# Initialize components for Routine "End"
EndClock = core.Clock()
finishExp = visual.TextStim(win=win, name='finishExp',
    text='The experiment is complete. Thank you!\n\nPress SPACE to quit',
    font='Arial',
    units='pix', pos=(0, 0), height=30, wrapWidth=None, ori=0, 
    color='black', colorSpace='rgb', opacity=1, 
    languageStyle='LTR',
    depth=-1.0);
PressToFinish = keyboard.Keyboard()

#initalize components for Routine "StartCategorization"
StartCateClock = core.Clock()
CategorInstruction = visual.TextStim(win=win, name='CategorInstruction',
    text='The Categorization test stage is about to begin',
    font='Arial',
    units='pix', pos=(0, 150), height=20, wrapWidth=800, ori=0, 
    color='black', colorSpace='rgb', opacity=1, 
    languageStyle='LTR', 
    depth=-1.0);
CategorInstr_Add = visual.TextStim(win=win, name='CategorInstr_Add',
    text=t02,
    font='Arial',
    pos=(0, 0), height=20, wrapWidth=800, ori=0, 
    color='black', colorSpace='rgb', opacity=1, 
    languageStyle='LTR',
    depth=-2.0);
    
#initialize components for Routine "CategorizationPhase"
CategorPhaseClock = core.Clock()
stimtrak3 = visual.Polygon(
    win=win, name='stimtrak3',units='pix', 
    edges=90, size=(20,20),
    ori=0, pos=(930,510),
    lineWidth=1, lineColor='white', lineColorSpace='rgb',
    fillColor='white', fillColorSpace='rgb',
    opacity=1, depth=-4.0, interpolate=True)
Resp1 = keyboard.Keyboard()
FixImage3 = visual.ImageStim(
    win=win,
    name='FixImage3', units='pix', 
    image=path+'fixationpoint_sm.png', mask=None,
    ori=0, pos=(0, 0), size=36.0,
    color=[1,1,1], colorSpace='rgb', opacity=1,
    flipHoriz=False, flipVert=False,
    texRes=128, interpolate=True, depth=-1.0)

# Create some handy timers
globalClock = core.Clock()  # to track the time since experiment started
routineTimer = core.CountdownTimer()  # to track time remaining of each (non-slip) routine 

# ------Prepare to start Routine "ExpSettings"-------
win.mouseVisible=False
# update component parameters for each repeat
ExpStart.keys = []
ExpStart.rt = []
# keep track of which components have finished
ExpSettingsComponents = [InstrExp, ExpStart]
for thisComponent in ExpSettingsComponents:
    thisComponent.tStart = None
    thisComponent.tStop = None
    thisComponent.tStartRefresh = None
    thisComponent.tStopRefresh = None
    if hasattr(thisComponent, 'status'):
        thisComponent.status = NOT_STARTED
# reset timers
t = 0
_timeToFirstFrame = win.getFutureFlipTime(clock="now") # timing of the next screen refresh
ExpSettingsClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip; resets the routine clock
frameN = -1
continueRoutine = True

# Set counters for session types (practice or main) and blocks within each session
sessionCount=0
mainsessionCount=-1 # separate counter for main sessions (to switch between sublists of blocks only of main sessions)
session_block_count=0 #count blocks within a session
#Set picture tracking index for main and practice blocks to switch
lastindex=-1
lastindex_prac=-1

i=0 #absolute counter of blocks

# -------Run Routine "ExpSettings"-------

while continueRoutine:
    # get current time
    t = ExpSettingsClock.getTime()
    tThisFlip = win.getFutureFlipTime(clock=ExpSettingsClock)
    tThisFlipGlobal = win.getFutureFlipTime(clock=None) # timing of next screen refresh relative to the global clock
    frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
    # update/draw components on each frame
    
    # *InstrExp* updates
    if InstrExp.status == NOT_STARTED and frameN >= 0.0:
        # keep track of start time/frame for later
        InstrExp.frameNStart = frameN  # exact frame index
        InstrExp.tStart = t  # local t and not account for scr refresh
        InstrExp.tStartRefresh = tThisFlipGlobal  # on global time
        win.timeOnFlip(InstrExp, 'tStartRefresh')  # (update tStartRefresh) time at next scr refresh
        InstrExp.setAutoDraw(True)
    
    # *ExpStart* updates
    waitOnFlip = False
    if ExpStart.status == NOT_STARTED and frameN >= 0.0:
        # keep track of start time/frame for later
        ExpStart.frameNStart = frameN  # exact frame index
        ExpStart.tStart = t  # local t and not account for scr refresh
        ExpStart.tStartRefresh = tThisFlipGlobal  # on global time
        win.timeOnFlip(ExpStart, 'tStartRefresh')  # time at next scr refresh
        ExpStart.status = STARTED
        # keyboard checking is just starting
        waitOnFlip = True
        win.callOnFlip(ExpStart.clock.reset)  # t=0 on next screen flip; schedule keyboard clock to reset at next scr refresh
        win.callOnFlip(ExpStart.clearEvents, eventType='keyboard')  # clear events on next screen flip
    if ExpStart.status == STARTED and not waitOnFlip:
        theseKeys = ExpStart.getKeys(keyList=['space'], waitRelease=False)
        if len(theseKeys):
            theseKeys = theseKeys[0]  # at least one key was pressed
            
            # check for quit:
            if "escape" == theseKeys:
                endExpNow = True
            ExpStart.keys = theseKeys.name  # just the last key pressed
            ExpStart.rt = theseKeys.rt
            # a response ends the routine
            continueRoutine = False
    
    # check for quit (typically the Esc key)
    if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
        core.quit()
    
    # check if all components have finished
    if not continueRoutine:  # a component has requested a forced-end of Routine
        break
    continueRoutine = False  # will revert to True if at least one component still running
    for thisComponent in ExpSettingsComponents:
        if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
            continueRoutine = True
            break  # at least one component has not yet finished
    
    # refresh the screen
    if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
        win.flip()

# -------Ending Routine "ExpSettings"-------
for thisComponent in ExpSettingsComponents:
    if hasattr(thisComponent, "setAutoDraw"):
        thisComponent.setAutoDraw(False)
thisExp.addData('InstrExp.started', InstrExp.tStartRefresh)
thisExp.addData('InstrExp.stopped', InstrExp.tStopRefresh)
# check responses
if ExpStart.keys in ['', [], None]:  # No response was made
    ExpStart.keys = None
thisExp.addData('ExpStart.keys',ExpStart.keys)
if ExpStart.keys != None:  # we had a response
    thisExp.addData('ExpStart.rt', ExpStart.rt)
thisExp.addData('ExpStart.started', ExpStart.tStartRefresh)
thisExp.addData('ExpStart.stopped', ExpStart.tStopRefresh)
thisExp.nextEntry()
# the Routine "ExpSettings" was not non-slip safe, so reset the non-slip timer
routineTimer.reset()

def recording_warning():
    # ------Prepare to start Routine "StartRecording"-------
    win.mouseVisible=False
    # update component parameters for each repeat
    RecConfirm.keys = []
    RecConfirm.rt = []
    # keep track of which components have finished
    StartRecordingComponents = [ReminderMessage, RecConfirm]
    for thisComponent in StartRecordingComponents:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    StartRecordingClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip
    frameN = -1
    continueRoutine = True

    # -------Run Routine "StartRecording"-------
    while continueRoutine:
        # get current time
        t = StartRecordingClock.getTime()
        tThisFlip = win.getFutureFlipTime(clock=StartRecordingClock)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *ReminderMessage* updates
        if ReminderMessage.status == NOT_STARTED and frameN >= 0.0:
            # keep track of start time/frame for later
            ReminderMessage.frameNStart = frameN  # exact frame index
            ReminderMessage.tStart = t  # local t and not account for scr refresh
            ReminderMessage.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(ReminderMessage, 'tStartRefresh')  # time at next scr refresh
            ReminderMessage.setAutoDraw(True)
        
        # *RecConfirm* updates
        waitOnFlip = False
        if RecConfirm.status == NOT_STARTED and frameN >= 0.0:
            # keep track of start time/frame for later
            RecConfirm.frameNStart = frameN  # exact frame index
            RecConfirm.tStart = t  # local t and not account for scr refresh
            RecConfirm.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(RecConfirm, 'tStartRefresh')  # time at next scr refresh
            RecConfirm.status = STARTED
            # keyboard checking is just starting
            waitOnFlip = True
            win.callOnFlip(RecConfirm.clock.reset)  # t=0 on next screen flip
            win.callOnFlip(RecConfirm.clearEvents, eventType='keyboard')  # clear events on next screen flip
        if RecConfirm.status == STARTED and not waitOnFlip:
            theseKeys = RecConfirm.getKeys(keyList=['p'], waitRelease=False)
            if len(theseKeys):
                theseKeys = theseKeys[0]  # at least one key was pressed
                
                # check for quit:
                if "escape" == theseKeys:
                    endExpNow = True
                RecConfirm.keys = theseKeys.name  # just the last key pressed
                RecConfirm.rt = theseKeys.rt
                # a response ends the routine
                continueRoutine = False
        
        # check for quit (typically the Esc key)
        #if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
        #    core.quit()
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in StartRecordingComponents:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
        
    # -------Ending Routine "StartRecording"-------
    for thisComponent in StartRecordingComponents:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # check responses
    if AllowContinue.keys in ['', [], None]:  # No response was made
        AllowContinue.keys = None
    # the Routine "StartRecording" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()

recording_warning()

# set up handler to look after randomisation of conditions etc
# maximum number of blocks for looping is 52 based on blocks_per_session list
WholeExp = data.TrialHandler(nReps=sum(blocks_per_session), method='random', 
    extraInfo=expInfo, originPath=-1,
    trialList=[None],
    seed=None, name='WholeExp')
thisExp.addLoop(WholeExp)  # add the loop to the experiment
thisWholeExp = WholeExp.trialList[0]  # so we can initialise stimuli with some values
# abbreviate parameter names if possible (e.g. rgb = thisWholeExp.rgb)
if thisWholeExp != None:
    for paramName in thisWholeExp:
        exec('{} = thisWholeExp[paramName]'.format(paramName))



for thisWholeExp in WholeExp:
    currentLoop = WholeExp
    # abbreviate parameter names if possible (e.g. rgb = thisWholeExp.rgb)
    if thisWholeExp != None:
        for paramName in thisWholeExp:
            exec('{} = thisWholeExp[paramName]'.format(paramName))
            


    # set up handler to look after randomisation of conditions etc
    study = data.TrialHandler(nReps=200, method='random', 
        extraInfo=expInfo, originPath=-1,
        trialList=[None],
        seed=None, name='study')
    thisExp.addLoop(study)  # add the loop to the experiment
    thisStudy = study.trialList[0]  # so we can initialise stimuli with some values
    # abbreviate parameter names if possible (e.g. rgb = thisStudy.rgb)
    if thisStudy != None:
        for paramName in thisStudy:
            exec('{} = thisStudy[paramName]'.format(paramName))
    
    for thisStudy in study:
        currentLoop = study
        # abbreviate parameter names if possible (e.g. rgb = thisStudy.rgb)
        if thisStudy != None:
            for paramName in thisStudy:
                exec('{} = thisStudy[paramName]'.format(paramName))
                
    


    # ------Prepare to start Routine "StartStudy"-------
    win.mouseVisible=False
    # update component parameters for each repeat
    sessionType=sessions[sessionCount] # which session type it is now
    condition=conditions[sessionCount] # which condition it is
    condition1 = conditions_c[sessionCount] # which cate condition it is
    maxblocks=blocks_per_session[sessionCount] # how many block max does this session have


    # Generate random block sequence 
    if sessionType=='main' and session_block_count==0:
        mainsessionCount+=1
        sessionBlocks=bsets[mainsessionCount]
        nn=1
        while nn==1:
            blockseq=random.sample(sessionBlocks, len(sessionBlocks))
            checkrep=[]
            for bi in range(len(sessionBlocks)):
                if sum(blockseq[bi:bi+2])>setsizes[1]+2*setsizes[0]: #if any three blocks in a row are longer than one long and two short blocks
                    checkrep.append(1) #put a 1
            if sum(checkrep)>0:
                nn=1
            else:
                nn=0
    if sessionType=='practice' and session_block_count==0:
        blockseq=nPracticeblocks*[setsizes[0]]
    print(blockseq)
    print(session_block_count)
    setsize=blockseq[session_block_count]
    print('Start Session #{} {}, condition {}, block #{}'.format(sessionCount+1,sessionType,condition, session_block_count+1))
    
    # Reminder for Experimenter to start EEG recording before the first main block
    if sessionType=='main' and mainsessionCount==0 and session_block_count==0:
        recording_warning()
    
    # ### EEG and eye-tracker trigger to begin synchronization
    if sessionType=='main' and mainsessionCount==0 and session_block_count==0: # send an initial trigger before the first block of the first main session
        el_tracker.sendMessage('SYNC %d' % 100 )
        parallel.setData(100)
        core.wait(0.005)
        parallel.setData(0)
    
    if sessionType=='practice': #for practice blocks
        pth = "/Users/3447783148qq.com/Desktop/Lab Project Materials/SUN_selection_Matthieu"
        pth1=path_prac1
        pth2 = path_prac2
        images1=img_prac1[(lastindex_prac+1):(lastindex_prac+1+30)]
        images2 = img_prac2[(lastindex_prac+1):(lastindex_prac+1+30)]
    if sessionType=='main': #for main blocks
        pth = "/Users/3447783148qq.com/Desktop/Lab Project Materials/SUN_selection_Matthieu"
        pth1=path1
        pth2 = path2
        images1=allimages1[(lastindex+1):(lastindex+1+30)]
        images2 = allimages2[(lastindex+1):(lastindex+1+30)]
    
    #EEG trigger by phase
    if sessionType=='main':
        trigger_study=1
        trigger_study_offset=99
    if sessionType=='practice':
        trigger_study=255
    
    #List of image files
    j=0 #set trial counter of the study phase to 0
    
    #Since two images (indoor vs. outdoor) are created, each with the amount of setsize, it should be setzise divded by 2
    n = setsize // 2
    cate_index = setsize + 10
    old=[images1[0:n], images2[0:n], ['old']*setsize] #1st half of the list is study items and we label them "old"
    old_study = old[0] + old[1]
    random.shuffle(old_study)
    new=[images1[n:setsize], images2[n:setsize], ['new']*setsize] #2nd half of te list will be used as foils in test and we label them "new"
    new2 = [images1[setsize:cate_index], images2[setsize:cate_index]]
    new_study = new[0] + new[1]
    random.shuffle(new_study)
    # OldNew=[old[0]+new[0],old[1]+new[1]] #merged list and corresponding labels
    msg_cond='OLD'
    if condition1=='find_Indoor':
        msg_cond1='Indoor'
    else:
        msg_cond1='Outdoor'
    
    if session_block_count==0:
        if sessionType == 'practice':
            instr_msg = (
                "In this part of the experiment, you will complete "
                "a memory test and a categorization test.\n\n"
                "Memory test: Find the OLD image.\n"
                "Answer with your {} hand.\n"
                "After each response, the correct old image will be shown "
                "with feedback on your answer.\n\n"
                "Categorization test: Find the {} image.\n"
                "Answer with your {} hand.\n\n"
                "Let's start with some practice.\n\n"
                "Press SPACE when you are ready to start."
            ).format(
                handtext[sessionCount],
                msg_cond1,
                handtext[sessionCount]
            )
        if sessionType=='main':
            instr_msg="We are starting the main blocks of this part. You will get {} blocks\n\nReminder: You need to find the location of {} pictures at test\n\nAnswer with your {} hand\n\nYou will also need to find the location of {} pictures at categorization\n\nAnswer with your {} hand\n\nPress SPACE when you are ready to start".format(maxblocks,msg_cond,handtext[sessionCount],msg_cond1,handtext[sessionCount])

    else:
        if sessionType=='practice':
            instr_msg='When you are ready to start the next block press SPACE'
        if sessionType=='main':
            instr_msg = (
                'Block {} is next.\n\n'
                'Reminder: Find the OLD image during the memory test.\n'
                'Answer with your {} hand.\n\n'
                'During categorization, find the {} image.\n'
                'Answer with your {} hand.\n\n'
                'When you are ready to start the next block press SPACE'
            ).format(
                session_block_count + 1,
                handtext[sessionCount],
                msg_cond1,
                handtext[sessionCount]
            )
    StudyInstr.setText(instr_msg)
    
    GotoStudy.keys = []
    GotoStudy.rt = []
    # keep track of which components have finished
    StartStudyComponents = [StudyInstr, GotoStudy]
    for thisComponent in StartStudyComponents:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    StartStudyClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip
    frameN = -1
    continueRoutine = True
    
    # -------Run Routine "StartStudy"-------
    while continueRoutine:
        # get current time
        t = StartStudyClock.getTime()
        tThisFlip = win.getFutureFlipTime(clock=StartStudyClock)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *StudyInstr* updates
        if StudyInstr.status == NOT_STARTED and frameN >= 0.0:
            # keep track of start time/frame for later
            StudyInstr.frameNStart = frameN  # exact frame index
            StudyInstr.tStart = t  # local t and not account for scr refresh
            StudyInstr.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(StudyInstr, 'tStartRefresh')  # time at next scr refresh
            StudyInstr.setAutoDraw(True)
        
        # *GotoStudy* updates
        waitOnFlip = False
        if GotoStudy.status == NOT_STARTED and frameN >= 0.0:
            # keep track of start time/frame for later
            GotoStudy.frameNStart = frameN  # exact frame index
            GotoStudy.tStart = t  # local t and not account for scr refresh
            GotoStudy.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(GotoStudy, 'tStartRefresh')  # time at next scr refresh
            GotoStudy.status = STARTED
            # keyboard checking is just starting
            waitOnFlip = True
            win.callOnFlip(GotoStudy.clock.reset)  # t=0 on next screen flip
            win.callOnFlip(GotoStudy.clearEvents, eventType='keyboard')  # clear events on next screen flip
        if GotoStudy.status == STARTED and not waitOnFlip:
            theseKeys = GotoStudy.getKeys(keyList=['space'], waitRelease=False)
            if len(theseKeys):
                theseKeys = theseKeys[0]  # at least one key was pressed
                
                # check for quit:
                if "escape" == theseKeys:
                    endExpNow = True
                GotoStudy.keys = theseKeys.name  # just the last key pressed
                GotoStudy.rt = theseKeys.rt
                # a response ends the routine
                continueRoutine = False
        
        # check for quit (typically the Esc key)
        if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
            core.quit()
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in StartStudyComponents:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # -------Ending Routine "StartStudy"-------
    for thisComponent in StartStudyComponents:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    #eyetracker tag for the beginning of the Study phase
    el_tracker.sendMessage('start STUDY block %i, set size %s' %(i,setsize)) 
    WholeExp.addData('StudyInstr.started', StudyInstr.tStartRefresh)
    WholeExp.addData('StudyInstr.stopped', StudyInstr.tStopRefresh)
    # check responses
    if GotoStudy.keys in ['', [], None]:  # No response was made
        GotoStudy.keys = None
    WholeExp.addData('GotoStudy.keys',GotoStudy.keys)
    if GotoStudy.keys != None:  # we had a response
        WholeExp.addData('GotoStudy.rt', GotoStudy.rt)
    WholeExp.addData('GotoStudy.started', GotoStudy.tStartRefresh)
    WholeExp.addData('GotoStudy.stopped', GotoStudy.tStopRefresh)
    # the Routine "StartStudy" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()
    
    # set up handler to look after randomisation of conditions etc
    study = data.TrialHandler(nReps=200, method='random', 
        extraInfo=expInfo, originPath=-1,
        trialList=[None],
        seed=None, name='study')
    thisExp.addLoop(study)  # add the loop to the experiment
    thisStudy = study.trialList[0]  # so we can initialise stimuli with some values
    # abbreviate parameter names if possible (e.g. rgb = thisStudy.rgb)
    if thisStudy != None:
        for paramName in thisStudy:
            exec('{} = thisStudy[paramName]'.format(paramName))
    
    for thisStudy in study:
        currentLoop = study
        # abbreviate parameter names if possible (e.g. rgb = thisStudy.rgb)
        if thisStudy != None:
            for paramName in thisStudy:
                exec('{} = thisStudy[paramName]'.format(paramName))
        
        # ------Prepare to start Routine "StudyPhase"-------
        win.mouseVisible=False
        # update component parameters for each repeat
        phase='study'
        StudyImage.setSize(imagesize)
        absnum+=1 #Update an absolute trial number
        if sessionType=='main':
            epochnum+=1
        print("Study phase, session {}, block {} ({}), trial {}, image {}".format(sessionCount+1,session_block_count+1,sessionType, j+1,old_study[j]))
        
        #Fixation
        if j==0:
            fixtime1=fixtime[0] #Longer duration for the first trial
        else:
            fixtime1=fixtime[1] #shorter for the rest trials
        fixationtime=fixtime1+random.randint(-12,12) #randomize fixation duration (500 +/- 100 ms)
        
        # keep track of which components have finished
        StudyPhaseComponents = [StudyImage, FixImage1, stimtrak1]
        for thisComponent in StudyPhaseComponents:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        StudyPhaseClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip
        frameN = -1
        continueRoutine = True
        
        # -------Run Routine "StudyPhase"-------
        while continueRoutine:
            # get current time
            tThisFlip = win.getFutureFlipTime(clock=StudyPhaseClock)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            if (frameN<ITI+fixationtime): #ITI+fixation
                picture=path+'blank.jpg' #show blank screen before the image
            else:
                full_path1 = os.path.join(pth1, old_study[j])
                full_path2 = os.path.join(pth2, old_study[j])
                if os.path.exists(full_path1):
                    picture=full_path1 #set path to an image file
                else:
                    picture=full_path2
            
            #Eyetracker messages and EEG triggers about trial events:
            if (frameN==ITI): #when ITI ends and fixation starts
                sdfgh=0 ##THIS VARIABLE MEANS NOTHING. It'S HERE ONLY TO AVOID INDENTATION PROBLEMS WHEN NEXT LINES ARE COMMENTED
                el_tracker.startRecording(1, 1, 1, 1) #start eye-tracking
                el_tracker.sendMessage('FIXATION_study')
                el_tracker.sendMessage('trial %i'%absnum) #trial number
                if sessionType=='main':
                    el_tracker.sendMessage('epoch %i'%epochnum) #epoch number
            if (frameN==ITI+fixationtime+1): #when an image is presented
                el_tracker.sendMessage('STUDY_IMG %s' %setsize)
                el_tracker.sendMessage('trial %i'%absnum) #trial number
                if sessionType=='main':
                    el_tracker.sendMessage('epoch %i'%epochnum) #epoch number
                el_tracker.sendMessage('SYNC %d'%trigger_study) #EEG trigger message to eye-tracker
                parallel.setData(trigger_study)
                core.wait(0.005)
                parallel.setData(0)
                
                t_1=StudyPhaseClock.getTime()
            if (frameN==ITI+fixationtime+studytime): #when this image ends
                el_tracker.sendMessage('STIMULUS END')
                el_tracker.sendMessage('SYNC %d' % trigger_study_offset)
                parallel.setData(trigger_study_offset)
                core.wait(0.005)
                parallel.setData(0)
                t_2 = StudyPhaseClock.getTime()
            
            
            # *StudyImage* updates
            if StudyImage.status == NOT_STARTED and frameN >= 0:
                # keep track of start time/frame for later
                StudyImage.frameNStart = frameN  # exact frame index
                StudyImage.tStart = t  # local t and not account for scr refresh
                StudyImage.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(StudyImage, 'tStartRefresh')  # time at next scr refresh
                StudyImage.setAutoDraw(True)
            if StudyImage.status == STARTED:
                if frameN >= (StudyImage.frameNStart + ITI+fixationtime+studytime):
                    # keep track of stop time/frame for later
                    StudyImage.tStop = t  # not accounting for scr refresh
                    StudyImage.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(StudyImage, 'tStopRefresh')  # time at next scr refresh
                    StudyImage.setAutoDraw(False)
            if StudyImage.status == STARTED:  # only update if drawing
                StudyImage.setImage(picture, log=False)
            
            # *FixImage1* updates
            if FixImage1.status == NOT_STARTED and frameN >= ITI:
                # keep track of start time/frame for later
                FixImage1.frameNStart = frameN  # exact frame index
                FixImage1.tStart = t  # local t and not account for scr refresh
                FixImage1.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(FixImage1, 'tStartRefresh')  # time at next scr refresh
                FixImage1.setAutoDraw(True)
            if FixImage1.status == STARTED:
                if frameN >= (FixImage1.frameNStart + fixationtime+studytime):
                    # keep track of stop time/frame for later
                    FixImage1.tStop = t  # not accounting for scr refresh
                    FixImage1.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(FixImage1, 'tStopRefresh')  # time at next scr refresh
                    FixImage1.setAutoDraw(False)
            if FixImage1.status == STARTED:  # only update if drawing
                FixImage1.setImage(path+'fixationpoint_sm.png', log=False)
                    
            # *stimtrak1* updates
            if stimtrak1.status == NOT_STARTED and frameN >= ITI+fixationtime:
                # keep track of start time/frame for later
                stimtrak1.frameNStart = frameN  # exact frame index
                stimtrak1.tStart = t  # local t and not account for scr refresh
                stimtrak1.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(stimtrak1, 'tStartRefresh')  # time at next scr refresh
                stimtrak1.setAutoDraw(True)
            if stimtrak1.status == STARTED:
                if frameN >= (stimtrak1.frameNStart + 1):
                    # keep track of stop time/frame for later
                    stimtrak1.tStop = t  # not accounting for scr refresh
                    stimtrak1.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(stimtrak1, 'tStopRefresh')  # time at next scr refresh
                    stimtrak1.setAutoDraw(False)
            
            # check for quit (typically the Esc key)
            if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
                core.quit()
            
            # check if all components have finished
            if not continueRoutine:  # a component has requested a forced-end of Routine
                break
            continueRoutine = False  # will revert to True if at least one component still running
            for thisComponent in StudyPhaseComponents:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()
        
        # -------Ending Routine "StudyPhase"-------
        print(t_2-t_1)
        
        for thisComponent in StudyPhaseComponents:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        j+=1 #go to next picture
        
        #quit the loop when the study list is over
        if j>=setsize:
            study.finished=True
        else:
            study.finished=False
        
        currentimage=picture.replace(pth,'') #remove path name and keep only picture name
        
        #Save data:
        study.addData('STUDYITEM',currentimage) #which picture was shown
        study.addData('CONDITION',condition) #old or new as a target
        study.addData('SETSIZE',setsize) #setsize: small or large
        study.addData('Trial#',j) #Trial order in this block
        study.addData('TOTALTRIAL',absnum) #Absolute trial order
        if sessionType=='main':
            study.addData('EPOCH',epochnum) #EEG epoch number (only for main blocks)
            study.addData('EEGtrigger',trigger_study) # EEG trigger that was sent
        study.addData('PHASE',phase) #Mark Study phase (only for main blocks)
        study.addData('SESSIONTYPE',sessionType) # which session type it was
        
        study.addData('StudyImage.started', StudyImage.tStartRefresh)
        study.addData('StudyImage.stopped', StudyImage.tStopRefresh)
        #Add participants and experiment metadata
        study.addData('ID', gui.data[0])
        study.addData('Age', gui.data[1])
        study.addData('Gender', gui.data[2])
        study.addData('Handedness', gui.data[3])
        study.addData('COND_SEQUENCE', gui.data[4])
        # the Routine "StudyPhase" was not non-slip safe, so reset the non-slip timer
        routineTimer.reset()
        thisExp.nextEntry()
        
        # Put tracker in Offline mode / Pause eye-tracking
        el_tracker.setOfflineMode()

        # Clear the Host PC screen and wait for 500 ms
        el_tracker.sendCommand('clear_screen 0')
        #pylink.msecDelay()
        
    # completed 200 repeats of 'study'
    
    
    # ------Prepare to start Routine "StartTest"-------
    win.mouseVisible=False
    routineTimer.addTime(6.000000)
    # update component parameters for each repeat
    # twolast=old[0][(setsize-2):setsize] #two last studied items
    # rest_old_images=old[0][0:setsize-2] #the rest of the studied items
    # random.shuffle(rest_old_images)
    twolast=old_study[(setsize-2):setsize]
    rest_old_images=old_study[0:setsize-2]
    random.shuffle(rest_old_images)
    
    #Sequence generation for test trials
    #use two of the $restimages as test trials 1 and 2
    #mix $twolast studied items with other $restimages and show them after trial 2:
    mix=rest_old_images[2:len(rest_old_images)]+twolast
    random.shuffle(mix)
    testseq_old=rest_old_images[0:2]+mix #sequence for old items
    testseq_new=new_study #sequence for new items
    
    #Old images from the study phase + completely new images for categorization phase
    indoor_old = old[0].copy()
    random.shuffle(indoor_old)
    indoor_new = new2[0].copy()
    random.shuffle(indoor_new)
    outdoor_old = old[1].copy()
    random.shuffle(outdoor_old)
    outdoor_new = new2[1].copy()
    random.shuffle(outdoor_new)
    
    cate_lst = []
    
    for ci in range(5):
        cate_lst.append({'old_image': indoor_old[ci], 'new_image': outdoor_new[ci], 'old_category': 'Indoor', 'new_category': 'Outdoor', 'old_pos': 'LEFT', 'new_pos': 'RIGHT'})
    for ci in range(5, 10):
        cate_lst.append({'old_image': indoor_old[ci], 'new_image': outdoor_new[ci], 'old_category': 'Indoor', 'new_category': 'Outdoor', 'old_pos': 'RIGHT', 'new_pos': 'LEFT'})
    for ci in range(5):
        cate_lst.append({'old_image': outdoor_old[ci], 'new_image': indoor_new[ci], 'old_category': 'Outdoor', 'new_category': 'Indoor', 'old_pos': 'LEFT', 'new_pos': 'RIGHT'})
    for ci in range(5, 10):
        cate_lst.append({'old_image': outdoor_old[ci], 'new_image': indoor_new[ci], 'old_category': 'Outdoor', 'new_category': 'Indoor', 'old_pos': 'RIGHT', 'new_pos': 'LEFT'})
    
    random.shuffle(cate_lst)
    
    #Sequence of locations for the correct answer
    half_ss=int(setsize/2) # we need half-set size to provide an equal number of right and left locations (as location list has length 2, so we multiply our half-SS to get the set size number of locations)
    loc_seq=['LEFT','RIGHT']*half_ss
    random.shuffle(loc_seq)
    
    
    k=0 #set counter for test trials
    #Set counter for correct answers
    CorCount=0
    
    TestInstr_Add.setText(t01.format('OLD',handtext[sessionCount]))
        
    # keep track of which components have finished
    StartTestComponents = [TestInstruction, TestInstr_Add]
    
    
    for thisComponent in StartTestComponents:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    StartTestClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip
    frameN = -1
    continueRoutine = True
    
    # -------Run Routine "StartTest"-------
    
    while continueRoutine and routineTimer.getTime() > 0:
        # get current time
        t = StartTestClock.getTime()
        tThisFlip = win.getFutureFlipTime(clock=StartTestClock)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *TestInstruction* updates
        if TestInstruction.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            TestInstruction.frameNStart = frameN  # exact frame index
            TestInstruction.tStart = t  # local t and not account for scr refresh
            TestInstruction.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(TestInstruction, 'tStartRefresh')  # time at next scr refresh
            TestInstruction.setAutoDraw(True)
        if TestInstruction.status == STARTED:
            # is it time to stop? (based on global clock, using actual start)
            if tThisFlipGlobal > TestInstruction.tStartRefresh + 6-frameTolerance:
                # keep track of stop time/frame for later
                TestInstruction.tStop = t  # not accounting for scr refresh
                TestInstruction.frameNStop = frameN  # exact frame index
                win.timeOnFlip(TestInstruction, 'tStopRefresh')  # time at next scr refresh
                TestInstruction.setAutoDraw(False)
        
        # *TestInstr_Add* updates
        if TestInstr_Add.status == NOT_STARTED and tThisFlip >= 3-frameTolerance:
            # keep track of start time/frame for later
            TestInstr_Add.frameNStart = frameN  # exact frame index
            TestInstr_Add.tStart = t  # local t and not account for scr refresh
            TestInstr_Add.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(TestInstr_Add, 'tStartRefresh')  # time at next scr refresh
            TestInstr_Add.setAutoDraw(True)
        if TestInstr_Add.status == STARTED:
            # is it time to stop? (based on global clock, using actual start)
            if tThisFlipGlobal > TestInstr_Add.tStartRefresh + 6-frameTolerance:
                # keep track of stop time/frame for later
                TestInstr_Add.tStop = t  # not accounting for scr refresh
                TestInstr_Add.frameNStop = frameN  # exact frame index
                win.timeOnFlip(TestInstr_Add, 'tStopRefresh')  # time at next scr refresh
                TestInstr_Add.setAutoDraw(False)
        
        # check for quit (typically the Esc key)
        if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
            core.quit()
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in StartTestComponents:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # -------Ending Routine "StartTest"-------
    for thisComponent in StartTestComponents:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    #eyetracker tag for the beginning of the Test phase
    el_tracker.sendMessage('start TEST block %i, set size %s' %(i,setsize))
    WholeExp.addData('TestInstruction.started', TestInstruction.tStartRefresh)
    WholeExp.addData('TestInstruction.stopped', TestInstruction.tStopRefresh)
    WholeExp.addData('TestInstr_Add.started', TestInstr_Add.tStartRefresh)
    WholeExp.addData('TestInstr_Add.stopped', TestInstr_Add.tStopRefresh)
    
    # set up handler to look after randomisation of conditions etc
    test = data.TrialHandler(nReps=200, method='random', 
        extraInfo=expInfo, originPath=-1,
        trialList=[None],
        seed=None, name='test')
    thisExp.addLoop(test)  # add the loop to the experiment
    thisTest = test.trialList[0]  # so we can initialise stimuli with some values
    # abbreviate parameter names if possible (e.g. rgb = thisTest.rgb)
    if thisTest != None:
        for paramName in thisTest:
            exec('{} = thisTest[paramName]'.format(paramName))
    
    for thisTest in test:
        currentLoop = test
        # abbreviate parameter names if possible (e.g. rgb = thisTest.rgb)
        if thisTest != None:
            for paramName in thisTest:
                exec('{} = thisTest[paramName]'.format(paramName))
        
        # ------Prepare to start Routine "TestPhase"-------
        win.mouseVisible=False
        # update component parameters for each repeat

        #Location
        target_loc=loc_seq[k] #set target location for this trial
        
        #Fixation point timing
        if k==0:
            fixtime1=fixtime[0] #Longer duration for the first trial
        else:
            fixtime1=fixtime[1] #shorter for the rest trials
        fixationtime=fixtime1+random.randint(-12,12)
        print("Test phase, session {}, block {} ({}), trial {}".format(sessionCount+1,session_block_count+1,sessionType, k+1))
        print("Images: {}; {}".format(testseq_old[k],testseq_new[k]))
        print("Target location: {}".format(target_loc))
        absnum+=1 #Update an absolute trial number
        if sessionType=='main':
            epochnum+=1
        
        # Recognition always asks participant to find OLD.
        # Therefore, target_loc is always the OLD image location.
        if target_loc == 'LEFT':
            old_pos = (-pos_shift, 0)
            new_pos = (pos_shift, 0)
        else: 
            old_pos = (pos_shift, 0)
            new_pos = (-pos_shift, 0)

        # EEG trigger by phase
        if sessionType == 'main':
            trigger_test = 2
            trigger_resp = 21
            trigger_noanswer = 222
        else:  # practice
            trigger_test = 255
                
        # Images to show
        test_old_path1 = os.path.join(pth1, testseq_old[k])
        test_old_path2 = os.path.join(pth2, testseq_old[k])
        test_new_path1 = os.path.join(pth1, testseq_new[k])
        test_new_path2 = os.path.join(pth2, testseq_new[k])
        if os.path.exists(test_old_path1):
            OldImage = visual.ImageStim(
                win=win,
                name='OldImage', units='pix',
                image=test_old_path1, mask=None,
                ori=0, pos=old_pos, size=imagesize,
                color=[1,1,1], colorSpace='rgb', opacity=1,
                flipHoriz=False, flipVert=False,
                texRes=128, interpolate=True, depth=-1.0)
        elif os.path.exists(test_old_path2):
            OldImage = visual.ImageStim(
                win=win,
                name='OldImage', units='pix',
                image=test_old_path2, mask=None,
                ori=0, pos=old_pos, size=imagesize,
                color=[1,1,1], colorSpace='rgb', opacity=1,
                flipHoriz=False, flipVert=False,
                texRes=128, interpolate=True, depth=-1.0)
        if os.path.exists(test_new_path1):
            NewImage = visual.ImageStim(
                win=win,
                name='NewImage', units='pix', 
                image=test_new_path1, mask=None,
                ori=0, pos=new_pos, size=imagesize,
                color=[1,1,1], colorSpace='rgb', opacity=1,
                flipHoriz=False, flipVert=False,
                texRes=128, interpolate=True, depth=-1.0)
        elif os.path.exists(test_new_path2):
            NewImage = visual.ImageStim(
                win=win,
                name='NewImage', units='pix', 
                image=test_new_path2, mask=None,
                ori=0, pos=new_pos, size=imagesize,
                color=[1,1,1], colorSpace='rgb', opacity=1,
                flipHoriz=False, flipVert=False,
                texRes=128, interpolate=True, depth=-1.0)

        phase='test' #mark the test phase
        
        #THIS CODE ONLY FOR TECHICAL TESTING PURPOSES
        #dur=random.randint(600,1000)/1000 #assigns random reaction times
        
        Resp.keys = []
        Resp.rt = []
        # keep track of which components have finished
        TestPhaseComponents = [Blank_L, Blank_R, OldImage, NewImage, FixImage2, qmark, stimtrak2, Resp]
        for thisComponent in TestPhaseComponents:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        TestPhaseClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip
        frameN = -1
        continueRoutine = True
        
        # -------Run Routine "TestPhase"-------
        while continueRoutine:
            # get current time
            t = TestPhaseClock.getTime()
            tThisFlip = win.getFutureFlipTime(clock=TestPhaseClock)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            
            #Eyetracker messages and EEG triggers about trial events and conditions:
            if sessionType=='main':
                if (frameN==0): #When fixation starts
                    sdfgh=0 ##THIS VARIABLE MEANS NOTHING. It'S HERE ONLY TO AVOID INDENTATION PROBLEMS WHEN NEXT LINES ARE COMMENTED
                    el_tracker.startRecording(1, 1, 1, 1) #start eye-tracking
                    el_tracker.sendMessage('FIXATION_test') #trial number
                    el_tracker.sendMessage('trial %i'%absnum)
                    if sessionType=='main':
                        el_tracker.sendMessage('epoch %i'%epochnum) #epoch number
                if (frameN==fixationtime+1): #when an image starts
                    el_tracker.sendMessage('TEST_IMG %s' %setsize)
                    el_tracker.sendMessage('trial %i'%absnum)
                    if sessionType=='main':
                        el_tracker.sendMessage('epoch %i'%epochnum) #epoch number
                    el_tracker.sendMessage('SYNC %d'%trigger_test) #EEG trigger message to eye-tracker
                    parallel.setData(trigger_test)
                    core.wait(0.005)
                    parallel.setData(0)

                    
                    t_3=TestPhaseClock.getTime()
                    fr_3=frameN
                if (frameN==fixationtime+testtime): #when the participant can start answering
                    el_tracker.sendMessage('RESPONSE START')
                    el_tracker.sendMessage('SYNC 199')
                    parallel.setData(199)
                    core.wait(0.005)
                    parallel.setData(0)
                    
                    t_4=TestPhaseClock.getTime()
                    fr_4=frameN
            if sessionType=='practice':
                if (frameN==0):
                    el_tracker.startRecording(1, 1, 1, 1) #start eye-tracking
                if (frameN==fixationtime+1): #when an image starts
                    t_3=TestPhaseClock.getTime()
                    fr_3=frameN
                if (frameN==fixationtime+testtime): #when the participant can start answering
                    t_4=TestPhaseClock.getTime()
                    fr_4=frameN
            
            # *Blank_L* updates
            if Blank_L.status == NOT_STARTED and frameN >= 0:
                # keep track of start time/frame for later
                Blank_L.frameNStart = frameN  # exact frame index
                Blank_L.tStart = t  # local t and not account for scr refresh
                Blank_L.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(Blank_L, 'tStartRefresh')  # time at next scr refresh
                Blank_L.setAutoDraw(True)
            if Blank_L.status == STARTED:
                if frameN >= (fixationtime):
                    # keep track of stop time/frame for later
                    Blank_L.tStop = t  # not accounting for scr refresh
                    Blank_L.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(Blank_L, 'tStopRefresh')  # time at next scr refresh
                    Blank_L.setAutoDraw(False)
            
            # *Blank_R* updates
            if Blank_R.status == NOT_STARTED and frameN >= 0:
                # keep track of start time/frame for later
                Blank_R.frameNStart = frameN  # exact frame index
                Blank_R.tStart = t  # local t and not account for scr refresh
                Blank_R.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(Blank_R, 'tStartRefresh')  # time at next scr refresh
                Blank_R.setAutoDraw(True)
            if Blank_R.status == STARTED:
                if frameN >= (fixationtime):
                    # keep track of stop time/frame for later
                    Blank_R.tStop = t  # not accounting for scr refresh
                    Blank_R.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(Blank_R, 'tStopRefresh')  # time at next scr refresh
                    Blank_R.setAutoDraw(False)
            
            # *OldImage* updates
            if OldImage.status == NOT_STARTED and frameN >= fixationtime:
                # keep track of start time/frame for later
                OldImage.frameNStart = frameN  # exact frame index
                OldImage.tStart = t  # local t and not account for scr refresh
                OldImage.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(OldImage, 'tStartRefresh')  # time at next scr refresh
                OldImage.setAutoDraw(True)
            if OldImage.status == STARTED:
                if frameN >= (fixationtime+testtime+respwait):
                    # keep track of stop time/frame for later
                    OldImage.tStop = t  # not accounting for scr refresh
                    OldImage.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(OldImage, 'tStopRefresh')  # time at next scr refresh
                    OldImage.setAutoDraw(False)
            
            # *NewImage* updates
            if NewImage.status == NOT_STARTED and frameN >= fixationtime:
                # keep track of start time/frame for later
                NewImage.frameNStart = frameN  # exact frame index
                NewImage.tStart = t  # local t and not account for scr refresh
                NewImage.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(NewImage, 'tStartRefresh')  # time at next scr refresh
                NewImage.setAutoDraw(True)
            if NewImage.status == STARTED:
                if frameN >= (fixationtime+testtime+respwait):
                    # keep track of stop time/frame for later
                    NewImage.tStop = t  # not accounting for scr refresh
                    NewImage.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(NewImage, 'tStopRefresh')  # time at next scr refresh
                    NewImage.setAutoDraw(False) 
            

            # *FixImage2* updates
            if FixImage2.status == NOT_STARTED and frameN >= 0:
                # keep track of start time/frame for later
                FixImage2.frameNStart = frameN  # exact frame index
                FixImage2.tStart = t  # local t and not account for scr refresh
                FixImage2.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(FixImage2, 'tStartRefresh')  # time at next scr refresh
                FixImage2.setAutoDraw(True)
            if FixImage2.status == STARTED:
                if frameN >= (FixImage2.frameNStart + fixationtime+testtime):
                    # keep track of stop time/frame for later
                    FixImage2.tStop = t  # not accounting for scr refresh
                    FixImage2.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(FixImage2, 'tStopRefresh')  # time at next scr refresh
                    FixImage2.setAutoDraw(False)
            # *qmark* updates
            if qmark.status == NOT_STARTED and frameN >= fixationtime+testtime:
                # keep track of start time/frame for later
                qmark.frameNStart = frameN  # exact frame index
                qmark.tStart = t  # local t and not account for scr refresh
                qmark.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(qmark, 'tStartRefresh')  # time at next scr refresh
                qmark.setAutoDraw(True)
            if qmark.status == STARTED:
                if frameN >= (qmark.frameNStart+respwait):
                    # keep track of stop time/frame for later
                    qmark.tStop = t  # not accounting for scr refresh
                    qmark.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(qmark, 'tStopRefresh')  # time at next scr refresh
                    qmark.setAutoDraw(False)
                    
            # *stimtrak2* updates
            if stimtrak2.status == NOT_STARTED and frameN >= fixationtime:
                # keep track of start time/frame for later
                stimtrak2.frameNStart = frameN  # exact frame index
                stimtrak2.tStart = t  # local t and not account for scr refresh
                stimtrak2.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(stimtrak2, 'tStartRefresh')  # time at next scr refresh
                stimtrak2.setAutoDraw(True)
            if stimtrak2.status == STARTED:
                if frameN >= (stimtrak2.frameNStart + 1):
                    # keep track of stop time/frame for later
                    stimtrak2.tStop = t  # not accounting for scr refresh
                    stimtrak2.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(stimtrak2, 'tStopRefresh')  # time at next scr refresh
                    stimtrak2.setAutoDraw(False)
            
                    
            # *Resp* updates
            waitOnFlip = False
            if Resp.status == NOT_STARTED and frameN >= fixationtime+testtime:
                # keep track of start time/frame for later
                Resp.frameNStart = frameN  # exact frame index
                Resp.tStart = t  # local t and not account for scr refresh
                Resp.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(Resp, 'tStartRefresh')  # time at next scr refresh
                Resp.status = STARTED
                # keyboard checking is just starting
                waitOnFlip = True
                win.callOnFlip(Resp.clock.reset)  # t=0 on next screen flip
                win.callOnFlip(Resp.clearEvents, eventType='keyboard')  # clear events on next screen flip
            if Resp.status == STARTED:
                if frameN >= (Resp.frameNStart + respwait):
                    # keep track of stop time/frame for later
                    Resp.tStop = t  # not accounting for scr refresh
                    Resp.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(Resp, 'tStopRefresh')  # time at next scr refresh
                    # NO-RESPONSE trigger for EEG + EyeLink
                    if sessionType == 'main':
                        el_tracker.sendMessage('SYNC %d' % trigger_noanswer)
                        parallel.setData(trigger_noanswer)
                        core.wait(0.005)
                        parallel.setData(0)
                    Resp.status = FINISHED
            if Resp.status == STARTED and not waitOnFlip:
                theseKeys = Resp.getKeys(keyList=buttons, waitRelease=False)
                if len(theseKeys):
                    theseKeys = theseKeys[0]   # at least one key was pressed
                    
                    # check for quit:
                    if "escape" == theseKeys:
                        endExpNow = True
                    Resp.keys = theseKeys.name  # just the last key pressed
                    Resp.rt = theseKeys.rt
                    #RESPONSE TRIGGER FOR EEG & eye-tracker:
                    if sessionType=='main':
                        el_tracker.sendMessage('SYNC %d'%trigger_resp) #EEG trigger message to eye-tracker
                        parallel.setData(trigger_resp)
                        core.wait(0.005)
                        parallel.setData(0)
                    # a response ends the routine
                    continueRoutine = False

            
            # check for quit (typically the Esc key)
            if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
                core.quit()
            
            # check if all components have finished
            if not continueRoutine:  # a component has requested a forced-end of Routine
                break
            continueRoutine = False  # will revert to True if at least one component still running
            for thisComponent in TestPhaseComponents:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()
        
        # -------Ending Routine "TestPhase"-------

        print(t_4-t_3)
        print(fr_4-fr_3)

        if (Resp.keys==buttons[0]):
            ANSWER='LEFT'
        elif (Resp.keys==buttons[1]):
            ANSWER='RIGHT'
        else:
            ANSWER='NoAnswer'
        
        if (ANSWER==target_loc):
            CORANS='CORRECT'
        if (ANSWER!=target_loc):
            CORANS='INCORRECT'
        if (ANSWER=='NoAnswer'):
            CORANS='NO ANSWER'
        
        for thisComponent in TestPhaseComponents:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        
        old_image=testseq_old[k] #sequence with old images
        new_image=testseq_new[k] #sequence with new images
        
        k+=1 #go to next pictures
        
        #Update the counter of correct answers
        if CORANS=='CORRECT':
            CorCount+=1
            recognition_correct+=1
        else:
            CorCount+=0
            
        recognition_trials+=1
        block_recognition_accuracy=int(round((100 * CorCount / k), 0))
        
        cumulative_recognition_accuracy = int(round((100 * recognition_correct / recognition_trials), 0))
        
        print("Answer: {}, Running correct: {}%".format(CORANS, int(round(100*CorCount/k,0))))
        print("Block Accuracy: {}%, Cumulative Recognition Accuracy: {}%".format(block_recognition_accuracy, cumulative_recognition_accuracy))
        
        #Save data:
        test.addData('OLDITEM',old_image) 
        test.addData('NEWITEM',new_image) 
        test.addData('CONDITION',condition) #old or new as a target
        test.addData('SETSIZE',setsize) #old or new as a target
        test.addData('Trial#',k) #Trial order in this block
        test.addData('TOTALTRIAL',absnum) #Absolute trial order
        if sessionType=='main':
            test.addData('EPOCH',epochnum) #EEG epoch number (only for main blocks)
            test.addData('EEGtrigger',trigger_test) # EEG trigger that was sent; maybe a potential coding error, since this may be test.addData()
        test.addData('PHASE',phase) #Mark Study phase
        test.addData('SESSIONTYPE',sessionType) # which session type it was
        test.addData('TARGET_LOC',target_loc) #target location (left or right)
        test.addData('ANSWER',ANSWER) #mark answer as "red" or "blue"
        test.addData('CORRECT',CORANS) #mark whether an answer was correct or not
        test.addData('BLOCK_RECOGNITION_ACCURACY', block_recognition_accuracy)
        test.addData('CUMULATIVE_RECOGNITION_ACCURACY', cumulative_recognition_accuracy)

        #Add participants and experiment metadata
        test.addData('ID', gui.data[0])
        test.addData('Age', gui.data[1])
        test.addData('Gender', gui.data[2])
        test.addData('Handedness', gui.data[3])
        test.addData('COND_SEQUENCE', gui.data[4])
        # check responses
        if Resp.keys in ['', [], None]:  # No response was made
            Resp.keys = None
        test.addData('Resp.keys',Resp.keys)
        if Resp.keys != None:  # we had a response
            test.addData('Resp.rt', Resp.rt)
        test.addData('Resp.started', Resp.tStartRefresh)
        test.addData('Resp.stopped', Resp.tStopRefresh)
        # the Routine "TestPhase" was not non-slip safe, so reset the non-slip timer
        routineTimer.reset()
        thisExp.nextEntry()
        
        # Put tracker in Offline mode / Pause eye-tracking
        el_tracker.setOfflineMode()

        # Clear the Host PC screen and wait for 500 ms
        el_tracker.sendCommand('clear_screen 0')
        
                # update component parameters for each repeat
        # Feedback for both practice and main trials
        fbtime = 0.5
        fb_msg = CORANS
        fbtime = round(fbtime * framesec, 0)
        
        gotoTrial.keys = []
        gotoTrial.rt = []
        # keep track of which components have finished
        NextTrialComponents = [BlankScreen_L,BlankScreen_R,fbFrame,feedback,OldImage,gotoTrial]
        for thisComponent in NextTrialComponents:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        NextTrialClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip;may be a potential coding error: should be NextTrialClock.reset(-_timeToFirstFrame)
        frameN = -1
        continueRoutine = True
        
        # -------Run Routine "NextTrial"-------
        while continueRoutine:
            # get current time
            t = NextTrialClock.getTime()
            tThisFlip = win.getFutureFlipTime(clock=NextTrialClock)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            if (frameN<=fbtime): #Feedback time
                fb_message=fb_msg #show the feedback message
                fb_textsize=40
            else:
                fb_message='Press SPACE for the next trial' #Reminder to switch to the next trial
                fb_textsize=20
                #Quit trial feedback on the last trial of the block (when k == set size)
                if k==setsize:
                    continueRoutine=False
            
            # *BlankScreen_L* updates
            if BlankScreen_L.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                BlankScreen_L.frameNStart = frameN  # exact frame index
                BlankScreen_L.tStart = t  # local t and not account for scr refresh
                BlankScreen_L.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(BlankScreen_L, 'tStartRefresh')  # time at next scr refresh
                BlankScreen_L.setAutoDraw(True)
              
            # *BlankScreen_R* updates
            if BlankScreen_R.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                BlankScreen_R.frameNStart = frameN  # exact frame index
                BlankScreen_R.tStart = t  # local t and not account for scr refresh
                BlankScreen_R.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(BlankScreen_R, 'tStartRefresh')  # time at next scr refresh
                BlankScreen_R.setAutoDraw(True)
                
            # *fbFrame* updates
            if fbFrame.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                fbFrame.frameNStart = frameN  # exact frame index
                fbFrame.tStart = t  # local t and not account for scr refresh
                fbFrame.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(fbFrame, 'tStartRefresh')  # time at next scr refresh
                fbFrame.setAutoDraw(True)
            
            # Show the OLD image during recognition feedback
            if OldImage.status == NOT_STARTED and frameN == 0:
                OldImage.setAutoDraw(True)
                OldImage.status = STARTED
            
            if OldImage.status == STARTED and frameN >= fbtime:
                OldImage.setAutoDraw(False)
                OldImage.status = FINISHED
            
            # *feedback* updates
            if feedback.status == NOT_STARTED and frameN >= 0:
                # keep track of start time/frame for later
                feedback.frameNStart = frameN  # exact frame index
                feedback.tStart = t  # local t and not account for scr refresh
                feedback.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(feedback, 'tStartRefresh')  # time at next scr refresh
                feedback.setAutoDraw(True)
            if feedback.status == STARTED:  # only update if drawing
                feedback.setText(fb_message, log=False)
                feedback.setHeight(fb_textsize, log=False)
                
            # *gotoTrial* updates
            waitOnFlip = False
            if gotoTrial.status == NOT_STARTED and frameN >= fbtime:
                # keep track of start time/frame for later
                gotoTrial.frameNStart = frameN  # exact frame index
                gotoTrial.tStart = t  # local t and not account for scr refresh
                gotoTrial.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(gotoTrial, 'tStartRefresh')  # time at next scr refresh
                gotoTrial.status = STARTED
                # keyboard checking is just starting
                waitOnFlip = True
                win.callOnFlip(gotoTrial.clock.reset)  # t=0 on next screen flip
                win.callOnFlip(gotoTrial.clearEvents, eventType='keyboard')  # clear events on next screen flip
            if gotoTrial.status == STARTED and not waitOnFlip:
                theseKeys = gotoTrial.getKeys(keyList=['space'], waitRelease=False)
                if len(theseKeys):
                    theseKeys = theseKeys[0]  # at least one key was pressed
                    
                    # check for quit:
                    if "escape" == theseKeys:
                        endExpNow = True
                    gotoTrial.keys = theseKeys.name  # just the last key pressed
                    gotoTrial.rt = theseKeys.rt
                    # a response ends the routine
                    continueRoutine = False
                    
            # check for quit (typically the Esc key)
            if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
                core.quit()
            
            # check if all components have finished
            if not continueRoutine:  # a component has requested a forced-end of Routine
                break
            continueRoutine = False  # will revert to True if at least one component still running
            for thisComponent in NextTrialComponents:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()
        
        # -------Ending Routine "NextTrial"-------
        
        for thisComponent in NextTrialComponents:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        
        #quit the loop when the test list is finished
        if k>=len(testseq_old):
            test.finished=True
        else:
            test.finished=False
            
        #old_image=picture_old.replace(pth,'')
        #new_image=picture_old.replace(pth,'')
        
        # check responses
        if gotoTrial.keys in ['', [], None]:  # No response was made
            gotoTrial.keys = None

        # the Routine "NextTrial" was not non-slip safe, so reset the non-slip timer
        routineTimer.reset()
        thisExp.nextEntry()
        
    # Prepare to start Routine "StartCategorization"
    win.mouseVisible=False
    c=0 #count the number of categorization trials
    CorCount1=0
    
    if condition1=='find_Indoor':
        CategorInstr_Add.setText(t02.format('Indoor', handtext[sessionCount]))
    else:
        CategorInstr_Add.setText(t02.format('Outdoor', handtext[sessionCount]))
    
    StartCateComponents = [CategorInstruction, CategorInstr_Add]
    for thisComponent in StartCateComponents:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock='now')
    StartCateClock.reset(-_timeToFirstFrame)
    frameN = -1
    
    #initalize instruction timer for categorization phase
    routineTimer.reset()
    routineTimer.addTime(6.0)
    StartCateClock.reset()
    
    continueRoutine = True
    
    while continueRoutine and routineTimer.getTime() > 0:
        t = StartCateClock.getTime()
        tThisFlip = win.getFutureFlipTime(clock=StartCateClock)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN += 1
        
        if CategorInstruction.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            CategorInstruction.frameNStart = frameN
            CategorInstruction.tStart = t
            CategorInstruction.tStartRefresh = tThisFlipGlobal
            win.timeOnFlip(CategorInstruction, 'tStartRefresh')
            CategorInstruction.setAutoDraw(True)
        if CategorInstruction.status == STARTED:
            if tThisFlipGlobal > CategorInstruction.tStartRefresh + 6-frameTolerance:
                CategorInstruction.tStop = t
                CategorInstruction.frameNStop = frameN
                win.timeOnFlip(CategorInstruction, 'tStopRefresh')
                CategorInstruction.setAutoDraw(False)
        
        if CategorInstr_Add.status == NOT_STARTED and tThisFlip >= 3-frameTolerance:
            CategorInstr_Add.frameNStart = frameN
            CategorInstr_Add.tStart = t
            CategorInstr_Add.tStartRefresh = tThisFlipGlobal
            win.timeOnFlip(CategorInstr_Add, 'tStartRefresh')
            CategorInstr_Add.setAutoDraw(True)
        if CategorInstr_Add.status == STARTED:
            if tThisFlipGlobal > CategorInstr_Add.tStartRefresh + 6-frameTolerance:
                CategorInstr_Add.tStop = t
                CategorInstr_Add.frameNStop = frameN
                win.timeOnFlip(CategorInstr_Add, 'tStopRefresh')
                CategorInstr_Add.setAutoDraw(False)
        
        if endExpNow or defaultKeyboard.getKeys(keyList=['escape']):
            core.quit()
        
        if not continueRoutine:
            break
        continueRoutine = False
        for thisComponent in StartCateComponents:
            if hasattr(thisComponent, 'status') and thisComponent.status != FINISHED:
                continueRoutine = True
                break
        
        if continueRoutine:
            win.flip()
    
    for thisComponent in StartCateComponents:
        if hasattr(thisComponent, 'setAutoDraw'):
            thisComponent.setAutoDraw(False)
    el_tracker.sendMessage('start Cate Block %i, set size %s' %(i,setsize))
    WholeExp.addData('CategorInstruction.started', CategorInstruction.tStartRefresh)
    WholeExp.addData('CategorInstruction.stopped', CategorInstruction.tStopRefresh)
    WholeExp.addData('CategorInstr_Add.started', CategorInstr_Add.tStartRefresh)
    WholeExp.addData('CategorInstr_Add.stopped', CategorInstr_Add.tStopRefresh)
    
    # set up categorization trials for each block
    cate_test = data.TrialHandler(nReps=setsize, method='random', extraInfo=expInfo, originPath=-1, trialList=[None], seed=None, name='cate_test')
    thisExp.addLoop(cate_test)
    thisCate = cate_test.trialList[0]
    if thisCate != None:
        for paraName in thisCate:
            exec('{} = thisCate[paraName]'.format(paraName))
    
    for thisCate in cate_test:
        currentLoop = cate_test
        if thisCate != None:
            for paraName in thisCate:
                exec('{} = thisCate[paraName]'.format(paraName))
        
        #Prepare to start Routine "CategorizationPhase"
        win.mouseVisible=False
        
        cate_dict = cate_lst[c]
        #each categorization dictionary represents one categorization trial
        if condition1=='find_Indoor':
            if cate_dict['old_category']=='Indoor':
                if cate_dict['old_pos']=='LEFT':
                    target_loc = 'LEFT'
                    old_pos=(-pos_shift,0)
                    new_pos=(pos_shift,0)
                else:
                    target_loc = 'RIGHT'
                    old_pos=(pos_shift,0)
                    new_pos=(-pos_shift,0)
            else:
                if cate_dict['new_pos']=='LEFT':
                    target_loc = 'LEFT'
                    new_pos=(-pos_shift,0)
                    old_pos=(pos_shift,0)
                else:
                    target_loc = 'RIGHT'
                    new_pos=(pos_shift,0)
                    old_pos=(-pos_shift,0)
        
        elif condition1=='find_Outdoor':
            if cate_dict['old_category']=='Outdoor':
                if cate_dict['old_pos']=='LEFT':
                    target_loc = 'LEFT'
                    old_pos=(-pos_shift,0)
                    new_pos=(pos_shift,0)
                else:
                    target_loc = 'RIGHT'
                    old_pos=(pos_shift,0)
                    new_pos=(-pos_shift,0)
            else:
                if cate_dict['new_pos']=='LEFT': 
                    target_loc = 'LEFT'
                    old_pos=(pos_shift,0)
                    new_pos=(-pos_shift,0)
                else:
                    target_loc = 'RIGHT'
                    old_pos=(-pos_shift,0)
                    new_pos=(pos_shift,0)
                    
        #Get the specific image file from inside a folder
        old_image = cate_dict['old_image']
        new_image = cate_dict['new_image']
        
        if c == 0:
            fixtime1 = fixtime[0]
        else:
            fixtime1 = fixtime[1]
        fixationtime = fixtime1 + random.randint(-12, 12)
        print("Categorization phase, session {}, block {} ({}), trial {}".format(sessionCount+1,session_block_count+1,sessionType, c+1))
        print("Images: {}, {}; {}, {}".format(old_image, cate_dict['old_category'], new_image, cate_dict['new_category']))
        print("Target location: {}".format(target_loc))
        absnum+=1 #Update an absolute trial number
        if sessionType=='main':
            epochnum+=1
    
        # EEG trigger by phase
        if sessionType == 'main':
            trigger_cate = 3
            trigger_resp1 = 31
            trigger_noanswer1 = 223
        else:  # practice
            trigger_cate = 255
            
        # Images to show
        old_path_indoor = os.path.join(pth1, old_image)
        old_path_outdoor = os.path.join(pth2, old_image)
        new_path_indoor = os.path.join(pth1, new_image)
        new_path_outdoor = os.path.join(pth2, new_image)
        if os.path.exists(old_path_indoor):
            OldImage = visual.ImageStim(
                win=win,
                name='OldImage', units='pix',
                image=old_path_indoor, mask=None,
                ori=0, pos=old_pos, size=imagesize,
                color=[1,1,1], colorSpace='rgb', opacity=1,
                flipHoriz=False, flipVert=False,
                texRes=128, interpolate=True, depth=-1.0)
        else:
            OldImage = visual.ImageStim(
                win=win,
                name='OldImage', units='pix',
                image=old_path_outdoor, mask=None,
                ori=0, pos=old_pos, size=imagesize,
                color=[1,1,1], colorSpace='rgb', opacity=1,
                flipHoriz=False, flipVert=False,
                texRes=128, interpolate=True, depth=-1.0)
        if os.path.exists(new_path_indoor):    
            NewImage = visual.ImageStim(
                win=win,
                name='NewImage', units='pix', 
                image=new_path_indoor, mask=None,
                ori=0, pos=new_pos, size=imagesize,
                color=[1,1,1], colorSpace='rgb', opacity=1,
                flipHoriz=False, flipVert=False,
                texRes=128, interpolate=True, depth=-1.0)
        else:
            NewImage = visual.ImageStim(
                win=win,
                name='NewImage', units='pix', 
                image=new_path_outdoor, mask=None,
                ori=0, pos=new_pos, size=imagesize,
                color=[1,1,1], colorSpace='rgb', opacity=1,
                flipHoriz=False, flipVert=False,
                texRes=128, interpolate=True, depth=-1.0)
                    
        phase = 'Categorization test'
        Resp1.keys = []
        Resp1.rt = []
        # keep track of which components have finished
        CategorPhaseComponents = [Blank_L, Blank_R, OldImage, NewImage, FixImage3, qmark, stimtrak3, Resp1]
        for thisComponent in CategorPhaseComponents:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        CategorPhaseClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip
        frameN = -1
        continueRoutine = True
        
        # -------Run Routine "Categorization Phase"-------
        while continueRoutine:
            # get current time
            t = CategorPhaseClock.getTime()
            tThisFlip = win.getFutureFlipTime(clock=CategorPhaseClock)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            
            #Eyetracker messages and EEG triggers about trial events and conditions:
            if sessionType=='main':
                if (frameN==0): #When fixation starts
                    sdfgh=0 ##THIS VARIABLE MEANS NOTHING. It'S HERE ONLY TO AVOID INDENTATION PROBLEMS WHEN NEXT LINES ARE COMMENTED
                    el_tracker.startRecording(1, 1, 1, 1) #start eye-tracking
                    el_tracker.sendMessage('FIXATION_test') #trial number
                    el_tracker.sendMessage('trial %i'%absnum)
                    if sessionType=='main':
                        el_tracker.sendMessage('epoch %i'%epochnum) #epoch number
                if (frameN==fixationtime+1): #when an image starts
                    el_tracker.sendMessage('CateTEST_IMG %s' %setsize)
                    el_tracker.sendMessage('trial %i'%absnum)
                    if sessionType=='main':
                        el_tracker.sendMessage('epoch %i'%epochnum) #epoch number
                    el_tracker.sendMessage('SYNC %d'%trigger_cate) #EEG trigger message to eye-tracker
                    parallel.setData(trigger_cate)
                    core.wait(0.005)
                    parallel.setData(0)
                    t_5=CategorPhaseClock.getTime()
                    fr_5=frameN
                    
                if (frameN==fixationtime+testtime): #when the participant can start answering
                    el_tracker.sendMessage('RESPONSE START')
                    el_tracker.sendMessage('SYNC 199')
                    parallel.setData(199)
                    core.wait(0.005)
                    parallel.setData(0) 
                    t_6=CategorPhaseClock.getTime()
                    fr_6=frameN
                    
            if sessionType=='practice':
                if (frameN==0):
                    el_tracker.startRecording(1, 1, 1, 1) #start eye-tracking
                if (frameN==fixationtime+1): #when an image starts
                    t_5=CategorPhaseClock.getTime()
                    fr_5=frameN
                if (frameN==fixationtime+testtime): #when the participant can start answering
                    t_6=CategorPhaseClock.getTime()
                    fr_6=frameN
            
            # *Blank_L* updates
            if Blank_L.status == NOT_STARTED and frameN >= 0:
                # keep track of start time/frame for later
                Blank_L.frameNStart = frameN  # exact frame index
                Blank_L.tStart = t  # local t and not account for scr refresh
                Blank_L.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(Blank_L, 'tStartRefresh')  # time at next scr refresh
                Blank_L.setAutoDraw(True)
            if Blank_L.status == STARTED:
                if frameN >= (fixationtime):
                    # keep track of stop time/frame for later
                    Blank_L.tStop = t  # not accounting for scr refresh
                    Blank_L.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(Blank_L, 'tStopRefresh')  # time at next scr refresh
                    Blank_L.setAutoDraw(False)
            
            # *Blank_R* updates
            if Blank_R.status == NOT_STARTED and frameN >= 0:
                # keep track of start time/frame for later
                Blank_R.frameNStart = frameN  # exact frame index
                Blank_R.tStart = t  # local t and not account for scr refresh
                Blank_R.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(Blank_R, 'tStartRefresh')  # time at next scr refresh
                Blank_R.setAutoDraw(True)
            if Blank_R.status == STARTED:
                if frameN >= (fixationtime):
                    # keep track of stop time/frame for later
                    Blank_R.tStop = t  # not accounting for scr refresh
                    Blank_R.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(Blank_R, 'tStopRefresh')  # time at next scr refresh
                    Blank_R.setAutoDraw(False)
            
            # *OldImage* updates
            if OldImage.status == NOT_STARTED and frameN >= fixationtime:
                # keep track of start time/frame for later
                OldImage.frameNStart = frameN  # exact frame index
                OldImage.tStart = t  # local t and not account for scr refresh
                OldImage.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(OldImage, 'tStartRefresh')  # time at next scr refresh
                OldImage.setAutoDraw(True)
            if OldImage.status == STARTED:
                if frameN >= (fixationtime+testtime+respwait):
                    # keep track of stop time/frame for later
                    OldImage.tStop = t  # not accounting for scr refresh
                    OldImage.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(OldImage, 'tStopRefresh')  # time at next scr refresh
                    OldImage.setAutoDraw(False)
            
            # *NewImage* updates
            if NewImage.status == NOT_STARTED and frameN >= fixationtime:
                # keep track of start time/frame for later
                NewImage.frameNStart = frameN  # exact frame index
                NewImage.tStart = t  # local t and not account for scr refresh
                NewImage.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(NewImage, 'tStartRefresh')  # time at next scr refresh
                NewImage.setAutoDraw(True)
            if NewImage.status == STARTED:
                if frameN >= (fixationtime+testtime+respwait):
                    # keep track of stop time/frame for later
                    NewImage.tStop = t  # not accounting for scr refresh
                    NewImage.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(NewImage, 'tStopRefresh')  # time at next scr refresh
                    NewImage.setAutoDraw(False) 
            

            # *FixImage3* updates
            if FixImage3.status == NOT_STARTED and frameN >= 0:
                # keep track of start time/frame for later
                FixImage3.frameNStart = frameN  # exact frame index
                FixImage3.tStart = t  # local t and not account for scr refresh
                FixImage3.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(FixImage3, 'tStartRefresh')  # time at next scr refresh
                FixImage3.setAutoDraw(True)
            if FixImage3.status == STARTED:
                if frameN >= (FixImage3.frameNStart + fixationtime+testtime):
                    # keep track of stop time/frame for later
                    FixImage3.tStop = t  # not accounting for scr refresh
                    FixImage3.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(FixImage3, 'tStopRefresh')  # time at next scr refresh
                    FixImage3.setAutoDraw(False)
            # *qmark* updates
            if qmark.status == NOT_STARTED and frameN >= fixationtime+testtime:
                # keep track of start time/frame for later
                qmark.frameNStart = frameN  # exact frame index
                qmark.tStart = t  # local t and not account for scr refresh
                qmark.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(qmark, 'tStartRefresh')  # time at next scr refresh
                qmark.setAutoDraw(True)
            if qmark.status == STARTED:
                if frameN >= (qmark.frameNStart+respwait):
                    # keep track of stop time/frame for later
                    qmark.tStop = t  # not accounting for scr refresh
                    qmark.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(qmark, 'tStopRefresh')  # time at next scr refresh
                    qmark.setAutoDraw(False)
                    
            # *stimtrak3* updates
            if stimtrak3.status == NOT_STARTED and frameN >= fixationtime:
                # keep track of start time/frame for later
                stimtrak3.frameNStart = frameN  # exact frame index
                stimtrak3.tStart = t  # local t and not account for scr refresh
                stimtrak3.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(stimtrak3, 'tStartRefresh')  # time at next scr refresh
                stimtrak3.setAutoDraw(True)
            if stimtrak3.status == STARTED:
                if frameN >= (stimtrak3.frameNStart + 1):
                    # keep track of stop time/frame for later
                    stimtrak3.tStop = t  # not accounting for scr refresh
                    stimtrak3.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(stimtrak3, 'tStopRefresh')  # time at next scr refresh
                    stimtrak3.setAutoDraw(False)
            
                    
            # *Resp1* updates
            waitOnFlip = False
            if Resp1.status == NOT_STARTED and frameN >= fixationtime+testtime:
                # keep track of start time/frame for later
                Resp1.frameNStart = frameN  # exact frame index
                Resp1.tStart = t  # local t and not account for scr refresh
                Resp1.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(Resp1, 'tStartRefresh')  # time at next scr refresh
                Resp1.status = STARTED
                # keyboard checking is just starting
                waitOnFlip = True
                win.callOnFlip(Resp1.clock.reset)  # t=0 on next screen flip
                win.callOnFlip(Resp1.clearEvents, eventType='keyboard')  # clear events on next screen flip
            if Resp1.status == STARTED:
                if frameN >= (Resp1.frameNStart + respwait):
                    # keep track of stop time/frame for later
                    Resp1.tStop = t  # not accounting for scr refresh
                    Resp1.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(Resp1, 'tStopRefresh')  # time at next scr refresh
                    if sessionType == 'main':
                        el_tracker.sendMessage('SYNC %d' % trigger_noanswer1)
                        parallel.setData(trigger_noanswer1)
                        core.wait(0.005)
                        parallel.setData(0)
                    Resp1.status = FINISHED
            if Resp1.status == STARTED and not waitOnFlip:
                theseKeys = Resp1.getKeys(keyList=buttons, waitRelease=False)
                if len(theseKeys):
                    theseKeys = theseKeys[0]   # at least one key was pressed
                    
                    # check for quit:
                    if "escape" == theseKeys:
                        endExpNow = True
                    Resp1.keys = theseKeys.name  # just the last key pressed
                    Resp1.rt = theseKeys.rt
                    #RESPONSE TRIGGER FOR EEG & eye-tracker:
                    if sessionType=='main':
                        el_tracker.sendMessage('SYNC %d'%trigger_resp1) #EEG trigger message to eye-tracker
                        parallel.setData(trigger_resp1)
                        core.wait(0.005)
                        parallel.setData(0)
                    # a response ends the routine
                    continueRoutine = False

            
            # check for quit (typically the Esc key)
            if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
                core.quit()
            
            # check if all components have finished
            if not continueRoutine:  # a component has requested a forced-end of Routine
                break
            continueRoutine = False  # will revert to True if at least one component still running
            for thisComponent in CategorPhaseComponents:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()
        
        # -------Ending Routine "TestPhase"-------

        print(t_6-t_5)
        print(fr_6-fr_5)

        if (Resp1.keys==buttons[0]):
            ANSWER='LEFT'
        elif (Resp1.keys==buttons[1]):
            ANSWER='RIGHT'
        else:
            ANSWER='NoAnswer'
        
        if (ANSWER==target_loc):
            CORANS='CORRECT'
        if (ANSWER!=target_loc):
            CORANS='INCORRECT'
        if (ANSWER=='NoAnswer'):
            CORANS='NO ANSWER'
        
        for thisComponent in CategorPhaseComponents:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        
        c+=1 #go to next pictures
        
        #Update the counter of correct answers
        if CORANS=='CORRECT':
            CorCount1+=1
            categorization_correct+=1
        else:
            CorCount1+=0
            
        categorization_trials+=1
        block_categorization_accuracy=int(round((100 * CorCount1 / c), 0))
        cumulative_categorization_accuracy = int(round((100 * categorization_correct / categorization_trials), 0))
        
        print("Answer: {}, Running correct: {}%".format(CORANS, int(round(100*CorCount1/c,0))))
        print("Block Accuracy: {}%, Cumulative categorization Accuracy: {}%".format(block_categorization_accuracy, cumulative_categorization_accuracy))
        
        #quit the loop when the test list is finished
        ## if k>=len(testseq):
        ##    test.finished=True
        ## else:
        ##    test.finished=False
            
        
        #Save data:
        cate_test.addData('Cate_OLDITEM',old_image) #which target picture was shown
        cate_test.addData('OLDITEM_CATEGORY',cate_dict['old_category'])
        cate_test.addData('Cate_NEWITEM',new_image) #which foil picture was shown
        cate_test.addData('NEWITEM_CATEGORY',cate_dict['new_category'])
        cate_test.addData('Cate_CONDITION',condition1) #old or new as a target
        cate_test.addData('Cate_SETSIZE',setsize) #old or new as a target
        cate_test.addData('Cate_Trial#',c) #Trial order in this block
        cate_test.addData('TOTALTRIAL',absnum) #Absolute trial order
        if sessionType=='main':
            cate_test.addData('EPOCH',epochnum) #EEG epoch number (only for main blocks)
            cate_test.addData('EEGtrigger',trigger_cate) 
        cate_test.addData('PHASE',phase) #Mark Study phase
        cate_test.addData('Cate_SESSIONTYPE',sessionType) # which session type it was
        cate_test.addData('Cate_TARGET_LOC',target_loc) #target location (left or right)
        cate_test.addData('Cate_ANSWER',ANSWER) #mark answer as "red" or "blue"
        cate_test.addData('Cate_CORRECT',CORANS) #mark whether an answer was correct or not
        cate_test.addData('BLOCK_CATEGORIZATION_ACCURACY', block_categorization_accuracy)
        cate_test.addData('CUMULATIVE_CATEGORIZATION_ACCURACY', cumulative_categorization_accuracy)

        #Add participants and experiment metadata
        cate_test.addData('ID', gui.data[0])
        cate_test.addData('Age', gui.data[1])
        cate_test.addData('Gender', gui.data[2])
        cate_test.addData('Handedness', gui.data[3])
        cate_test.addData('COND_SEQUENCE', gui.data[4])
        # check responses
        if Resp1.keys in ['', [], None]:  # No response was made
            Resp1.keys = None
        cate_test.addData('Cate_Resp1.keys',Resp1.keys)
        if Resp1.keys != None:  # we had a response
            cate_test.addData('Cate_Resp1.rt', Resp1.rt)
        cate_test.addData('Cate_Resp1.started', Resp1.tStartRefresh)
        cate_test.addData('Cate_Resp1.stopped', Resp1.tStopRefresh)
        # the Routine "TestPhase" was not non-slip safe, so reset the non-slip timer
        routineTimer.reset()
        thisExp.nextEntry()
        
        # Put tracker in Offline mode / Pause eye-tracking
        el_tracker.setOfflineMode()

        # Clear the Host PC screen and wait for 500 ms
        el_tracker.sendCommand('clear_screen 0')
        
        
    
        # ------Prepare to start Routine "NextTrial"-------
        win.mouseVisible=False
        
        # update component parameters for each repeat
        # No corrective feedback during categorization
        fbtime = 0
        fb_msg = ''
        
        gotoTrial.keys = []
        gotoTrial.rt = []
        # keep track of which components have finished
        NextTrialComponents = [BlankScreen_L,BlankScreen_R,fbFrame,feedback,gotoTrial]
        for thisComponent in NextTrialComponents:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        NextTrialClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip;may be a potential coding error: should be NextTrialClock.reset(-_timeToFirstFrame)
        frameN = -1
        continueRoutine = True
        
        # -------Run Routine "NextTrial"-------
        while continueRoutine:
            # get current time
            t = NextTrialClock.getTime()
            tThisFlip = win.getFutureFlipTime(clock=NextTrialClock)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            # No correctness feedback; only the next-trial prompt
            fb_message = 'Press SPACE for the next trial'
            fb_textsize = 20
            
            if c == setsize:
                continueRoutine = False
            
            # *BlankScreen_L* updates
            if BlankScreen_L.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                BlankScreen_L.frameNStart = frameN  # exact frame index
                BlankScreen_L.tStart = t  # local t and not account for scr refresh
                BlankScreen_L.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(BlankScreen_L, 'tStartRefresh')  # time at next scr refresh
                BlankScreen_L.setAutoDraw(True)
              
            # *BlankScreen_R* updates
            if BlankScreen_R.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                BlankScreen_R.frameNStart = frameN  # exact frame index
                BlankScreen_R.tStart = t  # local t and not account for scr refresh
                BlankScreen_R.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(BlankScreen_R, 'tStartRefresh')  # time at next scr refresh
                BlankScreen_R.setAutoDraw(True)
                
            # *fbFrame* updates
            if fbFrame.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                fbFrame.frameNStart = frameN  # exact frame index
                fbFrame.tStart = t  # local t and not account for scr refresh
                fbFrame.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(fbFrame, 'tStartRefresh')  # time at next scr refresh
                fbFrame.setAutoDraw(True)
            
            # *feedback* updates
            if feedback.status == NOT_STARTED and frameN >= 0:
                # keep track of start time/frame for later
                feedback.frameNStart = frameN  # exact frame index
                feedback.tStart = t  # local t and not account for scr refresh
                feedback.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(feedback, 'tStartRefresh')  # time at next scr refresh
                feedback.setAutoDraw(True)
            if feedback.status == STARTED:  # only update if drawing
                feedback.setText(fb_message, log=False)
                feedback.setHeight(fb_textsize, log=False)
                
            # *gotoTrial* updates
            waitOnFlip = False
            if gotoTrial.status == NOT_STARTED and frameN >= fbtime:
                # keep track of start time/frame for later
                gotoTrial.frameNStart = frameN  # exact frame index
                gotoTrial.tStart = t  # local t and not account for scr refresh
                gotoTrial.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(gotoTrial, 'tStartRefresh')  # time at next scr refresh
                gotoTrial.status = STARTED
                # keyboard checking is just starting
                waitOnFlip = True
                win.callOnFlip(gotoTrial.clock.reset)  # t=0 on next screen flip
                win.callOnFlip(gotoTrial.clearEvents, eventType='keyboard')  # clear events on next screen flip
            if gotoTrial.status == STARTED and not waitOnFlip:
                theseKeys = gotoTrial.getKeys(keyList=['space'], waitRelease=False)
                if len(theseKeys):
                    theseKeys = theseKeys[0]  # at least one key was pressed
                    
                    # check for quit:
                    if "escape" == theseKeys:
                        endExpNow = True
                    gotoTrial.keys = theseKeys.name  # just the last key pressed
                    gotoTrial.rt = theseKeys.rt
                    # a response ends the routine
                    continueRoutine = False
                    
            # check for quit (typically the Esc key)
            if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
                core.quit()
            
            # check if all components have finished
            if not continueRoutine:  # a component has requested a forced-end of Routine
                break
            continueRoutine = False  # will revert to True if at least one component still running
            for thisComponent in NextTrialComponents:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()
        
        # -------Ending Routine "NextTrial"-------
        
        for thisComponent in NextTrialComponents:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        
        #quit the loop when the test list is finished
        if c>=len(cate_lst):
            cate_test.finished=True
        else:
            cate_test.finished=False
            
        #old_image=picture_old.replace(pth,'')
        #new_image=picture_old.replace(pth,'')
        
        # check responses
        if gotoTrial.keys in ['', [], None]:  # No response was made
            gotoTrial.keys = None

        # the Routine "NextTrial" was not non-slip safe, so reset the non-slip timer
        routineTimer.reset()
        thisExp.nextEntry()
        
    # completed 200 repeats of 'test'
    
    # ------Prepare to start Routine "TechnicalBreak"-------
    win.mouseVisible=False
    # update component parameters for each repeat
    
    ##el_tracker.doTrackerSetup()
    ##el_tracker.setOfflineMode()
    ##el_tracker.startRecording(1, 1, 1, 1)
    
    
    #Record file with presented pictures
    #create file name to save stimulus data
    stimdata=file_currentseq
    

    # Buttons allowing the experimenter to switch blocks
    if sessionType=='practice':
        print('')
        print('REMINDER')
        print('press {} for more practice'.format('P'))
        print('press {} for the main block'.format('T'))
        nextblockButtons=['p','t'] # 'p' for another practice, 't' for main
    else:
        print('press {} for the next block'.format('T'))
        nextblockButtons=['t'] # only 't' can be used to switch blocks in the main session
    
    
    #Text
    ii=i+1
    
    test_accuracy = int(round(100 * CorCount / k, 0))
    cate_accuracy = int(round(100 * CorCount1 / c, 0))
    
    if sessionType == 'main' and session_block_count == maxblocks - 1:
        instr_msg = (
            '{} block {} is finished.\n\n'
            'Memory test: {}% correct\n'
            'Categorization test: {}% correct\n\n'
            'You are done with this part. '
            'Please carefully READ THE INSTRUCTION ON THE NEXT SCREEN!\n\n'
            'Wait for the experimenter'
            )

    else:
        instr_msg = (
            '{} block {} is finished.\n\n'
            'Memory test: {}% correct\n'
            'Categorization test: {}% correct\n\n'
            'Wait for the experimenter'
            )
    if sessionType=='main':
        msg_sessiontype='Main'
    else:
        msg_sessiontype='Practice'
    instr_msg_upd = instr_msg.format(msg_sessiontype,session_block_count + 1,test_accuracy,cate_accuracy)
    instrcolor=(1,1,1)
    instrpos=(0,0)
    instrsize=30
    blockclear.setText(instr_msg_upd)
    blockclear.setColor(instrcolor, colorSpace='rgb')
    blockclear.setPos(instrpos)
    blockclear.setSize(instrsize) #may be the argument should be instrsize instead of instrpos
    
    AllowContinue.keys = []
    AllowContinue.rt = []
    # keep track of which components have finished
    TechnicalBreakComponents = [blockclear, AllowContinue]
    for thisComponent in TechnicalBreakComponents:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    TechnicalBreakClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip
    frameN = -1
    continueRoutine = True
    
    # -------Run Routine "TechnicalBreak"-------
    while continueRoutine:
        # get current time
        t = TechnicalBreakClock.getTime()
        tThisFlip = win.getFutureFlipTime(clock=TechnicalBreakClock)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        if session_block_count>=maxblocks:
            sessionCount+=1
            session_block_count=0
        
        # *blockclear* updates
        if blockclear.status == NOT_STARTED and frameN >= 0.0:
            # keep track of start time/frame for later
            blockclear.frameNStart = frameN  # exact frame index
            blockclear.tStart = t  # local t and not account for scr refresh
            blockclear.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(blockclear, 'tStartRefresh')  # time at next scr refresh
            blockclear.setAutoDraw(True)
        
        # *AllowContinue* updates
        waitOnFlip = False
        if AllowContinue.status == NOT_STARTED and frameN >= 0.0:
            # keep track of start time/frame for later
            AllowContinue.frameNStart = frameN  # exact frame index
            AllowContinue.tStart = t  # local t and not account for scr refresh
            AllowContinue.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(AllowContinue, 'tStartRefresh')  # time at next scr refresh
            AllowContinue.status = STARTED
            # keyboard checking is just starting
            waitOnFlip = True
            win.callOnFlip(AllowContinue.clock.reset)  # t=0 on next screen flip
            win.callOnFlip(AllowContinue.clearEvents, eventType='keyboard')  # clear events on next screen flip
        if AllowContinue.status == STARTED and not waitOnFlip:
            theseKeys = AllowContinue.getKeys(keyList=nextblockButtons, waitRelease=False) # recall that nextblockButtons is either 't' or 't' and 'p' in a list
            if len(theseKeys):
                theseKeys = theseKeys[0]  # at least one key was pressed
                
                # check for quit:
                if "escape" == theseKeys:
                    endExpNow = True
                AllowContinue.keys = theseKeys.name  # just the last key pressed
                AllowContinue.rt = theseKeys.rt
                # a response ends the routine
                continueRoutine = False
        
        # check for quit (typically the Esc key)
        if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
            core.quit()
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in TechnicalBreakComponents:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # -------Ending Routine "TechnicalBreak"-------
    for thisComponent in TechnicalBreakComponents:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # check responses
    if AllowContinue.keys in ['', [], None]:  # No response was made
        AllowContinue.keys = None
    # the Routine "TechnicalBreak" was not non-slip safe, so reset the non-slip timer
    
    # Counter updates
    if sessionType=='practice':
        if AllowContinue.keys=='t':
            sessionCount+=1
            session_block_count=0
        if AllowContinue.keys=='p':
            sessionCount+=0
            session_block_count+=1
    if sessionType=='main':
        if AllowContinue.keys=='t':
            sessionCount+=0
            session_block_count+=1
    if session_block_count>=maxblocks:
        sessionCount+=1
        session_block_count=0
        
    
    routineTimer.reset()
    
    
    # ------Prepare to start Routine "switchblock"-------
    win.mouseVisible=False 
    # update component parameters for each repeat
    # keep track of which components have finished
    switchblockComponents = []
    for thisComponent in switchblockComponents:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    switchblockClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip
    frameN = -1
    continueRoutine = True
    
    # -------Run Routine "switchblock"-------
    while continueRoutine:
        # get current time
        t = switchblockClock.getTime()
        tThisFlip = win.getFutureFlipTime(clock=switchblockClock)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # check for quit (typically the Esc key)
        if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
            core.quit()
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in switchblockComponents:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    if event.getKeys('q'):
        continueRoutine=False # may be accidentally added one more '='
    else:
        continueRoutine=True
    
    # -------Ending Routine "switchblock"-------
    for thisComponent in switchblockComponents:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    lastimage1=images1[len(images1)-1] #what was the last image in this block list
    # Update the index of the last shown image to start the new block with the next on the list
    if sessionType=='practice':
        lastindex_prac+=len(images1) #Each block moves the start position forward by the images it used
    if sessionType=='main':
        lastindex=allimages1.index(lastimage1) #what number the last image has in the entire list of images
    
    i+=1 #go to next block
    
    # the Routine "switchblock" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()
    thisExp.nextEntry()
    
    # EYE-TRACKER CALIBRATION FOR THE NEXT BLOCK IF NEEDED (JUST PRESS "O" IF YOU WANT TO SKIP)
    print("For eye-tracker calibration, press C. To skip calibration, press O")
    el_tracker.doTrackerSetup()

    # put tracker in idle/offline mode before recording
    el_tracker.setOfflineMode()

    
    if sessionCount>=len(sessions):
        WholeExp.finished=True
# completed nblocks repeats of 'WholeExp'


# ------Prepare to start Routine "End"-------
win.mouseVisible=False
# update component parameters for each repeat
# ### Eyetracking message and EEG final trigger for synchronization
el_tracker.sendMessage('SYNC %d' % 200 )
parallel.setData(200)
core.wait(0.005)
parallel.setData(0)

#Stop eye-tracker recording
terminate_recording()


PressToFinish.keys = []
PressToFinish.rt = []
# keep track of which components have finished
EndComponents = [finishExp, PressToFinish]
for thisComponent in EndComponents:
    thisComponent.tStart = None
    thisComponent.tStop = None
    thisComponent.tStartRefresh = None
    thisComponent.tStopRefresh = None
    if hasattr(thisComponent, 'status'):
        thisComponent.status = NOT_STARTED
# reset timers
t = 0
_timeToFirstFrame = win.getFutureFlipTime(clock="now")
EndClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip
frameN = -1
continueRoutine = True

# -------Run Routine "End"-------
while continueRoutine:
    # get current time
    t = EndClock.getTime()
    tThisFlip = win.getFutureFlipTime(clock=EndClock)
    tThisFlipGlobal = win.getFutureFlipTime(clock=None)
    frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
    # update/draw components on each frame
    
    # *finishExp* updates
    if finishExp.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
        # keep track of start time/frame for later
        finishExp.frameNStart = frameN  # exact frame index
        finishExp.tStart = t  # local t and not account for scr refresh
        finishExp.tStartRefresh = tThisFlipGlobal  # on global time
        win.timeOnFlip(finishExp, 'tStartRefresh')  # time at next scr refresh
        finishExp.setAutoDraw(True)
    
    # *PressToFinish* updates
    waitOnFlip = False
    if PressToFinish.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
        # keep track of start time/frame for later
        PressToFinish.frameNStart = frameN  # exact frame index
        PressToFinish.tStart = t  # local t and not account for scr refresh
        PressToFinish.tStartRefresh = tThisFlipGlobal  # on global time
        win.timeOnFlip(PressToFinish, 'tStartRefresh')  # time at next scr refresh
        PressToFinish.status = STARTED
        # keyboard checking is just starting
        waitOnFlip = True
        win.callOnFlip(PressToFinish.clock.reset)  # t=0 on next screen flip
        win.callOnFlip(PressToFinish.clearEvents, eventType='keyboard')  # clear events on next screen flip
    if PressToFinish.status == STARTED and not waitOnFlip:
        theseKeys = PressToFinish.getKeys(keyList=['space'], waitRelease=False)
        if len(theseKeys):
            theseKeys = theseKeys[0]  # at least one key was pressed
            
            # check for quit:
            if "escape" == theseKeys:
                endExpNow = True
            PressToFinish.keys = theseKeys.name  # just the last key pressed
            PressToFinish.rt = theseKeys.rt
            # a response ends the routine
            continueRoutine = False
    
    # check for quit (typically the Esc key)
    if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
        core.quit()
    
    # check if all components have finished
    if not continueRoutine:  # a component has requested a forced-end of Routine
        break
    continueRoutine = False  # will revert to True if at least one component still running
    for thisComponent in EndComponents:
        if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
            continueRoutine = True
            break  # at least one component has not yet finished
    
    # refresh the screen
    if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
        win.flip()

# -------Ending Routine "End"-------
for thisComponent in EndComponents:
    if hasattr(thisComponent, "setAutoDraw"):
        thisComponent.setAutoDraw(False)
thisExp.addData('finishExp.started', finishExp.tStartRefresh)
thisExp.addData('finishExp.stopped', finishExp.tStopRefresh)
# check responses
if PressToFinish.keys in ['', [], None]:  # No response was made
    PressToFinish.keys = None
thisExp.addData('PressToFinish.keys',PressToFinish.keys)
if PressToFinish.keys != None:  # we had a response
    thisExp.addData('PressToFinish.rt', PressToFinish.rt)
thisExp.addData('PressToFinish.started', PressToFinish.tStartRefresh)
thisExp.addData('PressToFinish.stopped', PressToFinish.tStopRefresh)
thisExp.nextEntry()
# the Routine "End" was not non-slip safe, so reset the non-slip timer
routineTimer.reset()

# Flip one final time so any remaining win.callOnFlip() 
# and win.timeOnFlip() tasks get executed before quitting
win.flip()

# these shouldn't be strictly necessary (should auto-save)
thisExp.saveAsWideText(filename+'.csv')
thisExp.saveAsPickle(filename)
logging.flush()

# close the log file
logFile.close()

# make sure everything is closed down
thisExp.abort()  # or data files will save again on exit
win.close()
core.quit()

##### EEG TRIGGERS:

## 100, 200 - recording start and finish

## STUDY stimulus onset: 1
## 99 - study stimulus offset

## RECOGNITION stimulus onset: 2
## RECOGNITION response window onset: 199
## RECOGNITION response time offset: 21

## CATEGORIZATION stimulus onset: 3
## CATEGORIZATION response window onset: 199
## CATEGORIZATION response time offset: 31


## 199 - response window begins
## 222 - test trial ended with no response
## 223 - categorization trial ended with no response
