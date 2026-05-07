import os
import json
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

# --- COMPONENT (Composite Pattern) ---
class StudyComponent(ABC):
    """Abstract base for both individual cards and decks."""
    @abstractmethod
    def review(self):
        pass

    @abstractmethod
    def get_status(self):
        pass

# --- LEAF (Active Recall + Proxy Pattern) ---
class Flashcard(StudyComponent):
    """
    The 'RealSubject' in the Proxy pattern. 
    It holds the actual answer/content.
    """
    def __init__(self, question, answer):
        self.question = question
        self._answer = answer  # The hidden content

    def review(self):
        print(f"\n[ACTIVE RECALL] Question: {self.question}")
        input("Press Enter to reveal answer...")
        print(f"Answer: {self._answer}")
        return self._score_review()

    def _score_review(self):
        try:
            score = int(input("Rate your recall (0-5): "))
            return score
        except ValueError:
            return 0

    def get_status(self):
        return f"Card: {self.question[:30]}..."

# --- PROXY (Proxy Pattern) ---
class CardProxy(StudyComponent):
    """
    Controls access to the Flashcard. 
    Can implement 'Lazy Loading' as seen in your notes.
    """
    def __init__(self, question, answer):
        self.question = question
        self.answer = answer
        self._real_card = None

    def review(self):
        # Lazy Initialization: Only create the 'Real' card when needed
        if self._real_card is None:
            self._real_card = Flashcard(self.question, self.answer)
        return self._real_card.review()

    def get_status(self):
        return f"Proxy for: {self.question}"

# --- COMPOSITE (Composite Pattern) ---
class StudyDeck(StudyComponent):
    """
    A collection of StudyComponents (Cards or other Decks).
    Allows treating a single card and a whole deck uniformly.
    """
    def __init__(self, name):
        self.name = name
        self.children = []

    def add(self, component: StudyComponent):
        self.children.append(component)

    def review(self):
        print(f"--- Starting Deck: {self.name} ---")
        scores = []
        for child in self.children:
            score = child.review()
            scores.append(score)
        print(f"--- Finished Deck: {self.name} ---")
        return scores

    def get_status(self):
        return f"Deck '{self.name}' containing {len(self.children)} items."

# --- LEITNER SYSTEM & SPACED REPETITION ---
class LeitnerSystem:
    """Implements the logic of moving items between review intervals."""
    def __init__(self):
        self.boxes = {1: [], 2: [], 3: [], 4: [], 5: []}

    def add_to_system(self, component: StudyComponent):
        self.boxes[1].append(component)

    def process_review(self, component, box_num, score):
        # Leitner Logic: Correct (score >= 4) moves up, Incorrect moves back to Box 1
        if score >= 4 and box_num < 5:
            self.boxes[box_num + 1].append(component)
        else:
            self.boxes[1].append(component)

# --- EXAMPLE IMPLEMENTATION ---
if __name__ == "__main__":
    # Create individual items (Leaves/Proxies)
    python_q = CardProxy("What is the Proxy Pattern?", "A surrogate to control access[cite: 1]")
    sql_q = CardProxy("What is a JOIN?", "Combining rows based on a related column.")
    
    # Create a hierarchy (Composite)[cite: 1]
    dev_deck = StudyDeck("Dev Tools")
    dev_deck.add(python_q)
    dev_deck.add(sql_q)
    
    # Unified execution: treating the deck like a single item[cite: 1]
    dev_deck.review()