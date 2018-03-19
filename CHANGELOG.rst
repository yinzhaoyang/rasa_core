Change Log
==========

All notable changes to this project will be documented in this file.
This project adheres to `Semantic Versioning`_ starting with version 0.2.0.

[Unreleased 0.9.0.aX] - `master`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: This version is not yet released and is under active development.

Added
-----
- parameter to specify NLU project when instantiating a ``RasaNLUInterpreter``
- simple ``/respond`` endpoint to get bot response to a user message

Changed
-------
- updated dependency fbmessenger from 4.3.1 to 5.0.0

Removed
-------

Fixed
-----

[0.8.2] - 2018-02-13
^^^^^^^^^^^^^^^^^^^^

Added
-----
- script to reload a dumped trackers state and to continue the conversation
  at the end of the stored dialogue

Changed
-------
- minor updates to dependencies

Fixed
-----
- fixed datetime serialisation of reminder event

[0.8.1] - 2018-02-01
^^^^^^^^^^^^^^^^^^^^

Fixed
-----
- removed deque to support python 3.5
- Documentation improvements to tutorials
- serialisation of date time value for ``ReminderScheduled`` event

[0.8.0] - 2018-01-30
^^^^^^^^^^^^^^^^^^^^

This is a major version change. Make sure to take a look at the
:ref:`migration` in the documentation for advice on how to
update existing projects.

Added
-----
- ``--debug`` and ``--verbose`` flags to scripts (train.py, run.py, server.py)
  to set the log level
- support for story cycles when using checkpoints
- added a new machine learning policy `SklearnPolicy` that uses an sklearn
  classifier to predict actions (logistic regression by default)
- warn if action emits events when using a model that it did never emit in
  any of the stories the model was trained on
- support for event pushing and endpoints to retrieve the tracker state from the server
- Timestamp to every event
- added a Slack channel that allows Rasa Core to communicate via a Slack app
- added a Telegram channel that allows Rasa Core to communicate via a Telegram bot

Changed
-------
- rewrite of the whole FB connector: replaced pymessenger library with fbmessenger
- story file utterance format changed from ``* _intent_greet[name=Rasa]``
  to ``* intent_greet{"name": "Rasa"}`` (old format is still supported but
  deprecated)
- persist action names in domain during model persistence
- improved travis build speed by not using miniconda
- don't fail with an exception but with a helpful error message if an
  utterance template contains a variable that can not be filled
- domain doesn't fail on unknown actions but emits a warning instead. this is to support reading
  logs from older conversation if one recently removed an action from the domain

Fixed
-----
- proper evaluation of stories with checkpoints
- proper visualisation of stories with checkpoints
- fixed float slot min max value handling
- fixed non integer feature decoding, e.g. used for memoization policy
- properly log to specified file when starting Rasa Core server
- properly calculate offset of last reset event after loading tracker from
  tracker store
- UserUtteranceReverted action incorrectly triggered actions to be replayed


[0.7.9] - 2017-11-29
^^^^^^^^^^^^^^^^^^^^

Fixed
-----
- visualisation using Networkx version 2.x
- add output about line of failing intent when parsing story files

[0.7.8] - 2017-11-27
^^^^^^^^^^^^^^^^^^^^

Fixed
-----
- Pypi readme rendering

[0.7.7] - 2017-11-24
^^^^^^^^^^^^^^^^^^^^

Added
-----
- log bot utterances to tracker

Fixed
-----
- documentation improvements in README
- renamed interpreter argument to rasa core server

[0.7.6] - 2017-11-15
^^^^^^^^^^^^^^^^^^^^

Fixed
-----
- moodbot example train command in docs


[0.7.5] - 2017-11-14
^^^^^^^^^^^^^^^^^^^^

Changed
-------
- "sender_id" (and "DEFAULT_SENDER_ID") keyword consistency issue #56

Fixed
-----
- improved moodbot example - more nlu examples as well as better fitting of dialogue model


[0.7.4] - 2017-11-09
^^^^^^^^^^^^^^^^^^^^

Changed
-------

- added method to tracker to retrieve the latest entities #68

[0.7.3] - 2017-10-31
^^^^^^^^^^^^^^^^^^^^

Added
-----
- parameter to specify font size when rendering story visualization

Fixed
-----
- fixed documentation of story visualization

[0.7.2] - 2017-10-30
^^^^^^^^^^^^^^^^^^^^

Added
-----
- added facebook bot example
- added support for conditional checkpoints. a checkpoint can be restricted to
  only allow one to use it if certain slots are set. see docs for details
- utterance templates in domain yaml support buttons and images
- validate domain yaml and raise exception on invalid file
- ``run`` script to load models and handle messages from an input channel

Changed
-------
- small dropout in standard keras model to decrease reliance on exact intents
- a LOT of documentation improvements

Fixed
-----
- fixed http error if action listen is not confirmed. #42

[0.7.1] - 2017-10-06
^^^^^^^^^^^^^^^^^^^^

Fixed
-----
- issues with restart events. They created wrong a messed up history leading to
  wrong predictions


[0.7.0] - 2017-10-04
^^^^^^^^^^^^^^^^^^^^

Added
-----
- support for Rasa Core usage as a server with remote action execution

Changed
-------
- switched to max code line length 80
- removed action id - use ``action.name()`` instead. if an action implementation overrides the name, it should include the ``action_`` prefix (as it is not automatically added anymore)
- renamed ``rasa_dm.util`` to ``rasa_dm.utils``
- renamed the whole package to ``rasa_core`` (so ``rasa_dm`` is gone!)
- renamed ``Reminder`` attribute ``id`` to ``name``
- a lot of documentation improvements. docs are now at https://core.rasa.ai
- use hashing when writing memorized turns into persistence - requires retraining of all models that are trained with a version prior to this
- changed ``agent.handle_message(...)`` interface for easier usage

[0.6.0] - 2017-08-27
^^^^^^^^^^^^^^^^^^^^

Added
-----
- support for multiple policies (e.g. one memoization and a Keras policy at the same time)
- loading domains from yaml files instead of defining them with python code
- added an api layer (called ``Agent``) for you to use for 95% of the things you want to do (training, persistence, loading models)
- support for reminders

Changed
-------
- large refactoring of code base

[0.5.0] - 2017-06-18
^^^^^^^^^^^^^^^^^^^^

Added
-----
- ``ScoringPolicy`` added to policy implementations (less strict than standard default policy)
- ``RasaNLUInterpreter`` to run a nlu instance within dm (instead of using the http interface)
- more tests

Changed
-------
- ``UserUtterance`` now holds the complete parse data from nlu (e.g. to access attributes other than entities or intent)
- ``Turn`` has a reference to a ``UserUtterance`` instead of directly storing intent & entities (allows access to other data)
- Simplified interface of output channels
- order of actions in the DefaultPolicy in ``possible_actions`` (``ActionListen`` now always has index 0)

Fixed
-----
- ``RedisTrackerStore`` checks if tracker is stored before accessing it (otherwise a ``None`` access exception is thrown)
- ``RegexInterpreter`` checks if the regex actually matches the message instead of assuming it always does
- ``str`` implementation for all events
- ``Controller`` can be started without an input channel (e.g. messages need to be fed into the queue manually)

[0.2.0] - 2017-05-18
^^^^^^^^^^^^^^^^^^^^
First released version.


.. _`master`: https://github.com/RasaHQ/rasa_core/

.. _`Semantic Versioning`: http://semver.org/
