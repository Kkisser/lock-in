from aiogram.filters.callback_data import CallbackData


class NavCB(CallbackData, prefix="nav"):
    """Tree navigation in 'Now' mode."""
    parent_id: int


class SelCB(CallbackData, prefix="sel"):
    """Select an action to start in 'Now' mode."""
    event_id: int


class StartCB(CallbackData, prefix="start"):
    """Confirm starting a session."""
    event_id: int


class SesCB(CallbackData, prefix="ses"):
    """Session control: pause / resume / finish / confirm_finish / cancel_finish."""
    action: str
    session_id: int


class ENavCB(CallbackData, prefix="enav"):
    """Editor tree navigation."""
    parent_id: int


class ESelCB(CallbackData, prefix="esel"):
    """Editor: select an event to manage."""
    event_id: int


class EActCB(CallbackData, prefix="eact"):
    """Editor action: create_group / create_action / rename / delete / confirm_delete / cancel_delete."""
    action: str
    event_id: int


class ELocCB(CallbackData, prefix="eloc"):
    """Editor: choose location (parent) for new event creation."""
    parent_id: int
    event_type: str


class CDelCB(CallbackData, prefix="cdel"):
    """Confirm or cancel deletion."""
    action: str  # "yes" or "no"
    event_id: int


class SetCB(CallbackData, prefix="set"):
    """Settings toggle."""
    key: str  # "confirm_finish" or "confirm_delete"
