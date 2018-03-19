from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import glob
import json

import pytest

from rasa_core import utils
from rasa_core.actions.action import ActionListen, ACTION_LISTEN_NAME
from rasa_core.channels import UserMessage
from rasa_core.conversation import Topic
from rasa_core.domain import TemplateDomain
from rasa_core.events import (
    UserUttered, TopicSet, ActionExecuted, Restarted, ActionReverted,
    UserUtteranceReverted)
from rasa_core.featurizers import BinaryFeaturizer
from rasa_core.tracker_store import InMemoryTrackerStore, RedisTrackerStore
from rasa_core.trackers import DialogueStateTracker
from rasa_core.training import extract_trackers_from_file
from tests.conftest import DEFAULT_STORIES_FILE
from tests.utilities import tracker_from_dialogue_file, read_dialogue_file

domain = TemplateDomain.load("data/test_domains/default_with_topic.yml")


def stores_to_be_tested():
    return [RedisTrackerStore(domain, mock=True),
            InMemoryTrackerStore(domain)]


def stores_to_be_tested_ids():
    return ["redis-tracker",
            "in-memory-tracker"]


def test_tracker_duplicate():
    filename = "data/test_dialogues/inform_no_change.json"
    dialogue = read_dialogue_file(filename)
    dialogue_topics = set([Topic(t.topic)
                           for t in dialogue.events
                           if isinstance(t, TopicSet)])
    domain.topics.extend(dialogue_topics)
    tracker = DialogueStateTracker(dialogue.name, domain.slots,
                                   domain.topics, domain.default_topic)
    tracker.recreate_from_dialogue(dialogue)
    num_actions = len([event
                       for event in dialogue.events
                       if isinstance(event, ActionExecuted)])

    # There is always one duplicated tracker more than we have actions,
    # as the tracker also gets duplicated for the
    # action that would be next (but isn't part of the operations)
    assert len(list(tracker.generate_all_prior_states())) == num_actions + 1


@pytest.mark.parametrize("store", stores_to_be_tested(),
                         ids=stores_to_be_tested_ids())
def test_tracker_store_storage_and_retrieval(store):
    tracker = store.get_or_create_tracker("some-id")
    # the retrieved tracker should be empty
    assert tracker.sender_id == "some-id"

    # Action listen should be in there
    assert list(tracker.events) == [ActionExecuted(ActionListen().name())]

    # lets log a test message
    intent = {"name": "greet", "confidence": 1.0}
    tracker.update(UserUttered("/greet", intent, []))
    assert tracker.latest_message.intent.get("name") == "greet"
    store.save(tracker)

    # retrieving the same tracker should result in the same tracker
    retrieved_tracker = store.get_or_create_tracker("some-id")
    assert retrieved_tracker.sender_id == "some-id"
    assert len(retrieved_tracker.events) == 2
    assert retrieved_tracker.latest_message.intent.get("name") == "greet"

    # getting another tracker should result in an empty tracker again
    other_tracker = store.get_or_create_tracker("some-other-id")
    assert other_tracker.sender_id == "some-other-id"
    assert len(other_tracker.events) == 1


@pytest.mark.parametrize("store", stores_to_be_tested(),
                         ids=stores_to_be_tested_ids())
@pytest.mark.parametrize("filename", glob.glob('data/test_dialogues/*json'))
def test_tracker_store(filename, store):
    tracker = tracker_from_dialogue_file(filename, domain)
    store.save(tracker)
    restored = store.retrieve(tracker.sender_id)
    assert restored == tracker


def test_tracker_write_to_story(tmpdir, default_domain):
    tracker = tracker_from_dialogue_file(
            "data/test_dialogues/enter_name.json", default_domain)
    p = tmpdir.join("export.md")
    tracker.export_stories_to_file(p.strpath)
    trackers = extract_trackers_from_file(p.strpath, default_domain,
                                          BinaryFeaturizer())
    assert len(trackers) == 1
    recovered = trackers[0]
    assert len(recovered.events) == 8
    assert recovered.events[6].type_name == "slot"
    assert recovered.events[6].key in {"location", "name"}
    assert recovered.events[6].value in {"central", "holger"}


def test_tracker_state_regression_without_bot_utterance(default_agent):
    sender_id = "test_tracker_state_regression_without_bot_utterance"
    for i in range(0, 2):
        default_agent.handle_message("/greet", sender_id=sender_id)
    tracker = default_agent.tracker_store.get_or_create_tracker(sender_id)

    # Ensures that the tracker has changed between the utterances
    # (and wasn't reset in between them)
    expected = ("action_listen;"
                "greet;utter_greet;action_listen;"
                "greet;action_listen")
    assert ";".join([e.as_story_string() for e in
                     tracker.events if e.as_story_string()]) == expected


def test_tracker_state_regression_with_bot_utterance(default_agent):
    sender_id = "test_tracker_state_regression_with_bot_utterance"
    for i in range(0, 2):
        default_agent.handle_message("/greet", sender_id=sender_id)
    tracker = default_agent.tracker_store.get_or_create_tracker(sender_id)

    expected = ["action_listen", "greet", None, "utter_greet",
                "action_listen", "greet", "action_listen"]
    print([e.as_story_string() for e in tracker.events])
    for e in tracker.events:
        print(e)
    assert [e.as_story_string() for e in tracker.events] == expected


def test_tracker_entity_retrieval(default_domain):
    tracker = DialogueStateTracker("default", default_domain.slots,
                                   default_domain.topics,
                                   default_domain.default_topic)
    # the retrieved tracker should be empty
    assert len(tracker.events) == 0
    assert list(tracker.get_latest_entity_values("entity_name")) == []

    intent = {"name": "greet", "confidence": 1.0}
    tracker.update(UserUttered("/greet", intent, [{
        "start": 1,
        "end": 5,
        "value": "greet",
        "entity": "entity_name",
        "extractor": "manual"
    }]))
    assert list(tracker.get_latest_entity_values("entity_name")) == ["greet"]
    assert list(tracker.get_latest_entity_values("unknown")) == []


def test_restart_event(default_domain):
    tracker = DialogueStateTracker("default", default_domain.slots,
                                   default_domain.topics,
                                   default_domain.default_topic)
    # the retrieved tracker should be empty
    assert len(tracker.events) == 0

    intent = {"name": "greet", "confidence": 1.0}
    tracker.update(ActionExecuted(ACTION_LISTEN_NAME))
    tracker.update(UserUttered("/greet", intent, []))
    tracker.update(ActionExecuted("my_action"))
    tracker.update(ActionExecuted(ACTION_LISTEN_NAME))

    assert len(tracker.events) == 4
    assert tracker.latest_message.text == "/greet"
    assert len(list(tracker.generate_all_prior_states())) == 4

    tracker.update(Restarted())

    assert len(tracker.events) == 5
    assert tracker.follow_up_action is not None
    assert tracker.follow_up_action.name() == ACTION_LISTEN_NAME
    assert tracker.latest_message.text is None
    assert len(list(tracker.generate_all_prior_states())) == 1

    dialogue = tracker.as_dialogue()

    recovered = DialogueStateTracker("default", default_domain.slots,
                                     default_domain.topics,
                                     default_domain.default_topic)
    recovered.recreate_from_dialogue(dialogue)

    assert recovered.current_state() == tracker.current_state()
    assert len(recovered.events) == 5
    assert tracker.follow_up_action is not None
    assert tracker.follow_up_action.name() == ACTION_LISTEN_NAME
    assert recovered.latest_message.text is None
    assert len(list(recovered.generate_all_prior_states())) == 1


def test_revert_action_event(default_domain):
    tracker = DialogueStateTracker("default", default_domain.slots,
                                   default_domain.topics,
                                   default_domain.default_topic)
    # the retrieved tracker should be empty
    assert len(tracker.events) == 0

    intent = {"name": "greet", "confidence": 1.0}
    tracker.update(ActionExecuted(ACTION_LISTEN_NAME))
    tracker.update(UserUttered("/greet", intent, []))
    tracker.update(ActionExecuted("my_action"))
    tracker.update(ActionExecuted(ACTION_LISTEN_NAME))

    # Expecting count of 4:
    #   +3 executed actions
    #   +1 final state
    assert tracker.latest_action_name == ACTION_LISTEN_NAME
    assert len(list(tracker.generate_all_prior_states())) == 4

    tracker.update(ActionReverted())

    # Expecting count of 3:
    #   +3 executed actions
    #   +1 final state
    #   -1 reverted action
    assert tracker.latest_action_name == "my_action"
    assert len(list(tracker.generate_all_prior_states())) == 3

    dialogue = tracker.as_dialogue()

    recovered = DialogueStateTracker("default", default_domain.slots,
                                     default_domain.topics,
                                     default_domain.default_topic)
    recovered.recreate_from_dialogue(dialogue)

    assert recovered.current_state() == tracker.current_state()
    assert tracker.latest_action_name == "my_action"
    assert len(list(tracker.generate_all_prior_states())) == 3


def test_revert_user_utterance_event(default_domain):
    tracker = DialogueStateTracker("default", default_domain.slots,
                                   default_domain.topics,
                                   default_domain.default_topic)
    # the retrieved tracker should be empty
    assert len(tracker.events) == 0

    intent1 = {"name": "greet", "confidence": 1.0}
    tracker.update(ActionExecuted(ACTION_LISTEN_NAME))
    tracker.update(UserUttered("/greet", intent1, []))
    tracker.update(ActionExecuted("my_action_1"))
    tracker.update(ActionExecuted(ACTION_LISTEN_NAME))

    intent2 = {"name": "goodbye", "confidence": 1.0}
    tracker.update(UserUttered("/goodbye", intent2, []))
    tracker.update(ActionExecuted("my_action_2"))
    tracker.update(ActionExecuted(ACTION_LISTEN_NAME))

    # Expecting count of 6:
    #   +5 executed actions
    #   +1 final state
    assert tracker.latest_action_name == ACTION_LISTEN_NAME
    assert len(list(tracker.generate_all_prior_states())) == 6

    tracker.update(UserUtteranceReverted())

    # Expecting count of 3:
    #   +5 executed actions
    #   +1 final state
    #   -2 rewound actions associated with the /goodbye
    #   -1 rewound action from the listen right before /goodbye
    assert tracker.latest_action_name == "my_action_1"
    assert len(list(tracker.generate_all_prior_states())) == 3

    dialogue = tracker.as_dialogue()

    recovered = DialogueStateTracker("default", default_domain.slots,
                                     default_domain.topics,
                                     default_domain.default_topic)
    recovered.recreate_from_dialogue(dialogue)

    assert recovered.current_state() == tracker.current_state()
    assert tracker.latest_action_name == "my_action_1"
    assert len(list(tracker.generate_all_prior_states())) == 3


def test_traveling_back_in_time(default_domain):
    tracker = DialogueStateTracker("default", default_domain.slots,
                                   default_domain.topics,
                                   default_domain.default_topic)
    # the retrieved tracker should be empty
    assert len(tracker.events) == 0

    intent = {"name": "greet", "confidence": 1.0}
    tracker.update(ActionExecuted(ACTION_LISTEN_NAME))
    tracker.update(UserUttered("/greet", intent, []))

    import time
    time.sleep(1)
    time_for_timemachine = time.time()
    time.sleep(1)

    tracker.update(ActionExecuted("my_action"))
    tracker.update(ActionExecuted(ACTION_LISTEN_NAME))

    # Expecting count of 4:
    #   +3 executed actions
    #   +1 final state
    assert tracker.latest_action_name == ACTION_LISTEN_NAME
    assert len(tracker.events) == 4
    assert len(list(tracker.generate_all_prior_states())) == 4

    tracker = tracker.travel_back_in_time(time_for_timemachine)

    # Expecting count of 2:
    #   +1 executed actions
    #   +1 final state
    assert tracker.latest_action_name == ACTION_LISTEN_NAME
    assert len(tracker.events) == 2
    assert len(list(tracker.generate_all_prior_states())) == 2


def test_dump_and_restore_as_json(default_agent, tmpdir):
    trackers = extract_trackers_from_file(
            DEFAULT_STORIES_FILE,
            default_agent.domain,
            default_agent.featurizer,
            default_agent.interpreter,
            default_agent.policy_ensemble.max_history())

    out_path = tmpdir.join("dumped_tracker.json")

    for tracker in trackers:
        dumped = tracker.current_state(should_include_events=True)
        utils.dump_obj_as_json_to_file(out_path.strpath, dumped)

        tracker_json = json.loads(utils.read_file(out_path.strpath))
        sender_id = tracker_json.get("sender_id", UserMessage.DEFAULT_SENDER_ID)
        restored_tracker = DialogueStateTracker.from_dict(
                sender_id, tracker_json.get("events", []), default_agent.domain)

        assert restored_tracker == tracker


def test_read_json_dump(default_agent):
    json_content = utils.read_file("data/test_trackers/tracker_moodbot.json")
    tracker_json = json.loads(json_content)
    sender_id = tracker_json.get("sender_id", UserMessage.DEFAULT_SENDER_ID)
    restored_tracker = DialogueStateTracker.from_dict(
            sender_id, tracker_json.get("events", []), default_agent.domain)

    assert len(restored_tracker.events) == 7
    assert restored_tracker.latest_action_name == "action_listen"
    assert not restored_tracker.is_paused()
    assert restored_tracker.sender_id == "mysender"
    assert restored_tracker.events[-1].timestamp == 1517821726.211042

    restored_state = restored_tracker.current_state(should_include_events=True)
    assert restored_state == tracker_json
