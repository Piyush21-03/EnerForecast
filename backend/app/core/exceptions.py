"""Domain exceptions. The API layer (Phase 7) maps these to HTTP responses."""


class ModelArtifactError(Exception):
    """Base class for problems with the exported model artifacts."""


class ArtifactNotFoundError(ModelArtifactError):
    """One or more required artifact files are missing."""


class InvalidArtifactError(ModelArtifactError):
    """An artifact exists but cannot be read or has the wrong shape."""


class ModelNotLoadedError(ModelArtifactError):
    """Prediction was requested before the model was loaded."""


class FeatureMismatchError(ModelArtifactError):
    """Input features do not match feature_columns.json (names or order)."""


class ForecastInputError(Exception):
    """Base class for invalid forecast inputs (maps to HTTP 4xx)."""


class InvalidTimestampError(ForecastInputError):
    """A timestamp is malformed, not hourly-aligned, or otherwise unusable."""


class InsufficientHistoryError(ForecastInputError):
    """Not enough contiguous hourly history to build the requested features."""


class InvalidHorizonError(ForecastInputError):
    """Requested forecast horizon is outside the supported range."""


class ForecastServiceError(Exception):
    """Base class for server-side forecast failures (maps to HTTP 5xx/503)."""


class HistoryUnavailableError(ForecastServiceError):
    """The hourly history data could not be loaded."""


class PersistenceError(ForecastServiceError):
    """Saving to (or reading from) the database failed."""


class ForecastComputationError(ForecastServiceError):
    """The model produced an unusable (e.g. non-finite) prediction."""
