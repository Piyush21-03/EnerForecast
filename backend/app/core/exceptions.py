"""Custom exception hierarchy for the Energy Forecasting API.

All domain-specific errors subclass ForecastBaseError so that a single
except clause can catch any application error while still allowing callers
to handle specific sub-classes precisely.
"""


class ForecastBaseError(Exception):
    """Root for every domain-specific exception raised by this application."""


# ------------------------------------------------------------------ artifacts
class ModelArtifactError(ForecastBaseError):
    """A model artifact file is missing or corrupt."""


class ArtifactNotFoundError(ModelArtifactError):
    """One or more required artifact files do not exist on disk."""


class InvalidArtifactError(ModelArtifactError):
    """An artifact file exists but its content is invalid or unparseable."""


class FeatureMismatchError(ModelArtifactError):
    """The feature columns in the artifact do not match the model or inputs."""


# ------------------------------------------------------------------ runtime
class ModelNotLoadedError(ForecastBaseError):
    """A model method was called before load() completed successfully."""


class ForecastServiceError(ForecastBaseError):
    """Generic error raised by the ForecastService layer."""


class ForecastInputError(ForecastServiceError):
    """The request inputs (timestamp / horizon) are invalid."""


class InvalidTimestampError(ForecastInputError):
    """The supplied timestamp is not a valid, hour-aligned, tz-naive value."""


class InvalidHorizonError(ForecastInputError):
    """The supplied horizon is outside the allowed range."""


class InsufficientHistoryError(ForecastServiceError):
    """Not enough historical data to build the required features."""


class ForecastComputationError(ForecastServiceError):
    """The model produced a result that failed a post-prediction sanity check."""


# ------------------------------------------------------------------ persistence
class PersistenceError(ForecastBaseError):
    """A database operation failed; the original SQLAlchemy exception is chained."""
