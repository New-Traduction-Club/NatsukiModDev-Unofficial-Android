init 5 python:
    registerTopic(
        Topic(
            persistent._topic_database,
            label="talk_test_notification",
            unlocked=True,
            prompt="DEV: Test notification",
            category=["DEV"],
            player_says=True,
            affinity_range=None,
            location="classroom"
        ),
        topic_group=TOPIC_TYPE_NORMAL
    )

label talk_test_notification:
    $ jn_activity.notifyPopup("This is a test notification")
    return
