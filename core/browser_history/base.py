from rapidfuzz import fuzz
from typing import Optional
from abc import ABC, abstractmethod
from core.event import Event  # adjust import as needed

class BrowserHistory(ABC):
    @abstractmethod
    def get_history(self) -> list[dict]:
        """Fetch today's history entries. Each entry is a dict with title, url, visit_time."""
        pass

    def match_event(self, event: Event) -> Optional[str]:
        """Match event title and time with browser history using fuzzy matching."""

        print(event.to_row())
        history = self.get_history()

        best_match = None
        highest_score = 0

        for entry in history:
            score = fuzz.token_set_ratio(entry['title'], event.window_title)
            if score >= 90:
                # Accept match if visit time is within ±5 minutes
                delta = abs((entry['visit_time'] - event.timestamp).total_seconds())
                if delta <= 24 * 60 * 60:  # 5 minutes
                    if score > highest_score:
                        best_match = entry['url']
                        highest_score = score

        if best_match:
            print(f"Matched with score: {highest_score}")
        return best_match
