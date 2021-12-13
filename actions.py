# -*- coding: utf-8 -*-
from typing import Text, Dict, Any, List, Union

from rasa_sdk.events import SlotSet
from rasa_sdk import Action, Tracker

from graph_database import GraphDatabase


# def resolve_mention(tracker: Tracker) -> Text:
#     """
#     Resolves a mention of an entity, such as first, to the actual entity.
#     If multiple entities are listed during the conversation, the entities
#     are stored in the slot 'listed_items' as a list. We resolve the mention,
#     such as first, to the list index and retrieve the actual entity.
#     :param tracker: tracker
#     :return: name of the actually entity
#     """
#     graph_database = GraphDatabase()

#     mention = tracker.get_slot("mention")
#     listed_items = tracker.get_slot("listed_items")

#     if mention is not None and listed_items is not None:
#         idx = int(graph_database.map("mention-mapping", mention))

#         if type(idx) is int and idx < len(listed_items):
#             return listed_items[idx]


def get_entity_type(tracker: Tracker) -> Text:
    """
    Get the entity type mentioned by the user. As the user may speak of an
    entity type in plural, we need to map the mentioned entity type to the
    type used in the knowledge base.
    :param tracker: tracker
    :return: entity type (same type as used in the knowledge base)
    """
    graph_database = GraphDatabase()
    entity_type = tracker.get_slot("entity_type")
    return graph_database.map("entity-type-mapping", entity_type)


def get_attribute(tracker: Tracker) -> Text:
    """
    Get the attribute mentioned by the user. As the user may use a synonym for
    an attribute, we need to map the mentioned attribute to the
    attribute name used in the knowledge base.
    :param tracker: tracker
    :return: attribute (same type as used in the knowledge base)
    """
    graph_database = GraphDatabase()
    attribute = tracker.get_slot("attribute")
    return graph_database.map("attribute-mapping", attribute)


# def get_entity_name(tracker: Tracker, entity_type: Text):
#     """
#     Get the name of the entity the user referred to. Either the NER detected the
#     entity and stored its name in the corresponding slot or the user referred to
#     the entity by an ordinal number, such as first or last, or the user refers to
#     an entity by its attributes.
#     :param tracker: Tracker
#     :param entity_type: the entity type
#     :return: the name of the actual entity (value of key attribute in the knowledge base)
#     """

#     # user referred to an entity by an ordinal number
#     mention = tracker.get_slot("mention")
#     if mention is not None:
#         return resolve_mention(tracker)

#     # user named the entity
#     entity_name = tracker.get_slot(entity_type)
#     if entity_name:
#         return entity_name

#     # user referred to an entity by its attributes
#     listed_items = tracker.get_slot("listed_items")
#     attributes = get_attributes_of_entity(entity_type, tracker)

#     if listed_items and attributes:
#         # filter the listed_items by the set attributes
#         graph_database = GraphDatabase()
#         for entity in listed_items:
#             key_attr = schema[entity_type]["key"]
#             result = graph_database.validate_entity(
#                 entity_type, entity, key_attr, attributes
#             )
#             if result is not None:
#                 return to_str(result, key_attr)

#     return None


# def get_attributes_of_entity(entity_type, tracker):
#     # check what attributes the NER found for entity type
#     attributes = []
#     if entity_type in schema:
#         for attr in schema[entity_type]["attributes"]:
#             attr_val = tracker.get_slot(attr.replace("-", "_"))
#             if attr_val is not None:
#                 attributes.append({"key": attr, "value": attr_val})
#     return attributes


# def reset_attribute_slots(slots, entity_type, tracker):
#     # check what attributes the NER found for entity type
#     if entity_type in schema:
#         for attr in schema[entity_type]["attributes"]:
#             attr = attr.replace("-", "_")
#             attr_val = tracker.get_slot(attr)
#             if attr_val is not None:
#                 slots.append(SlotSet(attr, None))
#     return slots


# def to_str(entity: Dict[Text, Any], entity_keys: Union[Text, List[Text]]) -> Text:
#     """
#     Converts an entity to a string by concatenating the values of the provided
#     entity keys.
#     :param entity: the entity with all its attributes
#     :param entity_keys: the name of the key attributes
#     :return: a string that represents the entity
#     """
#     if isinstance(entity_keys, str):
#         entity_keys = [entity_keys]

#     v_list = []
#     for key in entity_keys:
#         _e = entity
#         for k in key.split("."):
#             _e = _e[k]

#         if "balance" in key or "amount" in key:
#             v_list.append(f"{str(_e)} €")
#         elif "date" in key:
#             v_list.append(_e.strftime("%d.%m.%Y (%H:%M:%S)"))
#         else:
#             v_list.append(str(_e))
#     return ", ".join(v_list)


class ActionQueryAttribute(Action):
    """Action for querying a specific attribute of an entity."""

    def name(self):
        return "action_query_attribute"

    def run(self, dispatcher, tracker, domain):
        graph_database = GraphDatabase()

        # get entity type of entity
        entity_type = get_entity_type(tracker)

        if entity_type is None:
            dispatcher.utter_template("utter_rephrase", tracker)
            return []

        # get name of entity and attribute of interest
        name = get_entity_type(tracker)
        attribute = get_attribute(tracker)

        # if name is None or attribute is None:
        #     dispatcher.utter_template("utter_rephrase", tracker)
        #     slots = [SlotSet("mention", None)]
        #     reset_attribute_slots(slots, entity_type, tracker)
        #     return slots

        # query knowledge base
        value = graph_database.get_attribute_of(name, attribute)

        # utter response
        if value is not None and len(value) == 1:
            dispatcher.utter_message(
                f"'{value[0]}'."
            )
        else:
            dispatcher.utter_message(
                f"Did not found a valid value for attribute {attribute} for entity '{name}'."
            )

        slots = [SlotSet("mention", None), SlotSet(entity_type, name)]
        # reset_attribute_slots(slots, entity_type, tracker)
        return slots
