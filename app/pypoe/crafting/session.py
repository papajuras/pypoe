import logging
from pathlib import Path

from .actions import (
    capture_clipboard,
    delete_beast,
    file_logger,
    use_alt,
    use_aug,
    use_exalt,
    use_regal,
    use_scour,
    use_transmute,
)

logger = logging.getLogger(__name__)

from .matching import (
    count_patterns_in_string,
    has_prefix_slot,
    has_suffix_slot,
    matches_target,
)


class Positions:
    def __init__(
        self,
        alt: list[int],
        item: list[int],
        aug: list[int],
        regal: list[int],
        exalt: list[int],
        scour: list[int],
        transmute: list[int],
        delete_beasts: list[int],
    ):
        self.alt = alt
        self.item = item
        self.aug = aug
        self.regal = regal
        self.exalt = exalt
        self.scour = scour
        self.transmute = transmute
        self.delete_beasts = delete_beasts


class Settings:
    def __init__(self, use_regal: bool = False, exalt_after_regal: bool = False):
        self.use_regal = use_regal
        self.exalt_after_regal = exalt_after_regal


class CraftingSession:
    def __init__(
        self,
        prefixes: list[str],
        suffixes: list[str],
        positions: Positions,
        settings: Settings | None = None,
    ):
        self.prefixes = prefixes
        self.suffixes = suffixes
        self.positions = positions
        self.settings = settings or Settings()

        self._should_stop = False
        self._needs_transmute = False
        self.regal_counter = 0
        self.exalt_counter = 0

    def stop(self) -> None:
        self._should_stop = True

    @property
    def should_stop(self) -> bool:
        return self._should_stop

    def delete_beasts_loop(self) -> None:
        logger.info("delete_beasts_loop starting")
        count = 0
        while not self._should_stop:
            try:
                delete_beast(self.positions.delete_beasts)
            except Exception:
                logger.exception("delete_beast failed (iteration %d)", count)
                return
            count += 1

    def run(self) -> str | None:
        _log = file_logger()
        _log.info(
            "session started: prefixes=%s suffixes=%s alt_pos=%s item_pos=%s",
            self.prefixes, self.suffixes, self.positions.alt, self.positions.item,
        )
        for i in range(1000):
            if self._should_stop:
                _log.info("session stopped after %d iterations", i)
                return None
            try:
                if self._needs_transmute:
                    use_transmute(self.positions.transmute, self.positions.item)
                    self._needs_transmute = False
                else:
                    use_alt(self.positions.alt, self.positions.item)

                item_text = capture_clipboard()
                result = self._handle_match(item_text)
                if result is not None:
                    _log.info("session matched at iteration %d", i)
                    return result
            except Exception:
                _log.exception("session crashed at iteration %d", i)
                return None
        return None

    def _handle_match(self, item_text: str) -> str | None:
        aug_used = False

        if matches_target(item_text, self.prefixes, self.suffixes, True):
            if has_suffix_slot(item_text) or has_prefix_slot(item_text):
                use_aug(self.positions.aug, self.positions.item)
                aug_used = True
            if self.settings.use_regal:
                return self._check_regal(item_text)
            return item_text

        elif has_suffix_slot(item_text) and self._any_prefix_match(item_text):
            use_aug(self.positions.aug, self.positions.item)
            aug_used = True
        elif has_prefix_slot(item_text) and self._any_suffix_match(item_text):
            use_aug(self.positions.aug, self.positions.item)
            aug_used = True

        if aug_used:
            item_text = capture_clipboard()
            if matches_target(item_text, self.prefixes, self.suffixes, True):
                if self.settings.use_regal:
                    return self._check_regal(item_text)
                return item_text

        return None

    def _any_prefix_match(self, item_text: str) -> bool:
        return any(p.lower() in item_text.lower() for p in self.prefixes)

    def _any_suffix_match(self, item_text: str) -> bool:
        return any(s.lower() in item_text.lower() for s in self.suffixes)

    def _check_regal(self, item_text: str) -> str | None:
        prefixes_match = count_patterns_in_string(item_text, self.prefixes)
        suffixes_match = count_patterns_in_string(item_text, self.suffixes)
        total = prefixes_match + suffixes_match

        if total < 2:
            return None

        use_regal(self.positions.regal, self.positions.item)
        self.regal_counter += 1

        item_text = capture_clipboard()
        prefixes_match = count_patterns_in_string(item_text, self.prefixes)
        suffixes_match = count_patterns_in_string(item_text, self.suffixes)
        total = prefixes_match + suffixes_match

        if total >= 3:
            return item_text

        if self.settings.exalt_after_regal:
            return self._check_exalt(item_text)

        use_scour(self.positions.scour, self.positions.item)
        self._needs_transmute = True
        return None

    def _check_exalt(self, item_text: str) -> str | None:
        use_exalt(self.positions.exalt, self.positions.item)
        self.exalt_counter += 1

        item_text = capture_clipboard()
        self._save_exalt_clipboard(item_text)

        prefixes_match = count_patterns_in_string(item_text, self.prefixes)
        suffixes_match = count_patterns_in_string(item_text, self.suffixes)
        total = prefixes_match + suffixes_match

        if total >= 3:
            return item_text

        use_scour(self.positions.scour, self.positions.item)
        self._needs_transmute = True
        return None

    @staticmethod
    def _save_exalt_clipboard(content: str) -> None:
        out = Path(__file__).resolve().parent.parent / "tmp" / "exalts"
        out.mkdir(parents=True, exist_ok=True)
        i = 1
        while (out / f"exalt{i}.txt").exists():
            i += 1
        (out / f"exalt{i}.txt").write_text(content)
