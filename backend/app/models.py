"""Import every module's models so they register on Base.metadata."""

from app.modules.auth.models import *  # noqa: F403
from app.modules.mechanics.models import *  # noqa: F403
from app.modules.reminders.models import *  # noqa: F403
from app.modules.service_logs.models import *  # noqa: F403
from app.modules.vehicles.models import *  # noqa: F403
