"""Immutable resolved planning records."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    fixture_id: str
    locale: str
    client: str
    provider: str
    parameters: dict

    @property
    def size(self):
        return 3 if self.fixture_id == "fixture.uk.thread" else 1

    @property
    def key(self):
        return (
            self.fixture_id,
            self.locale,
            self.client,
            self.provider,
            tuple(sorted(self.parameters.items())),
        )
