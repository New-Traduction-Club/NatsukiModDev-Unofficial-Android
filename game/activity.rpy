default persistent._jn_activity_used_programs = []

init python in jn_activity:
    from Enum import Enum
    from plyer import notification
    import sys
    import random
    import re
    import store
    import store.jn_globals as jn_globals
    import store.jn_utils as jn_utils

    ACTIVITY_SYSTEM_ENABLED = True # Determines if the system supports activity detection
    LAST_ACTIVITY = None

    if renpy.windows:
        from plyer import notification
        import pygetwindow
        sys.path.append(renpy.config.gamedir + '\\python-packages\\')
        import win32api
        import win32gui

    elif renpy.linux:
        import os

        #NOTE: On linux, there are different types of desktop sessions. Xlib will ONLY work with X11 sessions.
        if (os.environ.get('DISPLAY') is None) or (os.environ.get('DISPLAY') == ''):
            store.jn_utils.log("DISPLAY is not set. Cannot use Xlib.")
            #Set a flag indicating this should be disabled.
            ACTIVITY_SYSTEM_ENABLED = False

        else:
            import Xlib
            import Xlib.display

    elif renpy.macintosh:
        ACTIVITY_SYSTEM_ENABLED = False

    class JNWindowFoundException(Exception):
        """
        Custom exception; used to break out of the win32gui.EnumWindows method while still returning a value,
        as only that and returning False are valid means of termination.
        """
        def __init__(self, hwnd):
            self.hwnd = hwnd

        def __str__(self):
            return self.hwnd

    class JNActivities(Enum):
        unknown = 0
        coding = 1
        discord = 2
        music_applications = 3
        gaming  = 4
        youtube = 5
        github_jn = 6
        artwork = 7
        anime_streaming = 8
        work_applications = 9
        twitter = 10
        deviantart = 11
        manga = 12
        ddlc_moe = 13
        takeaway_food = 14
        instagram = 15
        music_creation = 16
        reddit = 17
        fourchan = 18
        monika_after_story = 19
        just_yuri = 20
        forever_and_ever = 21
        video_applications = 22
        e_commerce = 23
        recording_software = 24

        def __int__(self):
            return self.value

    class JNPlayerActivity:
        """
        This class represents some activity a player can be doing, outside of JN, to be used in notifications/dialogue.
        """
        def __init__(
            self,
            activity_type,
            window_name_regex=None,
            notify_text=None
        ):
            """
            Initialises a new instance of JNPlayerActivity.

            IN:
                - activity_type - The JNActivities type of this JNPlayerActivity
                - window_name_regex - The window regex that must be matched for this activity to be the current activity
                - notify_text - List of text Natsuki may react with via popup, if this activity is detected
            """
            self.activity_type = activity_type
            self.window_name_regex = window_name_regex
            self.notify_text = notify_text

        def getRandomNotifyText(self):
            """
            Returns the substituted reaction text for this activity.
            """
            if self.notify_text and len(self.notify_text) > 0:
                store.happy_emote = jn_utils.getRandomHappyEmoticon()
                store.angry_emote = jn_utils.getRandomAngryEmoticon()
                store.sad_emote = jn_utils.getRandomSadEmoticon()
                store.tease_emote = jn_utils.getRandomTeaseEmoticon()
                store.confused_emote = jn_utils.getRandomConfusedEmoticon()
                return renpy.substitute(random.choice(self.notify_text))

            return None

    class JNActivityManager:
        """
        Management class for handling activities.
        """
        def __init__(self):
            self.registered_activities = {}
            self.last_activity = JNPlayerActivity(
                activity_type=JNActivities.unknown
            )
            self.__enabled = False

        def setIsEnabled(self, state):
            """
            Sets the enabled state, determining if activity detection is active.

            IN:
                - state - bool enabled state to set
            """
            self.__enabled = state

        def getIsEnabled():
            """
            Gets the enabled state.
            """
            return self.__enabled

        def registerActivity(self, activity):
            self.registered_activities[activity.activity_type] = activity

        def getActivityFromType(self, activity_type):
            """
            Returns the activity corresponding to the given JNActivities activity type, or None if it doesn't exist
            """
            if activity_type in self.registered_activities:
                return self.registered_activities[activity_type]

            return None

        def getCurrentActivity(self, delay=0):
            """
            Returns the current JNActivities state of the player as determined by the currently active window,
            and if the activity is registered.

            IN:
                - delay - Force RenPy to sleep before running the check. This allows time to swap windows from JN for debugging.
            OUT:
                - JNPlayerActivity type for the active window, or None
            """
            if delay is not 0:
                store.jnPause(delay, hard=True)

            if not self.__enabled:
                return self.getActivityFromType(JNActivities.unknown)

            window_name = getCurrentWindowName()
            if window_name is not None:
                window_name = getCurrentWindowName().lower()
                for activity in self.registered_activities.values():
                    if activity.window_name_regex:
                        if re.search(activity.window_name_regex, window_name) is not None:

                            if not self.hasPlayerDoneActivity(int(activity.activity_type)):
                                store.persistent._jn_activity_used_programs.append(int(activity.activity_type))

                            return activity

            return self.getActivityFromType(JNActivities.unknown)

        def hasPlayerDoneActivity(self, activity_type):
            """
            Returns True if the player has previously partook in the given activity.

            IN:
                - activity - The JNActivities activity to check
            """
            return int(activity_type) in store.persistent._jn_activity_used_programs

    ACTIVITY_MANAGER = JNActivityManager()

    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.unknown
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.coding,
        window_name_regex="(- visual studio|- notepad/+/+|- atom|- brackets|vim|eclipse|^github desktop$|^sourcetree$|- scratch)",
        notify_text=[
            __("You're seriously such a nerd, [player]."),
            __("You forgot a semicolon! [tease_emote]"),
            __("How do you even read all that stuff?!"),
            __("Well? Does it work? [tease_emote]"),
            __("What even IS that mumbo-jumbo..."),
            __("I don't even know where I'd start with coding stuff..."),
            __("More programming stuff?"),
            __("I see, I see. You're on nerd duty today! [tease_emote]"),
        ]
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.discord,
        window_name_regex="(- discord)",
        notify_text=[
            __("Someone's a social butterfly, huh?"),
            __("Yeah, yeah. Chat it up, [player]~"),
            __("Man... I wish I had some emotes... [sad_emote]"),
            __("Maybe I should start a server..."),
            __("Huh? Did someone message you?"),
            __("Eh? Did someone just ping you? [confused_emote]"),
            __("Don't just spend all day yapping away on there! [angry_emote]"),
            __("I'm not THAT boring to talk to, am I? [sad_emote]"),
        ]
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.music_applications,
        window_name_regex="(^spotify$|^spotify premium$|^groove$|^zune$|^itunes$|^musicbee$|^aimp$|^winamp$)",
        notify_text=[
            __("You better play something good!"),
            __("New playlist, [player]?"),
            __("Play some tunes, [player]!"),
            __("When do I get to pick something, huh? [angry_emote]"),
            __("Hit it, [player]! [tease_emote]"),
        ]
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.gaming,
        window_name_regex="(^steam$|^origin$|^battle.net$|- itch.io)",
        notify_text=[
            __("You better not be spending all day on that! [angry_emote]"),
            __("Just... remember to take breaks, alright? [sad_emote]"),
            __("Gonna play something?"),
            __("You could have just said if you were bored... [sad_emote]"),
            __("You better not play anything weird..."),
            __("Game time, huh?"),
        ]
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.youtube,
        window_name_regex="(- youtube)",
        notify_text=[
            __("YouTube, huh? I think Sayori uploaded something once..."),
            __("Oh! Oh! Let me watch! [happy_emote]"),
            __("What's on, [player]?"),
            __("You better not be watching anything weird..."),
            __("Just... no reaction videos. Please. [angry_emote]"),
        ]
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.github_jn,
        window_name_regex="(just-natsuki-team/natsukimoddev)",
        notify_text=[
            __("Hey! I know this place!"),
            __("I knew you'd help me out! Ehehe."),
            __("Oh! Oh! It's my website!"),
            __("I heard only complete nerds come here... [tease_emote]"),
            __("Ehehe. Thanks for stopping by!"),
            "Hey! It's geek-hub! [tease_emote]",
        ]
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.artwork,
        window_name_regex="(clip studio paint|photoshop|krita|gimp|paint.net|paint tool sai|medibang|- paint)",
        notify_text=[
            __("Draw for me, [player]! Ehehe."),
            __("I was never any good at artwork... [sad_emote]"),
            __("You're drawing? [confused_emote]"),
            __("Oh! Oh! What're you drawing?"),
            __("Eh? What're you drawing? [confused_emote]"),
            __("Draw me! Draw me!!"),
        ]
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.anime_streaming,
        window_name_regex="(^crunchyroll$)",
        notify_text=[
            __("What's the flavor of the month?"),
            __("So many options..."),
            __("I still don't see Parfait Girls anywhere..."),
            __("Infinite choices! Ehehe."),
            __("I could waste DAYS here... [confused_emote]"),
        ]
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.work_applications,
        window_name_regex="(- word| - excel| - powerpoint|openoffice|libreoffice)",
        notify_text=[
            __("Ew... work..."),
            __("You're sure you gotta do this now, [player]? [confused_emote]"),
            __("Ugh... reminds me of my school assignments..."),
            __("Great... now I'm getting flashbacks of my group projects."),
            __("Booo-ring! Ehehe."),
            __("Reminds me of schoolwork... [angry_emote]"),
        ]
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.twitter,
        window_name_regex="(/ twitter)",
        notify_text=[
            __("There's so much cool art here!"),
            __("I swear I could waste hours just scrolling here..."),
            __("Oh! Oh! Am I trending?"),
            __("I should probably check my Twitter, huh?"),
            __("Oh man! I gotta check on my feed! [confused_emote]"),
        ]
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.deviantart,
        window_name_regex="(deviantart - |\| deviantart)",
        notify_text=[
            __("So. Much. Art."),
            __("Oh! Do you post here, [player]?"),
            __("Just... don't search up anything weird..."),
            __("I... know this place."),
        ]
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.manga,
        window_name_regex="(- mangadex|- mangasee|- mangakot)",
        notify_text=[
            __("What's the flavor of the month?"),
            __("No Parfait Girls here... [sad_emote]"),
            __("Oh! What're you reading? [happy_emote]"),
            __("Looking for an EXPERT opinion? Ehehe."),
        ]
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.ddlc_moe,
        window_name_regex="(doki doki literature club! -)",
        notify_text=[
            "...",
            __("I... don't like this website."),
            __("Uuuuuu... do you HAVE to visit this place?"),
        ]
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.takeaway_food,
        window_name_regex=(
            "((uber eats[a-zA-Z]*| food delivery)|( - uber eats)|(deliveroo - takeaway food delivery)"
            "|(\| domino's pizza)|(\| pizza hut)|(\| grubhub)|(doordash food delivery & takeout -))"
        ),
        notify_text=[
            __("H-hey! Less of the junk! [angry_emote]"),
            __("Cooking isn't THAT hard, you know... [angry_emote]"),
            __("You better not be making a habit of that..."),
            __("[player]! Think of your wallet! Jeez... [confused_emote]"),
            __("[player]... come on... [sad_emote]"),
            __("Just... don't make a habit of this. [angry_emote] Please?"),
            __("Ew... junk food..."),
        ]
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.instagram,
        window_name_regex="(• instagram photos and videos)",
        notify_text=[
            __("So who are YOU stalking, huh? [tease_emote]"),
            __("Huh? Do you post here, [player]?"),
            __("You post here much, [player]?"),
        ]
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.music_creation,
        window_name_regex="(cubase|fl studio|reaper|mixcraft|studio one|logic pro|garageband|cakewalk|pro tools)",
        notify_text=[
            __("Ooooh! You're making beats?"),
            __("Making some tunes? [confused_emote]"),
            __("...Should I start taking NOTES? Ehehe."),
            __("Oh! Oh! I GOTTA listen to this!"),
        ]
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.reddit,
        window_name_regex="(reddit - dive into anything)",
        notify_text=[
            __("I hope you don't believe everything you read..."),
            __("Eh? What's in the news?"),
            __("Huh? Did something happen?"),
            __("You making a post, [player]? [confused_emote]"),
        ]
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.fourchan,
        window_name_regex="(- 4chan|^4chan$)"
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.monika_after_story,
        window_name_regex="^monika after story$"
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.just_yuri,
        window_name_regex="(^just yuri$|^just yuri \(beta\)$)"
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.forever_and_ever,
        window_name_regex="^forever & ever$"
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.video_applications,
        window_name_regex="(- vlc media player)",
        notify_text=[
            __("What're you watching, [player]? [confused_emote]"),
            __("You watching something, [player]? [confused_emote]"),
            __("Oh hey! Any funny video clips? [tease_emote]"),
        ]
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.e_commerce,
        window_name_regex="(^amazon.[A-Za-z]{2,6}|\| ebay)",
        notify_text=[
            __("Just... don't go overboard. [angry_emote]"),
            __("Shopping, huh? [tease_emote]"),
            __("Run out of something again? Ehehe."),
            __("Oh? You gotta grab something? [confused_emote]"),
            __("Money to burn, huh?")
        ]
    ))
    ACTIVITY_MANAGER.registerActivity(JNPlayerActivity(
        activity_type=JNActivities.recording_software,
        window_name_regex="(^obs [0-9]{1,2}\.[0-9]{1,2}\.[0-9]{1,2}|^bandicam [0-9]{4}|^fraps|^xsplit broadcaster$|- lightstream studio$)",
        notify_text=[
            __("W-wait... what kind of app is that, [player]? [confused_emote]"),
            __("Wait a second... is that some kind of recorder?"),
            __("I-I hope you aren't recording me, [player]. [angry_emote]"),
            __("Huh? What kind of program is that, [player]? [confused_emote]"),
            __("What are you recording, [player]...? [confused_emote]")
        ]
    ))

    def _getJNWindowHwnd():
        """
        Gets the hwnd of the JN game window (Windows only).

        OUT:
            - int representing the hwnd of the JN game window
        """
        def checkJNWindow(hwnd, ctx):
            """
            Returns JNWindowFoundException containing the hwnd of the JN game window.
            """
            if win32gui.GetWindowText(hwnd) == store.config.window_title:
                raise JNWindowFoundException(hwnd)

        try:
            # Iterate through all windows, comparing titles to find the JN game window
            win32gui.EnumWindows(checkJNWindow, None)

        except JNWindowFoundException as exception:
            return exception.hwnd

    def getJNWindowActive():
        """
        Returns True if the currently active window is the JN game window, otherwise False.
        """
        return getCurrentWindowName() == store.config.window_title

    def getCurrentWindowName(delay=0):
        """
        Gets the title of the currently active window.

        IN:
            - delay - int amount of seconds to wait before checking window

        OUT:
            - str representing the title of the currently active window
        """
        global ACTIVITY_SYSTEM_ENABLED
        if ACTIVITY_SYSTEM_ENABLED:
            if delay is not 0:
                store.jnPause(delay, hard=True)

            try:
                if renpy.windows and pygetwindow.getActiveWindow():
                    return pygetwindow.getActiveWindow().title

                elif renpy.linux:
                    # This is incredibly messy
                    focus = Xlib.display.Display().get_input_focus().focus

                    if not isinstance(focus, int):
                        # We have a window
                        wm_name = focus.get_wm_name()
                        wm_class = focus.get_wm_class()

                        if isinstance(wm_name, basestring) and wm_name != "":
                            # Window has a name, return it
                            return wm_name

                        elif wm_class is None and (wm_name is None or wm_name == ""):
                            # Try and get the parent of the window
                            focus = focus.query_tree().parent

                            if not isinstance(focus, int):
                                # Try and get the wm_name of the parent and return that instead
                                wm_name = focus.get_wm_name()
                                return wm_name if isinstance(wm_name, basestring) else ""

                        elif isinstance(wm_class, tuple):
                            # Just return the parent name
                            return str(wm_class[0])

                        # Fall through

            except AttributeError as exception:
                ACTIVITY_SYSTEM_ENABLED = False
                jn_utils.log("Failed to identify activity: {0}; only x11 sessions are supported. Disabling activity system for session.".format(repr(exception)))
                return ""

            except Exception as exception:
                ACTIVITY_SYSTEM_ENABLED = False
                jn_utils.log("Failed to identify activity: {0}. Disabling activity system for session.".format(repr(exception)))
                return ""

        return ""

    def taskbarFlash(flash_count=2, flash_frequency_milliseconds=750):
        """
        Flashes the JN icon on the taskbar (Windows only).
        By default, the icon will flash twice with a healthy delay between each flash, before remaining lit.

        IN:
            - flash_count - The amount of times to flash the icon before the icon remains in a lit state
            - flash_frequency_milliseconds - The amount of time to wait between each flash, in milliseconds
        """
        if renpy.windows:
            win32gui.FlashWindowEx(_getJNWindowHwnd(), 6, flash_count, flash_frequency_milliseconds)

    def notifyPopup(message):
        """
        Displays a toast-style popup (Windows, Linux and Android only).

        IN:
            - title - The title to display on the window
            - message - The message to display in the window
        """
        if renpy.android:
            try:
                from jnius import autoclass
                class_name = 'org.renpy.android.NotificationWorker'.encode('utf-8')
                NotificationWorker = autoclass(class_name)

                NotificationWorker.showDesktopNotification(
                    "Natsuki",
                    message,
                    (renpy.config.gamedir + '/mod_assets/jnlogo.ico')
                )
            except Exception as e:
                try:
                    Log = autoclass('android.util.Log')
                    Log.e("RenPyNotification", "Failed to trigger desktop notification: " + str(e))
                except:
                    print("Error:", e)
        elif renpy.windows or renpy.linux:
            notification.notify(
                title="Natsuki",
                message=message,
                app_name=store.config.window_title,
                app_icon=(renpy.config.gamedir + '/mod_assets/jnlogo.ico'),
                timeout=7
            )
