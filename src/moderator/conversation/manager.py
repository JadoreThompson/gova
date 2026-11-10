import uuid

from moderator.conversation.discord import DiscordConversation


class ConversationManager:
    def __init__(self):
        self._conversations: dict[uuid.UUID, DiscordConversation] = {}

    def add_conversation(self, conversation: DiscordConversation):
        self._conversations[conversation.id] = conversation

    def get_conversation(self, conversation_id: uuid.UUID) -> DiscordConversation:
        if conversation_id not in self._conversations:
            raise ValueError(f"Conversation with id {conversation_id} not found")
        return self._conversations[conversation_id]

    def remove_conversation(self, conversation_id: uuid.UUID):
        self.get_conversation(conversation_id)
        del self._conversations[conversation_id]
