from aiogram.fsm.state import State, StatesGroup


class YouTubeState(StatesGroup):
    """YouTube specific states."""
    selecting_quality = State()
    downloading_video = State()
    downloading_audio = State()


class TikTokState(StatesGroup):
    """TikTok specific states."""
    selecting_format = State()
