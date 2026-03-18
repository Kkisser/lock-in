from aiogram.filters.callback_data import CallbackData


class NavCB(CallbackData, prefix="nav"):
    """Tree navigation in 'Now' mode."""
    parent_id: int


class SelCB(CallbackData, prefix="sel"):
    """Select an action to start in 'Now' mode."""
    node_id: int


class StartCB(CallbackData, prefix="start"):
    """Confirm starting a session."""
    node_id: int


class SesCB(CallbackData, prefix="ses"):
    """Session control: pause / resume / finish / confirm_finish / cancel_finish."""
    action: str
    session_id: int


class ENavCB(CallbackData, prefix="enav"):
    """Editor tree navigation."""
    parent_id: int


class ESelCB(CallbackData, prefix="esel"):
    """Editor: select a node to manage."""
    node_id: int


class EActCB(CallbackData, prefix="eact"):
    """Editor action: create_group / create_action / rename / delete / move."""
    action: str
    node_id: int


class ELocCB(CallbackData, prefix="eloc"):
    """Editor: choose location (parent) for new node creation."""
    parent_id: int
    event_type: str


class CDelCB(CallbackData, prefix="cdel"):
    """Confirm or cancel deletion."""
    action: str  # "yes" or "no"
    node_id: int


class SetCB(CallbackData, prefix="set"):
    """Settings toggle / action."""
    key: str  # "confirm_finish", "confirm_delete", "timezone"


class TzCB(CallbackData, prefix="tz"):
    """Select timezone."""
    tz: str


class EMvNavCB(CallbackData, prefix="emvnav"):
    """Editor move: navigate tree while selecting move destination."""
    parent_id: int
    node_id: int


class EMvSelCB(CallbackData, prefix="emvsel"):
    """Editor move: confirm move to selected parent."""
    target_parent_id: int
    node_id: int
